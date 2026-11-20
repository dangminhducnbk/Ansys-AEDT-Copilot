"""Đọc board và dò channel (net giữa 2 linh kiện, kể cả qua tụ/điện trở nối tiếp)."""
import fnmatch
import math

SERIES_TYPES = ("resistor", "capacitor", "inductor")


def open_edb(aedb, cell=None, readonly=True, version=None):
    """Mở EDB qua aedt_env.open_edb (tìm AEDT, version tường minh, grpc=False). version None = theo config.yaml."""
    from ..aedt_env import open_edb as _open_edb
    return _open_edb(aedb, cell, readonly, version)


def board_summary(edb, top_n=30):
    layers = list(edb.stackup.signal_layers)
    comps = edb.components.instances
    big = sorted(comps.items(), key=lambda kv: -kv[1].numpins)[:top_n]
    return {
        "cells": [c.GetName() for c in edb.active_db.CircuitCells],
        "active_cell": edb.active_cell.GetName(),
        "signal_layers": layers,
        "n_nets": len(edb.nets.netlist),
        "n_components": len(comps),
        "power_ground_nets": list(edb.nets.power.keys()),
        "big_components": [{"refdes": rd, "part": c.partname, "pins": c.numpins, "type": c.type,
                            "layer": c.placement_layer} for rd, c in big],
    }


def inspect(board, cell=None):
    """Tổng quan board (.aedt / .aedb): mở chỉ đọc (version theo config.yaml) -> board_summary -> luôn đóng EDB."""
    from . import config, naming
    aedb, _ = naming.board_paths(board)
    edb = open_edb(aedb, cell, True, config.machine()["aedt_version"])
    try:
        return board_summary(edb)
    finally:
        edb.close()


def _net_components(edb, net):
    try:
        return dict(edb.nets.nets[net].components)
    except Exception:
        return {}


def _comp_nets(comp):
    return sorted({p.net_name for p in comp.pins.values() if p.net_name})


def trace_channel(edb, comp_a, comp_b, patterns=None, ref_nets=("GND",), max_depth=3):
    """Trả {nets, series, end_types, warnings}.
    patterns: danh sách mẫu net (fnmatch, vd 'CPHY_B02DEVA_*') hoặc tên net cụ thể. Trống = mọi net tín hiệu của comp_a."""
    warnings = []
    comps = edb.components.instances
    for rd in (comp_a, comp_b):
        if rd not in comps:
            raise ValueError(f"Không có linh kiện {rd} trong board")
    pg = set(edb.nets.power.keys()) | set(ref_nets)
    a_nets = [n for n in _comp_nets(comps[comp_a]) if n not in pg]
    if patterns:
        start = [n for n in a_nets if any(fnmatch.fnmatchcase(n, p) or n == p for p in patterns)]
        if not start:
            warnings.append(f"No net of {comp_a} matches {patterns}")
    else:
        start = a_nets
    b_nets = set(_comp_nets(comps[comp_b]))

    nets, series, reached = set(start), {}, set()
    chains = {}
    for n0 in start:
        frontier, seen, path = [n0], {n0}, []
        for _ in range(max_depth + 1):
            nxt = []
            for n in frontier:
                if n in b_nets:
                    reached.add(n0)
                for rd, c in _net_components(edb, n).items():
                    if rd in (comp_a, comp_b):
                        continue
                    ctype = (getattr(c, "type", "") or "").lower()
                    if c.numpins == 2 and ctype in SERIES_TYPES:
                        others = [m for m in _comp_nets(c) if m != n and m not in pg]
                        for m in others:
                            if m not in seen:
                                seen.add(m)
                                nxt.append(m)
                                series[rd] = {"type": c.type, "part": c.partname, "nets": _comp_nets(c)}
                                path.append(rd)
            if n0 in reached or not nxt:
                break
            frontier = nxt
        chains[n0] = sorted(seen)
        if n0 in reached:
            nets |= seen
    for n0 in start:
        if n0 not in reached:
            warnings.append(f"Net {n0} does not reach {comp_b} (also via series parts) - dropped from channel")
    nets = sorted(n for n in nets if any(n in chains[s] for s in reached))
    # chỉ giữ series nằm trên chuỗi đã tới đích
    series = {rd: v for rd, v in series.items() if all(m in nets or m in pg for m in v["nets"])}
    return {
        "nets": nets,
        "start_nets": sorted(reached),
        "series": series,
        "end_types": {rd: end_type(edb, comps[rd], set(nets)) for rd in (comp_a, comp_b)},
        "warnings": warnings,
    }


def end_type(edb, comp, nets):
    """'bga' | 'through_hole' | 'smd' | 'smd_via_in_pad'."""
    if "BGA" in (comp.partname or "").upper():
        return "bga"
    sig = [p for p in comp.pins.values() if p.net_name in nets]
    if not sig:
        return "unknown"
    p = sig[0]
    if p.start_layer != p.stop_layer:
        return "through_hole"
    try:
        (x0, y0), (x1, y1) = p.bounding_box
        w = min(x1 - x0, y1 - y0)
        cx, cy = p.position
        for v in edb.nets.nets[p.net_name].padstack_instances:
            if not v.is_pin and math.hypot(v.position[0] - cx, v.position[1] - cy) < w / 2:
                return "smd_via_in_pad"
    except Exception:
        pass
    return "smd"
