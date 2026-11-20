"""042: stackup of a design vs the original board (after cut and after merge).

read(edb) -> {"layers": [{name, type, material, fill, thickness_um}], "materials": {name: {permittivity, loss_tangent,
conductivity}}} (stackup order, only the materials the layers use). compare(ref, got) -> difference lines ([] = same).
"""
THICK_TOL_UM = 0.01
PROP_REL = 1e-6
PROPS = ("permittivity", "loss_tangent", "conductivity")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mat_props(edb, name):
    try:
        m = edb.materials[name]
    except Exception:
        return None
    out = {}
    for k, attrs in (("permittivity", ("permittivity",)), ("loss_tangent", ("dielectric_loss_tangent", "loss_tangent")),
                     ("conductivity", ("conductivity",))):
        v = None
        for a in attrs:
            v = _num(getattr(m, a, None))
            if v is not None:
                break
        out[k] = v
    return out


def read(edb):
    """Layers (stackup order) + properties of the materials they use."""
    layers, used = [], []
    for name, l in edb.stackup.layers.items():
        fill = getattr(l, "fill_material", None) or ""
        if str(getattr(l, "type", "")).lower() == "dielectric":
            fill = ""                                                   # dielectric layers have no fill
        row = {"name": name, "type": str(getattr(l, "type", "")), "material": getattr(l, "material", "") or "",
               "fill": fill, "thickness_um": round(float(l.thickness) * 1e6, 4)}
        layers.append(row)
        for m in (row["material"], row["fill"]):
            if m and m not in used:
                used.append(m)
    return {"layers": layers, "materials": {m: _mat_props(edb, m) for m in used}}


def _prop_diff(a, b):
    if a is None or b is None:
        return a != b
    return abs(a - b) > max(PROP_REL * abs(a), 1e-12)


def compare(ref, got):
    """ref / got = read() dicts -> ['<difference>', ...]."""
    if not ref or not got:
        return []
    out = []
    rl, gl = [l["name"] for l in ref["layers"]], [l["name"] for l in got["layers"]]
    for n in rl:
        if n not in gl:
            out.append(f"missing layer {n}")
    for n in gl:
        if n not in rl:
            out.append(f"extra layer {n}")
    common_r, common_g = [n for n in rl if n in gl], [n for n in gl if n in rl]
    if common_r != common_g:
        out.append(f"layer order: {' / '.join(common_r)} -> {' / '.join(common_g)}")
    gd = {l["name"]: l for l in got["layers"]}
    for r in ref["layers"]:
        g = gd.get(r["name"])
        if not g:
            continue
        if r["type"] != g["type"]:
            out.append(f"{r['name']} type {r['type']} -> {g['type']}")
        if abs(r["thickness_um"] - g["thickness_um"]) > THICK_TOL_UM:
            out.append(f"{r['name']} thickness {r['thickness_um']:g} -> {g['thickness_um']:g} um")
        if r["material"] != g["material"]:
            out.append(f"{r['name']} material {r['material']} -> {g['material']}")
        if r["fill"] != g["fill"]:
            out.append(f"{r['name']} fill {r['fill']} -> {g['fill']}")
    gm = got.get("materials") or {}
    for name, rp in (ref.get("materials") or {}).items():
        gp = gm.get(name)
        if gp is None or rp is None:
            continue                                                    # material renamed: reported per layer
        for k in PROPS:
            if _prop_diff(rp.get(k), gp.get(k)):
                out.append(f"{name} {k} {rp.get(k):g} -> {gp.get(k):g}" if None not in (rp.get(k), gp.get(k))
                           else f"{name} {k} {rp.get(k)} -> {gp.get(k)}")
    return out
