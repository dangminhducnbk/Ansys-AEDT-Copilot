"""Request + trạng thái từng interface (contract: isim-request.md).

<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/
    request.json        workspace, board, cell, stackup, schematic[], bom, interfaces[], created, netlist
    netlist.json        036: netlist đã đọc (interface_sim/netlist.py)
    <iface>/state.json  step, content, stage1, ends, settings, result, merged, history
038 (5.0.0): request id = <board>_<yyyymmdd_hhmmss>; file của request trong <request>/_work/ (work_dir);
    thư mục nội bộ của interface = _work/<iface>/, sau khi người dùng đặt tên thư mục channel (config.html) =
    <request>/<channel folder>/_work/ (request.json channel_folders). Request cũ (không có _work/) đọc như trước.
Danh sách request: ~/.aedt_copilot/isim_requests.json (đổi bằng env AEDT_COPILOT_ISIM_REGISTRY, dùng cho test).
"""
import contextlib
import datetime as dt
import json
import os
import re

from ..core.edb import aedb_path
from ..core.errors import CopilotInputError
from ..core.unique import claim_dir, file_lock, move_aside
from ..core.validate import require_path, require_text

STEPS = ("started", "content_agreed", "cut", "ends_checked", "applied", "merged")
NETLIST_FILE = "netlist.json"                         # 036: netlist đã đọc (kết nối + giá trị linh kiện)
NAME_BAD = '<>:"/\\|?*; '
# file / thư mục kết quả bị đổi tên (không xoá) khi quay lại 'started'
# settings.json / settings.md: chỉ có ở request 0.6.0 (004 dùng user_settings.json); vẫn đổi tên nếu có
OUTPUTS = ("content.md", "stage1", "stage1.json", "ends.json", "ends.md", "settings.json", "settings.md",
           "final", "result.json", "cut.log", "apply.log")
NEXT_SETTINGS = ("settings FORM (GATE B, mandatory): isim_settings_form(request_id) -> draw the form (one tab per "
                 "interface, pre-filled; mandatory sweep fields empty) or, without widget support, show its table_md "
                 "once -> isim_validate_form -> user's go -> isim_apply. Never ask setting values one by one.")
# 025: review.json KHÔNG đổi tên khi quay lại 'started': review là bước trước GATE A; review cũ bị gate báo out_of_date.


def _now():
    return dt.datetime.now().isoformat(timespec="seconds")


WORK = "_work"                                        # 038: thư mục file nội bộ (request + channel)


def request_file(folder):
    """request.json của request (038: trong _work/; cũ: ở thư mục request). None nếu không có."""
    for p in (os.path.join(folder, WORK, "request.json"), os.path.join(folder, "request.json")):
        if os.path.isfile(p):
            return p
    return None


def work_dir(req):
    """Thư mục file nội bộ của request: <request>/_work (038) hoặc <request> (request cũ)."""
    return req.get("work") or req["folder"]


def _registry_file():
    return os.environ.get("AEDT_COPILOT_ISIM_REGISTRY") or \
        os.path.join(os.path.expanduser("~"), ".aedt_copilot", "isim_requests.json")


