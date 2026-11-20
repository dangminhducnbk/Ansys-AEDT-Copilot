"""Skill PI-DC: power tree (guides/pidc_power_tree.md).

SIwave Export DC Power Tree bằng script (ScrExportDcPowerTree), làm trực tiếp trên thư mục người dùng (không save).
Một lần chạy SIwave: (1) xuất cây thử với file spec chỉ có tiêu đề -> SIwave ghi <png>.txt (biến môi trường
GENERATE_POWERTREE_TEXT_FILE) chứa tên mọi node; (2) ghi file spec cho mọi node theo thông số pidc.pt_*;
(3) xuất cây thật -> images/POWER_TREE.png + <png>.txt + <png>.pwrLoss.txt (GENERATE_POWERLOSS_TEXT_FILE).
Pass/Fail mỗi node cuối (tải) tính lại theo đúng quy tắc SIwave: |V - Vvrm| <= % x Vvrm (hoặc V >= Value) và I <= ngưỡng.
"""
from __future__ import annotations

import re
import shutil
import time

from .. import common, export

NAME = "power_tree"
ORDER = 40
NEEDS_EXPORT = False                    # tự chạy SIwave, không cần ảnh pidc_export
TITLE = "Power tree"
HEADER = "Include,Component Name,Current Threshold (A),Voltage Threshold,Voltage Percentage (%),Voltage Value (V)"

SCRIPT = r'''# IronPython 2.7 - PI-DC power tree (Ansys AEDT Copilot). ASCII only, no os module. Never saves the project.
import clr
clr.AddReference('System.Windows.Forms')
from System.IO import File, FileInfo
from System.Threading import Thread
from System.Windows.Forms import Application
from System import DateTime
SIM = %(sim)r
D = %(dir)r
ROW = %(row)r
AGG = %(agg)r
LOSS = %(loss)r
HEADER = %(header)r
EXTRA = %(extra)r
log = open(D + 'power_tree_log.txt', 'w')
def w(m):
    log.write(DateTime.Now.ToString('HH:mm:ss') + ' ' + str(m) + chr(10)); log.flush()
def wait(p, sec=300):
    t0 = DateTime.Now; last = -2; st = 0
    while (DateTime.Now - t0).TotalSeconds < sec:
        Application.DoEvents(); Thread.Sleep(250)
        s = FileInfo(p).Length if File.Exists(p) else -1
        if s > 0 and s == last:
            st += 1
            if st >= 8:
                return s
        else:
            st = 0
        last = s
    return FileInfo(p).Length if File.Exists(p) else -1
try:
    oDoc = oApp.GetActiveProject()
    w('agg rc=%%s' %% oDoc.ScrActivateDcPowerTreePinAggregation(AGG))
    w('loss rc=%%s' %% oDoc.ScrShowDcPowerTreePowerLossOfNets(LOSS))
    f = open(D + 'specs_probe.csv', 'w'); f.write(HEADER + chr(10)); f.close()
    w('probe rc=%%s' %% oDoc.ScrExportDcPowerTree(SIM, D + 'specs_probe.csv', D + 'probe_tree.png'))
    w('probe png %%s' %% wait(D + 'probe_tree.png'))
    names = []
    for ln in open(D + 'probe_tree.txt').read().splitlines():
        if ln.startswith('NODE "'):
            n = ln.split('"')[1]
            if n not in names:
                names.append(n)
    for n in EXTRA:                       # source names before pin aggregation (aggregated nodes take their spec)
        if n not in names:
            names.append(n)
    f = open(D + 'specs.csv', 'w')        # text mode: chr(10) -> CRLF
    f.write(HEADER + chr(10))
    for n in names:
        f.write(ROW %% n + chr(10))
    f.close()
    w('nodes %%d' %% len(names))
    w('tree rc=%%s' %% oDoc.ScrExportDcPowerTree(SIM, D + 'specs.csv', D + 'power_tree.png'))
    w('tree png %%s' %% wait(D + 'power_tree.png'))
    w('DONE')
except Exception:
    import traceback
    w('EXCEPTION ' + traceback.format_exc())
finally:
    log.close()
'''


def _num(s):
    m = re.match(r"([-+0-9.eE]+)\s*(u|m)?([VAW])", s)
    if not m:
        return None
    return float(m.group(1)) * {"u": 1e-6, "m": 1e-3, None: 1.0}[m.group(2)]


def parse_tree(txt: str) -> dict:
    """<png>.txt -> nodes/edges. Node khai báo theo thứ tự DFS ngay sau cạnh của cha -> node cùng tên (U13) khớp với
    cạnh CHƯA KHỚP GẦN NHẤT (sau cùng) có cùng tên đích."""
    nodes, edges, pending = [], [], []
    cur = None
    for ln in txt.splitlines():
        q = re.findall(r'"([^"]*)"', ln)
        if ln.startswith("NODE "):
            rest = ln.split('"')[2].split()
            node = {"id": len(nodes), "name": q[0], "V": _num(rest[0]) if rest else None,
                    "I": _num(rest[1]) if len(rest) > 1 else None, "parent_edge": None, "children": []}
            for e in reversed(pending):
                if e["to"] == q[0] and e["to_id"] is None:
                    e["to_id"] = node["id"]
                    node["parent_edge"] = e["id"]
                    break
            nodes.append(node)
            cur = node
        elif ln.startswith("NET ") and cur is not None:
            vals = [_num(t) for t in ln.split('"')[-1].split()]
            e = {"id": len(edges), "net": q[0], "from": q[1], "from_id": cur["id"], "to": q[2], "to_id": None,
                 "dV_worst": vals[0] if vals else None, "dV_avg": vals[1] if len(vals) > 1 else None}
            edges.append(e)
            pending.append(e)
            cur["children"].append(e["id"])
    return {"nodes": nodes, "edges": edges}


