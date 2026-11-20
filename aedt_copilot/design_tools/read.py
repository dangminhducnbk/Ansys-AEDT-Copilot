"""Đọc (chỉ đọc) trạng thái design: setup / sweep, airbox, port, solder ball (feature 007)."""
NAME = "read"
ORDER = 0
SECTIONS = ()


def _safe(fn, default=None):
    try:
        return fn()
    except Exception as ex:
        return default if default is not None else f"unreadable: {type(ex).__name__}"


def setups(edb):
    from ..interface_sim.apply import read_setup
    out = {}
    for name, st in _safe(lambda: dict(edb.setups), {}).items():
        sweeps = _safe(lambda: list(st.sweeps), [])
        if sweeps:
            for sw in sweeps:
                out[f"{name}/{sw}"] = read_setup(st, sw)
        else:
            out[name] = {"sweep": "none"}
    return out


def airbox(edb):
    from ..interface_sim.apply import read_airbox
    return _safe(lambda: read_airbox(edb), {})


def ports(edb):
    return sorted(_safe(lambda: list(dict(edb.ports)), []))


def solder_balls(edb, refdes=None):
    out = {}
    inst = _safe(lambda: dict(edb.components.instances), {})
    for rd in (refdes or inst):
        c = inst.get(rd)
        if c is None:
            continue
        try:
            sbp = c._edb_object.GetComponentProperty().GetSolderBallProperty()
            h = str(sbp.GetHeightValue().ToString() if hasattr(sbp.GetHeightValue(), "ToString") else sbp.GetHeightValue())
            d = sbp.GetDiameterValue()
            d = d[1] if isinstance(d, tuple) and len(d) > 1 else d
            d = str(d.ToString() if hasattr(d, "ToString") else d)
            if h in ("", "0", "0mm", "0.0") and d in ("", "0", "0mm", "0.0"):
                continue
            out[rd] = {"diameter": d, "height": h}
        except Exception:
            continue
    return out


def snapshot(edb):
    return {"setups": setups(edb), "airbox": airbox(edb), "ports": {p: True for p in ports(edb)},
            "solder_balls": solder_balls(edb)}


def validate(values, targets):
    return None, targets


def prepare(edb, P, targets):
    return targets


def run(edb, P, targets, log):
    return {"snapshot": snapshot(edb)}


def check(edb, P, targets):
    return []
