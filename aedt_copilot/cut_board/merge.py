"""Gộp các channel đã cắt (mỗi channel 1 project riêng) vào project ban đầu.

Quy tắc (setup-note §12):
- Sao lưu project gốc (.aedt + .aedb) trước khi sửa: <thư mục kết quả>/_backup/<thời gian>/
- Mỗi channel -> 1 design HFSS 3D Layout mới trong project gốc, tên = tên channel; trùng tên -> _v2, _v3...
- Không ghi đè, không xoá design nào. Design gốc (main) giữ nguyên.
- Làm tuần tự. Sau mỗi channel so port / setup / sweep với project channel.
Không dùng Design.copy_design_from của PyAEDT: khi trùng tên nó kích hoạt nhầm design cũ.
"""
import datetime as dt
import json
import os
import shutil
import traceback

from ..core.unique import claim_dir
from . import config


def _short(name):
    return name.split(";", 1)[-1]


def _designs(oproj):
    return [_short(d.GetName()) for d in oproj.GetDesigns()]


def _unique(name, existing):
    if name not in existing:
        return name
    i = 2
    while f"{name}_v{i}" in existing:
        i += 1
    return f"{name}_v{i}"


def _info(h):
    sweeps = []
    for s in h.setups:
        try:
            sweeps += [f"{s.name}:{w.name}" for w in s.sweeps]
        except Exception:
            pass
    return {"ports": sorted(h.port_list), "setups": sorted(h.setup_names), "sweeps": sorted(sweeps)}


def _backup(aedt, out_dir, log):
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = claim_dir(os.path.join(out_dir, "_backup", ts))         # 024: 2 merge cùng giây không chung backup
    shutil.copy2(aedt, bdir)
    aedb = os.path.splitext(aedt)[0] + ".aedb"
    if os.path.isdir(aedb):
        shutil.copytree(aedb, os.path.join(bdir, os.path.basename(aedb)))
    log(f"[backup] {bdir}")
    return bdir


SKIP_IN_AEDB = {"edb.def.tmp", "edb.def+", "edb.def.bak", "stride"}


def _copy_aedb(src, dst):
    """042: copy a board .aedb (edb.def and the other files AEDT needs), never lock / temp / backup files."""
    os.makedirs(dst, exist_ok=True)
    n = 0
    for name in os.listdir(src):
        p = os.path.join(src, name)
        if name in SKIP_IN_AEDB or name.lower().endswith(".lock"):
            continue
        if os.path.isdir(p):
            shutil.copytree(p, os.path.join(dst, name), ignore=shutil.ignore_patterns("*.lock"))
            n += sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)
        else:
            shutil.copy2(p, os.path.join(dst, name))
            n += os.path.getsize(p)
    if not os.path.isfile(os.path.join(dst, "edb.def")):
        raise RuntimeError(f"board {src}: no edb.def to copy")
    return n


def board_project_files(board, workspace=None):
    """042: (aedt | None, aedb) of the board the user gave (board = .aedb or .aedt; workspace = .aedt beside it)."""
    b = os.path.abspath(board.rstrip("/\\"))
    if b.lower().endswith(".aedt"):
        return b, b[:-5] + ".aedb"
    aedt = b[:-5] + ".aedt" if b.lower().endswith(".aedb") else None
    if workspace and str(workspace).lower().endswith(".aedt") and \
            os.path.normcase(os.path.abspath(workspace))[:-5] == os.path.normcase(b)[:-5]:
        aedt = os.path.abspath(workspace)
    return (aedt if aedt and os.path.isfile(aedt) else None), b