def verdicts(tree, P):
    """Pass/Fail các node cuối (tải) như SIwave: nguồn gốc = node đầu (VRM) Vout."""
    nodes, edges = tree["nodes"], tree["edges"]
    root = nodes[0] if nodes else None
    vref = root["V"] if root else None
    pct, vtype = float(P["pt_voltage"]), str(P["pt_voltage_type"]).lower()
    ithr = float(P["pt_current_A"])
    rows = []
    for n in nodes:
        if n["children"] or n["parent_edge"] is None:
            continue
        e = edges[n["parent_edge"]]
        # chuỗi đường đi VRM -> tải
        path, k = [], n
        while k["parent_edge"] is not None:
            pe = edges[k["parent_edge"]]
            path.append(pe["net"])
            k = nodes[pe["from_id"]]
        if vtype.startswith("perc"):
            vmin, vmax = vref * (1 - pct / 100), vref * (1 + pct / 100)
            spec = f"{vref:.3f} V (+/-{pct:g}%)"
        else:
            vmin, vmax = pct, float("inf")
            spec = f">= {pct:g} V"
        fv = n["V"] is not None and not (vmin <= n["V"] <= vmax)
        fi = n["I"] is not None and n["I"] > ithr
        rows.append({"load": n["name"], "net": e["net"], "from": e["from"], "path": " <- ".join(path), "V": n["V"],
                     "I": n["I"], "drop_mV": round((vref - n["V"]) * 1000, 3) if vref and n["V"] else None,
                     "drop_pct": round((vref - n["V"]) / vref * 100, 2) if vref and n["V"] else None,
                     "spec": spec, "result": "Fail_V+I" if fv and fi else "Fail_V" if fv else "Fail_I" if fi else "Pass"})
    return root, rows


def run(ctx, log=print, voltage=None, current=None) -> dict:
    from ...core import config
    t0 = time.time()
    P = dict(ctx.P)
    if voltage is not None:
        P["pt_voltage"] = voltage
    if current is not None:
        P["pt_current_A"] = current
    d = ctx.raw / "power_tree"
    d.mkdir(parents=True, exist_ok=True)
    for f in ("power_tree.png", "power_tree.txt", "power_tree.pwrLoss.txt", "power_tree_log.txt"):
        if (d / f).exists():
            (d / f).unlink()
    vt = str(P["pt_voltage_type"])
    perc = vt.lower().startswith("perc")
    row = f"{P['pt_include']},%s,{P['pt_current_A']:g},{'Percentage' if perc else 'Value'}," + \
          (f"{P['pt_voltage']:g}," if perc else f",{P['pt_voltage']:g}")
    fw = str(d).replace("\\", "/") + "/"
    script = d / "power_tree.py"
    t = ctx.siw.read_text(encoding="latin-1")
    extra = sorted(set(re.findall(r'^\s*(?:CSRC|VSRC)\s+"([^"]+)"', t, re.M)))     # nguồn dòng/áp (tải, VRM)
    script.write_text(SCRIPT % {"sim": ctx.sim, "dir": fw, "row": row, "agg": bool(P["pt_aggregate_pins"]),
                                "loss": bool(P["pt_output_power_loss"]), "header": HEADER, "extra": extra},
                      encoding="ascii")
    exe = common.siwave_exe(config.machine().get("aedt_version"))
    log("SIwave power tree ...")
    export._run(exe, ctx, script, "power_tree", str(P["launch"]).lower(), 900,
                {"GENERATE_POWERTREE_TEXT_FILE": "1", "GENERATE_POWERLOSS_TEXT_FILE": "1"})
    png, txt = d / "power_tree.png", d / "power_tree.txt"
    if not png.exists() or not txt.exists():
        res = {"skill": NAME, "title": TITLE, "verdict": "PENDING", "counts": {"PENDING": 1},
               "reason": f"power tree not exported - see {d / 'power_tree_log.txt'}", "seconds": round(time.time() - t0)}
        ctx.save_result(NAME, res)
        return res
    ctx.images.mkdir(parents=True, exist_ok=True)
    shutil.copy2(png, ctx.images / "POWER_TREE.png")
    tree = parse_tree(txt.read_text(encoding="latin-1"))
    root, rows = verdicts(tree, P)
    loss = []
    lp = d / "power_tree.pwrLoss.txt"
    if lp.exists():
        for ln in lp.read_text(encoding="latin-1").splitlines():
            m = re.match(r'NET "([^"]+)"\s+([-+0-9.eE]+)mW', ln)
            if m:
                loss.append({"net": m.group(1), "loss_mW": float(m.group(2))})
    nf = sum(r["result"] != "Pass" for r in rows)
    res = {"skill": NAME, "title": TITLE, "verdict": "FAIL" if nf else "PASS",
           "counts": {"FAIL": nf, "PASS": len(rows) - nf, "loads": len(rows)}, "image": "POWER_TREE.png",
           "settings": {k: P[k] for k in P if k.startswith("pt_")},
           "vrm": root and {"name": root["name"], "V": root["V"], "I": root["I"]}, "loads": rows,
           "power_loss": loss, "edges": tree["edges"], "seconds": round(time.time() - t0)}
    ctx.save_result(NAME, res)
    return res