def _rjson(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def wjson(path, data):
    """Ghi JSON nguyên tử (file tạm + os.replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, path)


def check_name(name, taken=()):
    """Tên interface = luật tên channel: không rỗng, không <>:"/\\|?*; hay dấu cách, không trùng (không phân biệt hoa)."""
    n = require_text("name", name)
    if any(c in n for c in NAME_BAD) or not n.strip("."):           # "." / ".." = thư mục cha
        raise CopilotInputError("name", 'name without <>:"/\\|?*; or space', name)
    if n.lower() in {t.lower() for t in taken}:
        raise CopilotInputError("name", "unique interface name", name)
    return n


# ----------------------------------------------------------------------------- request
def start(workspace, board="", cell="", stackup="", schematic=(), bom="", interfaces=(), netlist=""):
    """036: netlist (tuỳ chọn) = nguồn kết nối schematic do code đọc -> <request>/netlist.json."""
    ws = require_path("workspace", workspace, "file")
    if not ws.lower().endswith(".aedt"):
        raise CopilotInputError("workspace", "existing .aedt file", ws)
    bd = aedb_path(board or ws)
    if stackup:
        stackup = require_path("stackup", stackup, "file")
    if isinstance(schematic, str):
        schematic = [s for s in schematic.split(";") if s.strip()]
    sch = []
    for s in schematic:
        s = require_path("schematic", s, "file")
        if not s.lower().endswith(".pdf"):
            raise CopilotInputError("schematic", "existing .pdf file", s)
        sch.append(s)
    if bom:
        bom = require_path("bom", bom, "file")
        if not bom.lower().endswith((".xlsx", ".xlsm", ".csv")):
            raise CopilotInputError("bom", "existing .xlsx or .csv file", bom)
    if isinstance(interfaces, str):
        interfaces = [s for s in interfaces.split(";") if s.strip()]
    names = []
    for n in interfaces:
        names.append(check_name(n, names))
    nl = None
    if netlist:
        from . import netlist as NL
        netlist = require_path("netlist", netlist, "file")
        nl = NL.parse(netlist)                                          # lỗi định dạng -> từ chối trước khi tạo thư mục
    root = os.path.join(os.path.dirname(ws), "Ansys AEDT Copilot", "interface_sim")
    # 024: tạo thư mục nguyên tử; trùng giây -> _2, _3 (2 request không bao giờ chung thư mục)
    # 038: tên = <board>_<thời gian>; file nội bộ trong _work/
    stem = safe_name(os.path.splitext(os.path.basename(bd.rstrip("/\\")))[0])[:60] or "board"
    folder = claim_dir(os.path.join(root, f"{stem}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"))
    rid = os.path.basename(folder)
    req = {"request_id": rid, "workspace": ws, "board": bd, "cell": cell or "", "stackup": stackup or "",
           "schematic": sch, "bom": bom or "", "interfaces": names, "created": _now(), "netlist": netlist or "",
           "layout": "038", "channel_folders": {}, "review_first": True,     # 039: review question before config
           "review_page": True}                                             # 045: review + settings on one page
    work = os.path.join(folder, WORK)
    wjson(os.path.join(work, "request.json"), req)
    if nl:
        nl["parsed_at"] = _now()
        wjson(os.path.join(work, NETLIST_FILE), nl)
    with file_lock(_registry_file() + ".lock"):                         # 024: không mất mục khi chạy song song
        reg = _rjson(_registry_file(), []) or []
        reg.append({"request_id": rid, "folder": folder, "created": req["created"], "workspace": norm_path(ws)})
        wjson(_registry_file(), reg)
    out = {"request_id": rid, "folder": folder}
    if nl:
        out["netlist"] = NL.summary(nl, netlist)
    return out


def norm_path(p):
    """So khớp đường dẫn workspace (không phân biệt hoa / thường, dấu gạch chéo)."""
    return os.path.normcase(os.path.abspath(p))


def registry():
    """Các request còn thư mục (cũ nhất trước)."""
    reg = _rjson(_registry_file(), []) or []
    return [r for r in reg if request_file(r["folder"])]


def folder(request_id=""):
    reg = _rjson(_registry_file(), []) or []
    reg = [r for r in reg if request_file(r["folder"])]
    if not reg:
        raise CopilotInputError("request_id", "existing request (run isim_start first)", request_id)
    if not request_id:
        return reg[-1]["folder"]
    for r in reversed(reg):
        if r["request_id"] == request_id:
            return r["folder"]
    raise CopilotInputError("request_id", "existing request", request_id)


def load(request_id=""):
    f = folder(request_id)
    p = request_file(f)
    req = _rjson(p)
    req["folder"] = f
    req["work"] = os.path.dirname(p)                                  # 038: _work/ ; cũ: = folder
    return req


def save_request(req):
    d = {k: v for k, v in req.items() if k not in ("folder", "work")}
    wjson(os.path.join(work_dir(req), "request.json"), d)


def add_interface(request_id, name):
    """Thêm tên interface vào request (nếu chưa có). Trả request."""
    req = load(request_id)
    if name not in req["interfaces"]:
        check_name(name, req["interfaces"])
        req["interfaces"].append(name)
        save_request(req)
    return req


# ----------------------------------------------------------------------------- state
def iface_dir(request_id, name):
    """Thư mục nội bộ của interface; tên được kiểm tra trước (không thoát ra ngoài thư mục request).
    038: <request>/<channel folder>/_work khi đã đặt tên thư mục channel, <request>/_work/<name> trước đó."""
    return iface_dir_of(load(request_id), check_name(name))


def iface_dir_of(req, name):
    """Như iface_dir cho một request đã đọc (req có folder; 'work' tự suy ra nếu thiếu). Không đọc registry."""
    if req.get("layout") != "038":
        return os.path.join(req["folder"], name)
    cf = (req.get("channel_folders") or {}).get(name)
    return os.path.join(req["folder"], cf, WORK) if cf else os.path.join(req["folder"], WORK, name)


def read_folder(folder):
    """request.json của một thư mục request bất kỳ (cả 2 kiểu) + folder / work; None nếu không phải request."""
    p = request_file(folder)
    req = _rjson(p) if p else None
    if req is not None:
        req["folder"], req["work"] = folder, os.path.dirname(p)
    return req


def channel_dir(request_id, name):
    """038: thư mục channel <request>/<folder> (None khi chưa đặt tên / request cũ)."""
    req = load(request_id)
    cf = (req.get("channel_folders") or {}).get(name)
    return os.path.join(req["folder"], cf) if cf else None


def set_channel_folder(request_id, name, folder_name):
    """038: tên thư mục channel do người dùng nhập (config.html). Kiểm tra tên (luật tên channel, không trùng thư mục
    channel khác, không phải _work), chuyển thư mục nội bộ của interface vào <request>/<folder>/_work. -> đường dẫn."""
    req = load(request_id)
    if req.get("layout") != "038":
        raise CopilotInputError("request_id", "request created by 5.0.0 or later (channel folders)", request_id)
    n = check_name(name)
    if n not in req["interfaces"]:
        raise CopilotInputError("name", "interface of this request", name)
    cmap = dict(req.get("channel_folders") or {})
    fo = check_name(folder_name, [v for k, v in cmap.items() if k != n] + [WORK])
    old = iface_dir(req["request_id"], n)
    new = os.path.join(req["folder"], fo, WORK)
    if os.path.normcase(os.path.abspath(old)) == os.path.normcase(os.path.abspath(new)):
        return new
    if os.path.exists(new):
        raise CopilotInputError("folder", "a channel folder name not used yet in this request", fo)
    os.makedirs(os.path.dirname(new), exist_ok=True)
    if os.path.isdir(old):
        os.replace(old, new)
        prev = os.path.dirname(old)
        if cmap.get(n) and os.path.isdir(prev) and not os.listdir(prev):
            os.rmdir(prev)                                              # thư mục channel cũ (rỗng) của chính channel này
    else:
        os.makedirs(new)
    cmap[n] = fo
    req["channel_folders"] = cmap
    save_request(req)
    return new


def _state_path(request_id, name):
    return os.path.join(iface_dir(request_id, name), "state.json")


def get_state(request_id, name):
    st = _rjson(_state_path(request_id, name))
    if st is None:
        raise CopilotInputError("interface", "existing interface (run isim_trace first)", name)
    return st


def new_state(request_id, name):
    """Tạo state 'started' cho interface mới (hoặc trả state đang có)."""
    p = _state_path(request_id, name)
    st = _rjson(p)
    if st is None:
        st = {"name": name, "step": "started", "failed": False, "error": None, "content": None,
              "content_agreed_at": None, "stage1": None, "ends": None, "settings": None, "result": None,
              "merged": None, "history": [{"time": _now(), "step": "started", "note": "created"}]}
        wjson(p, st)
    return st


def set_state(request_id, name, note="", **changes):
    st = get_state(request_id, name)
    st.update(changes)
    st["history"].append({"time": _now(), "step": st["step"], "note": note or ",".join(sorted(changes))})
    wjson(_state_path(request_id, name), st)
    return st


def require_step(state, expected):
    """Bước hiện tại phải là expected (str hoặc tuple). Interface đang 'failed' -> so với bước tốt cuối cùng."""
    exp = (expected,) if isinstance(expected, str) else tuple(expected)
    if state["step"] not in exp:
        raise CopilotInputError("step", " or ".join(exp), state["step"])


def advance(request_id, name, to_step, note=""):
    """Chuyển bước. Chỉ tiến 1 bước; 'started' từ mọi bước (đổi tên kết quả cũ thành *_old_<time>, không xoá)."""
    if to_step not in STEPS:
        raise CopilotInputError("to_step", "one of " + ", ".join(STEPS), to_step)
    st = get_state(request_id, name)
    cur = STEPS.index(st["step"])
    if to_step == "started":
        tag = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        d = iface_dir(request_id, name)
        for o in OUTPUTS:
            p = os.path.join(d, o)
            if os.path.exists(p):
                root, ext = os.path.splitext(p) if os.path.isfile(p) else (p, "")
                move_aside(p, f"{root}_old_{tag}{ext}")                   # 024: không ghi đè bản _old_ cũ
        from . import user_settings
        user_settings.replace(request_id, name)                       # mục cũ -> replaced[]
        return set_state(request_id, name, note or "reset", step="started", failed=False, error=None,
                         content_agreed_at=None, stage1=None, ends=None, settings=None, result=None, merged=None)
    if STEPS.index(to_step) != cur + 1:
        raise CopilotInputError("to_step", f"{STEPS[cur + 1] if cur + 1 < len(STEPS) else '(last step)'}", to_step)
    return set_state(request_id, name, note, step=to_step, failed=False, error=None)


def fail(request_id, name, error):
    """Đánh dấu lỗi; giữ nguyên bước tốt cuối cùng (làm lại từ bước đó)."""
    return set_state(request_id, name, "failed: " + str(error)[:200], failed=True, error=str(error))


# ----------------------------------------------------------------------------- busy lock
def _pid_alive(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259           # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@contextlib.contextmanager
def busy(request_id, name):
    """Khoá <iface>/.busy (1 tiến trình / interface). Khoá của tiến trình đã chết -> thay."""
    d = iface_dir(request_id, name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, ".busy")
    for _ in range(2):
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            holder = _rjson(p, {}) or {}
            if _pid_alive(int(holder.get("pid") or 0)):
                raise CopilotInputError("interface", "not busy (another process works on it)", holder)
            os.remove(p)                                 # khoá treo
    else:
        raise CopilotInputError("interface", "not busy", name)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "time": _now()}, f)
    try:
        yield d
    finally:
        try:
            os.remove(p)
        except OSError:
            pass