def copy_board(board, workspace, target_aedt, log=print):
    """042: merged project = COPY of the user's board project: <target>.aedt (+ .aedb). The board is only read.
    Board without .aedt: the .aedb is copied, then opened once in AEDT (project file created) by merge_designs."""
    aedt, aedb = board_project_files(board, workspace)
    if not os.path.isdir(aedb):
        raise RuntimeError(f"board .aedb not found: {aedb}")
    dst_aedb = target_aedt[:-5] + ".aedb"
    if os.path.exists(target_aedt) or os.path.exists(dst_aedb):
        raise RuntimeError(f"merge target already exists: {target_aedt}")
    nbytes = _copy_aedb(aedb, dst_aedb)
    if aedt:
        shutil.copy2(aedt, target_aedt)
        nbytes += os.path.getsize(aedt)
    log(f"[board copy] {aedt or aedb} -> {target_aedt} ({nbytes / 1e6:.1f} MB)")
    return {"aedt": target_aedt, "aedb": dst_aedb, "bytes": nbytes, "from_aedt": bool(aedt)}


def _components(edb):
    out = {}
    for rd, c in edb.components.instances.items():
        out[rd] = {"pins": sorted(str(p) for p in c.pins), "part": c.partname or ""}
    return out


def component_diffs(ref, got):
    """042: components of the merged design vs the channel design -> lines ([] = same)."""
    out = []
    for rd, r in sorted(ref.items()):
        g = got.get(rd)
        if g is None:
            out.append(f"{rd} missing")
            continue
        if g["pins"] != r["pins"]:
            out.append(f"{rd} pins {len(r['pins'])} -> {len(g['pins'])}")
        if not g["part"] and r["part"]:
            out.append(f"{rd} part name {r['part']} -> (empty)")
    out += [f"{rd} extra" for rd in sorted(set(got) - set(ref))]
    return out


def merged_checks(merged_aedb, design, channel_aedb, board_stackup=None, version=None):
    """042: read the merged design back (read only, AEDT closed) and compare with the channel design: components / pins
    and stackup (vs board_stackup when given, else vs the channel). -> {"pins": [..], "stackup": [..]}."""
    from ..core.edb import edb_session
    from . import stackup_check as SC
    with edb_session(channel_aedb, None, True, version) as e:
        comps_c, st_c = _components(e), SC.read(e)
    with edb_session(merged_aedb, design, True, version) as e:
        comps_m, st_m = _components(e), SC.read(e)
    return {"pins": component_diffs(comps_c, comps_m), "stackup": SC.compare(board_stackup or st_c, st_m)}


