"""Bước 4: copy workspace sang thư mục simulation trên server remote, giải lần lượt từng design (contract isim-run.md).

Chỉ chạy khi người dùng yêu cầu. Mặc định (mode 'service'): server chạy PyAEDT service manager (port 17878),
tool mở AEDT không giao diện trên server, copy vào thư mục share (sim_dir) hoặc upload qua phiên RPyC
(sim_dir_server). Mode 'grpc': AEDT người dùng đã mở (-grpcsrv port). Không bao giờ ghi đè: mỗi lần chạy 1 thư mục mới.
"""
import datetime as dt
import os
import shutil
import subprocess
import sys

from ..core.errors import CopilotInputError
from ..core.validate import require_int, require_text
from . import report, request as R

EXCLUDE = ("*.aedtresults", "*.lock", "_backup", "Ansys AEDT Copilot", "*.auto")


def _size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    tot = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                tot += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return tot


def plan_copy(workspace, sim_dir, request_id, now=None):
    if not sim_dir or not os.path.isdir(sim_dir):
        raise CopilotInputError("sim_dir", "existing simulation folder reachable from this PC", sim_dir)
    if not os.access(sim_dir, os.W_OK):
        raise CopilotInputError("sim_dir", "writable folder", sim_dir)
    aedb = os.path.splitext(workspace)[0] + ".aedb"
    src = [workspace] + ([aedb] if os.path.isdir(aedb) else [])
    nbytes = sum(_size(s) for s in src)
    free = shutil.disk_usage(sim_dir).free
    if free < nbytes * 1.1:
        raise CopilotInputError("sim_dir", f"free space >= {nbytes * 1.1 / 1e9:.2f} GB", f"{free / 1e9:.2f} GB")
    tag = (now or dt.datetime.now()).strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(sim_dir, f"{request_id}_{tag}")
    if os.path.exists(dst):
        raise CopilotInputError("sim_dir", "new run folder (never overwrite)", dst)
    return {"src": src, "dst_folder": dst, "bytes": nbytes, "excluded": list(EXCLUDE)}


def server_path(local_path, sim_dir_local, sim_dir_server=""):
    lp, base = os.path.normcase(os.path.abspath(local_path)), os.path.normcase(os.path.abspath(sim_dir_local))
    if not (lp == base or lp.startswith(base.rstrip("\\/") + os.sep)):
        raise CopilotInputError("local_path", f"path under {sim_dir_local}", local_path)
    if not sim_dir_server:
        return os.path.abspath(local_path)
    rel = os.path.relpath(os.path.abspath(local_path), os.path.abspath(sim_dir_local))
    sep = "\\" if ("\\" in sim_dir_server or ":" in sim_dir_server[:3]) else "/"
    return sim_dir_server.rstrip("\\/") + sep + rel.replace(os.sep, sep)


def _merged_designs(req):
    out = []
    for n in req["interfaces"]:
        try:
            st = R.get_state(req["request_id"], n)
        except CopilotInputError:
            continue
        if st["step"] == "merged":
            out.append({"interface": n, "design": st["merged"]["design"],
                        "setup": ((st.get("settings") or {}).get("values") or {}).get("setup.name") or "Setup1"})
    return out


MODES = ("service", "grpc")


def _server_cfg(server):
    """config.yaml sim_servers: mục có host / name trùng server (để lấy pre_grpc_args, port mặc định)."""
    from ..core.config import machine
    for s in machine().get("sim_servers") or []:
        if isinstance(s, dict) and server in (str(s.get("host")), str(s.get("name"))):
            return s
    return {}


def _copy_filtered(srcs, dst_folder):
    os.makedirs(dst_folder)
    for s in srcs:
        d = os.path.join(dst_folder, os.path.basename(s))
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns(*EXCLUDE))
        else:
            shutil.copy2(s, d)


