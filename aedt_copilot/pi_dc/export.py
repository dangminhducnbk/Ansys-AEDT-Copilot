"""Xuất ảnh DC report từ SIwave, làm TRỰC TIẾP trên thư mục người dùng (không copy, không save project).

Output: <dir>/Ansys AEDT Copilot/raw/ (reports/<job>/report_files/*.png, filters/, export_*.py/log, manifest.json,
element_data/Vias.txt). SIwave tự ghi dcReport.cfg trong .siwaveresults (không tránh được).
- ScrExportDcSimReport chạy BẤT ĐỒNG BỘ: script chờ report.htm ghi xong rồi mới sang job sau.
- Ảnh nét: biến môi trường EXPORT_REPORT_IMAGE_WIDTH/HEIGHT (đọc bởi SIwaveRptGen.exe, không có trong tài liệu).
- Ảnh cần GPU/desktop tương tác: mặc định chạy qua explorer.exe.
- Filter: <current>1</current> (CUR_<layer>), ALL_POWER thêm <via-current>1</via-current> (VIACUR_<layer>, chỉ via nguồn).
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from . import common

FILTER = ('<?xml version="1.0" encoding="UTF-8" standalone="no" ?><dc_plot_filters><nets>{nets}</nets>'
          '<layers>{layers}</layers></dc_plot_filters>')
VIA_LAYER = "[--All Bondwires/Vias--]"

SCRIPT = r'''# IronPython 2.7 - PI-DC report export (Ansys AEDT Copilot). ASCII only, no os module. Never saves the project.
import clr
clr.AddReference('System.Windows.Forms')
from System.IO import File, FileInfo
from System.Threading import Thread
from System.Windows.Forms import Application
from System import DateTime, Environment
SIM = %(sim)r
OUT = %(out)r
LOG = %(log)r
VIAS = %(vias)r
JOBS = %(jobs)r
TIMEOUT_S = %(timeout)d
log = open(LOG, 'w')
def w(m):
    log.write(DateTime.Now.ToString('HH:mm:ss') + ' ' + str(m) + chr(10)); log.flush()
def size(p):
    if not File.Exists(p):
        return -1
    return FileInfo(p).Length
def wait_done(p):
    t0 = DateTime.Now
    last = -2
    stable = 0
    while (DateTime.Now - t0).TotalSeconds < TIMEOUT_S:
        Application.DoEvents()
        Thread.Sleep(250)
        s = size(p)
        if s > 0 and s == last:
            stable += 1
            if stable >= 8:
                return s, (DateTime.Now - t0).TotalSeconds
        else:
            stable = 0
        last = s
    return size(p), -1
try:
    oDoc = oApp.GetActiveProject()
    w('project %%s' %% oDoc.GetFilePath())
    w('image env %%s x %%s' %% (Environment.GetEnvironmentVariable('EXPORT_REPORT_IMAGE_WIDTH'),
                              Environment.GetEnvironmentVariable('EXPORT_REPORT_IMAGE_HEIGHT')))
    w('units rc=%%s' %% oDoc.ScrExportDcSimReportUnits('A/mm^2', 'mV', 'W/mm^3'))
    w('colorbar rc=%%s' %% oDoc.ScrExportDcSimReportColorBarProperties(14, 3, False, False))
    w('scaling cd rc=%%s' %% oDoc.ScrExportDcSimReportScaling('All', 'Current Density', -1, -1, False))
    w('scaling via rc=%%s' %% oDoc.ScrExportDcSimReportScaling('All', 'Via Current', -1, -1, False))
    w('scaling vlt rc=%%s' %% oDoc.ScrExportDcSimReportScaling('All', 'Voltage', -1, -1, False))
    for name, flt in JOBS:
        r1 = oDoc.ScrExportDcSimReportOptions(False, flt) if flt else '-'
        htm = OUT + '/' + name + '/report.htm'
        r2 = oDoc.ScrExportDcSimReport(SIM, 'white', htm)
        s, sec = wait_done(htm)
        w('JOB %%s options_rc=%%s export_rc=%%s htm_bytes=%%s wait_s=%%s' %% (name, r1, r2, s, sec))
    if VIAS:
        rc = oDoc.ScrExportElementData(SIM, VIAS, 'Vias')
        w('VIAS rc=%%s bytes=%%s' %% (rc, wait_done(VIAS)[0]))
    w('DONE')
except Exception:
    import traceback
    w('EXCEPTION ' + traceback.format_exc())
finally:
    log.close()
'''


def _fw(p) -> str:
    return str(p).replace("\\", "/")


def _jobs(ctx, voltage_only=False) -> list[tuple[str, str | None]]:
    """Job export. Bình thường: ALL_NETS (không filter, ĐẦU TIÊN vì filter giữ nguyên trong phiên) + ALL_POWER
    (current + voltage + via-current) + mỗi net nguồn (current + voltage). voltage_only: chỉ ảnh VLT (bổ sung)."""
    fdir = ctx.raw / ("filters_vlt" if voltage_only else "filters")
    fdir.mkdir(parents=True, exist_ok=True)

    def one(name, nets, via):
        # voltage chỉ cần cho ALL_POWER (ảnh VLT_ALL_POWER của skill voltage_distribution)
        lf = ("" if voltage_only else "<current>1</current>") + ("<voltage>1</voltage>" if via else "") + \
             ("<via-current>1</via-current>" if via and not voltage_only else "")
        lays = "".join(f"<layer><layer_name>{m}</layer_name><layer_filters>{lf}</layer_filters></layer>"
                       for m in ctx.metals + ([VIA_LAYER] if via and not voltage_only else []))
        n = "".join(f"<net><net_name>{x}</net_name><visible>1</visible></net>" for x in nets)
        p = fdir / f"{name}.xml"
        p.write_text(FILTER.format(nets=n, layers=lays), encoding="utf-8")
        return _fw(p)

    jobs = [] if voltage_only else [("ALL_NETS", None)]
    jobs += [("ALL_POWER", one("ALL_POWER", ctx.power, True))]
    if not voltage_only:
        jobs += [(common.safe(n), one(common.safe(n), [n], False)) for n in ctx.power]
    return jobs


def _htm_ok(rep_dir, job) -> bool:
    p = rep_dir / job / "report.htm"
    return p.exists() and p.stat().st_size > 0


def _run(exe, ctx, script: Path, tag: str, method: str, timeout: float, extra_env: dict | None = None):
    P = ctx.P
    env = dict(os.environ, EXPORT_REPORT_IMAGE_WIDTH=str(int(P["image_width"])),
               EXPORT_REPORT_IMAGE_HEIGHT=str(int(P["image_height"])), **(extra_env or {}))
    if method == "direct":
        subprocess.run([exe, str(ctx.siw), "-RunScriptAndExit", str(script)], env=env, timeout=timeout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    marker = ctx.raw / f"finished_{tag}.txt"
    if marker.exists():
        marker.unlink()
    bat = ctx.raw / f"run_{tag}.bat"
    bat.write_text("@echo off\r\nrem PI-DC export (Ansys AEDT Copilot). Never saves the project.\r\n"
                   f"set EXPORT_REPORT_IMAGE_WIDTH={int(P['image_width'])}\r\n"
                   f"set EXPORT_REPORT_IMAGE_HEIGHT={int(P['image_height'])}\r\n"
                   + "".join(f"set {k}={v}\r\n" for k, v in (extra_env or {}).items()) +
                   f'"{exe}" "{ctx.siw}" -RunScriptAndExit "{script}"\r\n'
                   f'echo exit=%ERRORLEVEL% > "{marker}"\r\n', encoding="mbcs")
    subprocess.Popen(["explorer.exe", str(bat)])                       # explorer = desktop tương tác (có GPU)
    t0 = time.time()
    while not marker.exists():
        if time.time() - t0 > timeout:
            raise RuntimeError(f"SIwave quá {timeout:.0f} s chưa xong (xem {ctx.raw})")
        time.sleep(3)


SIWAVE_MAX_WIDTH = 10000


def size_warnings(P) -> list:
    """016: SIwave giới hạn chiều rộng ảnh 10000 px -> cảnh báo khi template đặt lớn hơn."""
    w = int(P["image_width"])
    return [f"image_width {w} > {SIWAVE_MAX_WIDTH}: SIwave caps the width at {SIWAVE_MAX_WIDTH}"] if w > SIWAVE_MAX_WIDTH else []


def export(folder: str, sim: str = "", siw: str | None = None, log=print, voltage_only: bool = False) -> dict:
    """voltage_only: chỉ xuất bổ sung ảnh VLT (ALL_POWER + mỗi net) vào raw/reports_vlt (khi lần export trước chưa có voltage)."""
    from ..core import config
    t_start = time.time()
    ctx = common.Ctx(folder, siw, sim)
    warns = size_warnings(ctx.P)
    for w in warns:
        log("WARNING", w)
    ctx.mkdirs()
    if not (ctx.base.parent / (ctx.base.name + ".vcd")).exists():
        raise RuntimeError(f"Thiếu {ctx.base.name}.vcd - DC sim chưa giải xong?")
    rep = ctx.reports_vlt if voltage_only else ctx.reports
    longest = len(str(rep / ("X" * 40) / "report_files" / ("X" * 40 + ".png")))
    if longest > 255:
        raise RuntimeError(f"Đường dẫn output quá dài (~{longest} ký tự, SIwave lỗi 0507). Dùng thư mục ngắn hơn.")
    jobs = _jobs(ctx, voltage_only)
    for j, _ in jobs:
        (rep / j).mkdir(parents=True, exist_ok=True)
    (ctx.raw / "element_data").mkdir(exist_ok=True)
    exe = common.siwave_exe(config.machine().get("aedt_version"))
    timeout = float(ctx.P["job_timeout_s"])
    method = str(ctx.P["launch"]).lower()
    attempts = []
    pre = "vlt_" if voltage_only else ""

    def attempt(js, tag, vias):
        script = ctx.raw / f"export_{pre}{tag}.py"
        script.write_text(SCRIPT % {"sim": ctx.sim, "out": _fw(rep), "log": _fw(ctx.raw / f"export_{pre}{tag}_log.txt"),
                                    "vias": _fw(ctx.raw / "element_data" / "Vias.txt") if vias else "",
                                    "jobs": js, "timeout": int(timeout)}, encoding="ascii")
        log(f"SIwave ({method}): {len(js)} jobs")
        t0 = time.time()
        _run(exe, ctx, script, pre + tag, method, timeout * (len(js) + 2))
        bad = [j for j in js if not _htm_ok(rep, j[0])]
        attempts.append({"tag": pre + tag, "jobs": len(js), "failed": [j[0] for j in bad], "s": round(time.time() - t0)})
        return bad

    for j, _ in jobs:                                                    # report cũ -> xoá để kiểm tra đúng
        p = rep / j / "report.htm"
        if p.exists():
            p.unlink()
    bad = attempt(jobs, "1", not voltage_only)
    if bad:
        bad = attempt(bad, "retry", False)                               # chạy lại 1 lần (ALL_NETS vẫn đầu nếu có)
    if voltage_only:
        mp = ctx.raw / "manifest.json"
        man = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
        man["voltage_export"] = {"jobs": [j[0] for j in jobs], "missing_jobs": [j[0] for j in bad], "attempts": attempts,
                                 "warnings": warns,
                                 "seconds": round(time.time() - t_start), "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        mp.write_text(json.dumps(man, indent=1), encoding="utf-8")
        return man["voltage_export"]
    from PIL import Image
    sz = None
    p = ctx.cur_png("ALL_NETS", "CUR", ctx.metals[0])
    if p:
        with Image.open(p) as im:
            sz = im.size
    man = {"siw": str(ctx.siw), "sim_name": ctx.sim, "run_dir": str(ctx.run_dir), "power_nets": ctx.power,
           "metal_layers": ctx.metals, "jobs": [j[0] for j in jobs], "missing_jobs": [j[0] for j in bad],
           "attempts": attempts, "image_size": sz, "requested_size": [ctx.P["image_width"], ctx.P["image_height"]],
           "warnings": warns,
           "seconds": round(time.time() - t_start), "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    if "ALL_NETS" in man["missing_jobs"] or "ALL_POWER" in man["missing_jobs"]:
        man["error"] = "ALL_NETS/ALL_POWER không xuất được (GPU/desktop?). Xem raw/export_*_log.txt"
    (ctx.raw / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    return man