# ----------------------------------------------------------------------------- status
def _review_label(rid, name):
    """035: ô Review (not reviewed / out of date / approval out of date / no report / report ready / approved)."""
    from . import review
    try:
        return review.status_label(review.gate_status(rid, name))
    except (CopilotInputError, ValueError, OSError, KeyError) as ex:
        return f"? ({type(ex).__name__})"


def status(request_id=""):
    from . import report
    req = load(request_id)
    rows = []
    for n in req["interfaces"]:
        try:
            st = get_state(req["request_id"], n)
        except CopilotInputError:
            rows.append({"name": n, "step": "(not started)", "failed": False, "error": None, "warnings": []})
            continue
        warns = (st.get("result") or {}).get("warnings") or []
        unusual = [u["rule"] for e in ((st.get("ends") or {}).get("ends") or {}).values() for u in e.get("unusual", [])]
        rows.append({"name": n, "step": st["step"], "failed": st.get("failed"), "error": st.get("error"),
                     "unusual": unusual, "warnings": warns,
                     "merged": (st.get("merged") or {}).get("design"), "review": _review_label(req["request_id"], n)})
    md = report.table(["Interface", "Step", "Review", "Failed", "Unusual", "Warnings", "Merged as"],
                      [[r["name"], r["step"], r.get("review") or "", "yes: " + str(r["error"])[:80] if r.get("failed")
                        else "", ", ".join(r.get("unusual") or []), len(r.get("warnings") or []), r.get("merged") or ""]
                       for r in rows])
    return {"request_id": req["request_id"], "workspace": req["workspace"], "interfaces": rows, "table_md": md}


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)