def merge_designs(orig, sources, out_dir, port=None, log=print, create_if_missing=False, backup=True,
                  board_stackup=None):
    """Gộp các project channel (sources {tên: .aedb}) vào project orig (.aedt), mỗi channel 1 design mới.
    Sao lưu orig vào <out_dir>/_backup/<time>/ trước. Trả {project, backup, designs, channels{tên: ...}}.
    038 create_if_missing: orig chưa có -> tạo project rỗng (NewProject + SaveAs), không có gì để sao lưu.
    042 backup=False: orig is the tool's own board copy. orig .aedt missing but <orig>.aedb present (board copied
    as .aedb only) -> the .aedb is opened as the project. After the merge every merged design is read back:
    channels[n].checks {pins, stackup}; any line -> state error. board_designs_before / _after."""
    from ansys.aedt.core import Desktop, Hfss3dLayout
    from .aedt_finish import apply_display

    if os.path.exists(orig + ".lock") and not port:
        raise RuntimeError("Project gốc đang mở/khoá trong AEDT. Đóng project hoặc truyền port của phiên AEDT đó.")
    sel = list(sources)
    m = config.machine()
    port = port or None
    aedb_only = not os.path.exists(orig) and os.path.isdir(orig[:-5] + ".aedb")   # 042: board copied as .aedb only
    new_project = create_if_missing and not os.path.exists(orig) and not aedb_only
    bdir = None if (new_project or aedb_only or not backup) else _backup(orig, out_dir, log)
    desk = Desktop(version=m["aedt_version"], non_graphical=not port, new_desktop=not port,
                   close_on_exit=not port, port=int(port) if port else 0)
    od = desk.odesktop
    results = {}
    try:
        # 1) Chuẩn bị project từng channel: mở .aedb -> .aedt, tô màu net, lưu, ghi lại thông tin để so.
        for n in sel:
            src = sources[n]
            try:
                h = Hfss3dLayout(project=src, version=m["aedt_version"], new_desktop=False)
                warns = []
                apply_display(h, warnings=warns)
                h.save_project()
                results[n] = {"src_aedt": h.project_file, "src_design": h.design_name, "src": _info(h),
                              "warnings": warns}
                for w in warns:
                    log(f"[prepare] {n} WARNING: {w}")
                h.close_project(save=True)
                log(f"[prepare] {n}: {results[n]['src_aedt']}")
            except Exception as ex:
                traceback.print_exc()
                results[n] = {"state": "error", "error": f"chuẩn bị: {type(ex).__name__}: {ex}"}

        # 2) Mở project gốc, dán từng design.
        if new_project:                                   # 038: project gộp mới trong thư mục request (không design nào)
            oproj = od.NewProject()
            oproj.SaveAs(orig, True)
            log(f"[merge] new project {orig}")
        elif aedb_only:                                   # 042: open the copied board .aedb -> project file
            o = Hfss3dLayout(project=orig[:-5] + ".aedb", version=m["aedt_version"], new_desktop=False)
            oproj = o.oproject
            oproj.Save()
            log(f"[merge] board copy opened from .aedb: {o.project_file}")
        else:
            o = Hfss3dLayout(project=orig, version=m["aedt_version"], new_desktop=False)
            oproj = o.oproject
        board_before = _designs(oproj)
        for n in sel:
            r = results[n]
            if r.get("state") == "error":
                continue
            try:
                before = set(_designs(oproj))
                pf = od.OpenProject(r["src_aedt"])
                pf_name = pf.GetName()
                pf.CopyDesign(r["src_design"])
                oproj.Paste()
                od.CloseProject(pf_name)
                new = sorted(set(_designs(oproj)) - before)
                if len(new) != 1:
                    raise RuntimeError(f"Dán design không rõ kết quả: {new}")
                target = _unique(n, before)
                if new[0] != target:
                    oproj.SetActiveDesign(new[0]).RenameDesignInstance(new[0], target)
                oproj.Save()
                chk = Hfss3dLayout(project=oproj.GetName(), design=target, new_desktop=False)
                got = _info(chk)
                diff = [k for k in ("ports", "setups", "sweeps") if got[k] != r["src"][k]]
                r.update(design=target, merged=got,
                         state="error" if diff else ("renamed" if target != n else "ok"),
                         error=f"khác project channel ở: {diff}" if diff else None)
                log(f"[merge] {n} -> {target}: {r['state']}")
            except Exception as ex:
                traceback.print_exc()
                r.update(state="error", error=f"{type(ex).__name__}: {ex}")
        oproj.Save()
        designs = _designs(oproj)
        out = {"project": orig, "backup": bdir, "designs": designs,
               "board_designs_before": board_before, "board_designs_after": [d for d in board_before if d in designs],
               "channels": {n: {k: results[n].get(k) for k in ("state", "design", "error", "warnings", "src_aedt")}
                            for n in sel}}
    finally:
        desk.release_desktop(close_projects=not port, close_on_exit=not port)
    lost = [d for d in out["board_designs_before"] if d not in out["designs"]]
    if lost:                                                            # never expected: paste only adds designs
        out["error"] = f"designs of the target lost: {lost}"
    if not port:                                                        # 042: read every merged design back
        for n, r in out["channels"].items():
            if r.get("state") not in ("ok", "renamed"):
                continue
            try:
                chk = merged_checks(orig[:-5] + ".aedb", r["design"], sources[n], board_stackup, m["aedt_version"])
            except Exception as ex:
                chk = {"pins": [f"merged design unreadable: {type(ex).__name__}: {ex}"], "stackup": []}
            r["checks"] = chk
            lines = [f"pins: {x}" for x in chk["pins"]] + [f"stackup: {x}" for x in chk["stackup"]]
            if lines:
                r.update(state="error", error="; ".join(lines)[:600])
            log(f"[merge check] {n}: " + ("OK" if not lines else "; ".join(lines)[:300]))
    return out