def start(request_id="", server="", port=17878, sim_dir="", sim_dir_server="", designs=(), mode="service",
          aedt_port=50000, client_port=18050, spawn=True):
    """mode 'service': PyAEDT service manager trên server (port 17878) mở AEDT không giao diện (aedt_port);
    sim_dir trống -> upload qua phiên RPyC vào sim_dir_server. mode 'grpc': AEDT người dùng đã mở (-grpcsrv port)."""
    from ..core.validate import require_choice
    req = R.load(request_id)
    mode = require_choice("mode", mode, MODES)
    server = require_text("server", server)
    port = require_int("port", int(port) if str(port).isdigit() else port, 1, 65535)
    aedt_port = require_int("aedt_port", int(aedt_port) if str(aedt_port).isdigit() else aedt_port, 1, 65535)
    client_port = require_int("client_port", int(client_port) if str(client_port).isdigit() else client_port, 1, 65535)
    merged = _merged_designs(req)
    if not merged:
        raise CopilotInputError("designs", "at least one merged interface (run isim_merge first)", [])
    if isinstance(designs, str):
        designs = [d for d in designs.split(",") if d.strip()]
    if designs:
        names = {m["design"] for m in merged}
        bad = [d for d in designs if d not in names]
        if bad:
            raise CopilotInputError("designs", "merged design names " + ", ".join(sorted(names)), bad)
        merged = [m for d in designs for m in merged if m["design"] == d]
    proj = req.get("merged_project") or req["workspace"]  # 038: project gộp trong thư mục request
    aedb = os.path.splitext(proj)[0] + ".aedb"
    srcs = [proj] + ([aedb] if os.path.isdir(aedb) else [])
    tag = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    if sim_dir:                                           # thư mục share: copy trực tiếp
        pl = plan_copy(proj, sim_dir, req["request_id"])
        try:
            _copy_filtered(srcs, pl["dst_folder"])
        except PermissionError as ex:                      # os.access không thấy quyền share (SMB) chỉ đọc
            raise CopilotInputError("sim_dir", "folder this PC can write (share is read-only: leave sim_dir empty "
                                    "to upload through the service session)", sim_dir) from ex
        run_id = os.path.basename(pl["dst_folder"])
        proj_local = os.path.join(pl["dst_folder"], os.path.basename(proj))
        transfer, staging, folder = "local", None, pl["dst_folder"]
        proj_server = server_path(proj_local, sim_dir, sim_dir_server)
        nbytes = pl["bytes"]
    else:                                                 # không share: upload qua phiên RPyC (service)
        if mode != "service":
            raise CopilotInputError("sim_dir", "shared simulation folder reachable from this PC (grpc mode)", sim_dir)
        sim_dir_server = require_text("sim_dir_server", sim_dir_server)
        run_id = f"{req['request_id']}_{tag}"
        staging = os.path.join(R.work_dir(req), "_upload", run_id)
        if os.path.exists(staging):
            raise CopilotInputError("run", "new run folder (never overwrite)", staging)
        _copy_filtered(srcs, staging)
        sep = "\\" if ("\\" in sim_dir_server or ":" in sim_dir_server[:3]) else "/"
        folder = sim_dir_server.rstrip("\\/") + sep + run_id
        proj_server = folder + sep + os.path.basename(proj)
        transfer, nbytes = "upload", sum(_size(s) for s in srcs)
    cfg = _server_cfg(server)
    data = {"run_id": run_id, "mode": mode, "transfer": transfer, "staging": staging, "server": server, "port": port,
            "aedt_port": aedt_port, "client_port": client_port, "pre_grpc_args": bool(cfg.get("pre_grpc_args")),
            "sim_dir_local": os.path.abspath(sim_dir) if sim_dir else "", "sim_dir_server": sim_dir_server,
            "folder": folder, "project_server": proj_server, "state": "queued",
            "designs": [dict(m, state="queued", start=None, end=None, seconds=None, message=None) for m in merged]}
    path = os.path.join(R.work_dir(req), f"run_{run_id}.json")
    R.wjson(path, data)
    if spawn:
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0      # DETACHED_PROCESS | NEW_PROCESS_GROUP
        from ..core.config import ROOT, machine
        args_file = os.path.join(R.work_dir(req), f"run_{run_id}.args.json")
        R.wjson(args_file, {"run_json": path})
        logf = open(os.path.join(R.work_dir(req), f"run_{run_id}.log"), "w", encoding="utf-8")
        from .. import aedt_env
        subprocess.Popen([machine()["python"], "-u", "-m", "aedt_copilot", "isim", "--op=solve_loop",
                          f"--args-file={args_file}"], cwd=ROOT, env=aedt_env.child_env(), stdout=logf,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    return {"run_id": run_id, "mode": mode, "transfer": transfer, "folder": folder, "project_server": proj_server,
            "run_json": path, "designs": [m["design"] for m in merged], "bytes": nbytes}


def _now():
    return dt.datetime.now().isoformat(timespec="seconds")


def _solver_for(desk, data):
    from ansys.aedt.core import Hfss3dLayout
    opened = {}

    def solve(design, setup):
        h = Hfss3dLayout(project=data["project_server"], design=design, new_desktop=False)
        opened["name"] = h.project_name
        ok = h.analyze_setup(setup)
        h.save_project()
        if ok is False:
            raise RuntimeError(f"analyze_setup({setup}) returned False")
        return getattr(h, "results_directory", "") or ""
    return solve, opened


def _pyaedt_solver(data):
    """mode grpc: AEDT người dùng đã mở trên server (-grpcsrv port). Chỉ đóng project của mình."""
    from ansys.aedt.core import Desktop
    from ansys.aedt.core.generic.settings import settings
    from ..core.config import machine
    settings.remote_rpc_session = True                     # không mở thêm AEDT ở máy này
    desk = Desktop(version=machine()["aedt_version"], machine=data["server"], port=int(data["port"]),
                   new_desktop=False, non_graphical=False, close_on_exit=False)
    solve, opened = _solver_for(desk, data)

    def close():
        try:
            if opened.get("name"):
                desk.odesktop.CloseProject(opened["name"])
        finally:
            desk.release_desktop(close_projects=False, close_on_exit=False)
    return solve, close


def _service_solver(data):
    """mode service: phiên RPyC tới service manager -> mở AEDT không giao diện trên server -> (upload) -> giải.
    Đóng AEDT do mình mở khi xong (trả license)."""
    from ansys.aedt.core import Desktop
    from ansys.aedt.core.common_rpc import create_session
    from ansys.aedt.core.generic.settings import settings
    from ..core.config import machine
    if data.get("pre_grpc_args"):                          # AEDT 2025.2 chưa có Service Pack
        os.environ["PYAEDT_USE_PRE_GRPC_ARGS"] = "True"
    settings.grpc_secure_mode = False                      # LAN, không có chứng chỉ mTLS
    settings.grpc_local = False
    settings.remote_rpc_service_manager_port = int(data["port"])
    cl = create_session(data["server"], client_port=int(data["client_port"]), launch_aedt_on_server=True,
                        aedt_port=int(data["aedt_port"]), non_graphical=True, secure=False, listen_all=True)
    if data["transfer"] == "upload":
        if cl.root.pathexists(data["folder"]):
            raise RuntimeError(f"remote folder exists (never overwrite): {data['folder']}")
        cl.root.makedirs(data["folder"])
        for name in os.listdir(data["staging"]):
            cl.filemanager.upload(os.path.join(data["staging"], name),
                                  data["folder"] + ("\\" if "\\" in data["folder"] else "/") + name)
    desk = Desktop(version=machine()["aedt_version"], machine=data["server"], port=int(cl.aedt_port),
                   new_desktop=False, non_graphical=True)
    solve, opened = _solver_for(desk, data)

    def close():
        try:
            desk.release_desktop(close_projects=True, close_on_exit=True)
        finally:
            try:
                cl.close()
            except Exception:
                pass
    return solve, close


def solve_loop(run_json, solver=None):
    data = R._rjson(run_json)
    data["state"], data["started"] = "running", _now()
    R.wjson(run_json, data)
    make = solver or (_service_solver if data.get("mode", "service") == "service" else _pyaedt_solver)
    try:
        solve, close = make(data)
    except Exception as ex:
        data.update(state="failed", finished=_now(), message=f"connect / upload: {type(ex).__name__}: {ex}")
        for d in data["designs"]:
            d.update(state="failed", message="not started (connection failed)")
        R.wjson(run_json, data)
        return data
    try:
        for d in data["designs"]:
            d.update(state="running", start=_now())
            R.wjson(run_json, data)
            t0 = dt.datetime.now()
            try:
                d["results"] = solve(d["design"], d["setup"])
                d["state"] = "done"
            except Exception as ex:
                d.update(state="failed", message=f"{type(ex).__name__}: {ex}")
            d.update(end=_now(), seconds=round((dt.datetime.now() - t0).total_seconds()))
            R.wjson(run_json, data)
    finally:
        try:
            close()
        except Exception as ex:
            print("close:", ex, file=sys.stderr)
    data["state"], data["finished"] = "done", _now()
    R.wjson(run_json, data)
    return data


def status(request_id="", run_id=""):
    req = R.load(request_id)
    w = R.work_dir(req)
    runs = sorted(f for f in os.listdir(w) if f.startswith("run_") and f.endswith(".json"))
    if run_id:
        runs = [f for f in runs if f == f"run_{run_id}.json"]
    if not runs:
        raise CopilotInputError("run_id", "existing run of this request", run_id)
    data = R._rjson(os.path.join(w, runs[-1]))
    data["table_md"] = report.table(["Design", "State", "Start", "End", "Seconds", "Message"],
                                    [[d["design"], d["state"], d["start"], d["end"], d["seconds"], d["message"]]
                                     for d in data["designs"]])
    return data
