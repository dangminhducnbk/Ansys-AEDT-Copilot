"""Đổi kết quả đo (mét, tuple) sang dữ liệu JSON theo mm + bảng tóm tắt điểm nghi vấn (feature 011)."""
MM = 1e-3


def _mm(v):
    return None if v is None else round(float(v) / MM, 4)


def item(f):
    """finding của review.py -> item (contract review-checks.md). status = OK / NOT OK theo ngưỡng của luật (036)."""
    out = {"id": f.get("id"), "check": f["check"], "status": f["status"], "net": f["net"],
           "layer": f.get("layer"), "ref": f.get("ref", ""), "value": f.get("value"),
           "x_mm": _mm(f["x"]), "y_mm": _mm(f["y"])}
    if f.get("len_mm") is not None:
        out["len_mm"] = round(float(f["len_mm"]), 4)
    if f.get("other_net"):
        out["other_net"] = f["other_net"]
    if f.get("used"):
        out["used_layers"] = list(f["used"])
    if f.get("point"):
        out["point"] = f["point"]
    return out


def via_row(r):
    g = r.get("gnd") or None
    return {"net": r["net"], "x_mm": _mm(r["x"]), "y_mm": _mm(r["y"]), "kind": r["kind"], "size": r["size"],
            "defs": list(r["defs"]), "n_vias": r["n_vias"], "range": r["range"], "used": list(r["used"] or []),
            "backdrill": r["backdrill"], "stub_mm": round(r["stub_mm"], 4), "barrel_mm": round(r["barrel_mm"], 4),
            "gnd_d_mm": round(g["d_mm"], 4) if g else None,
            "gnd_xy_mm": [_mm(g["x"]), _mm(g["y"])] if g else None}


def point(p):
    return {"id": p["id"], "status": "NOT OK", "net": p["net"], "x_mm": _mm(p["x"]),
            "y_mm": _mm(p["y"]), "layer": p["main"].get("layer"),
            "issues": list(dict.fromkeys(f"{f['check']}: {f['value']}" for f in p["items"]))}  # 012: mỗi dòng một lần


def _cell(v):
    return str(v).replace("|", "/")


def summary_md(ch):
    """Bảng điểm NOT OK + lỗi check của một channel (036: không có mức nặng nhẹ)."""
    lines = [f"### {ch['name']} ({ch.get('comp_a')} - {ch.get('comp_b')}, {len(ch.get('nets') or [])} nets)"]
    if ch.get("error"):
        return "\n".join(lines + ["", f"ERROR: {ch['error']}"])
    errs = [f"- {k}: {v['error']}" for k, v in ch["checks"].items() if v.get("error")]
    pts = ch.get("points") or []
    if not pts:
        lines += ["", "No NOT OK point."]
    else:
        lines += ["", "| Point | Status | Net | Layer | x, y mm | Evidence |", "|---|---|---|---|---|---|"]
        for p in pts:
            lines.append(f"| {p['id']} | NOT OK | {p['net']} | {_cell(p['layer'])} | "
                         f"{p['x_mm']}, {p['y_mm']} | {_cell('; '.join(p['issues']))} |")
    if errs:
        lines += ["", "Check errors:"] + errs
    return "\n".join(lines)
