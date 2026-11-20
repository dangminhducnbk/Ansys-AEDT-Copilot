"""Bảng markdown cho chat / file .md (content, ends, settings, status, run)."""


def cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:g}"
    if isinstance(v, (list, tuple)):
        return ", ".join(cell(x) for x in v)
    return str(v).replace("|", "\\|").replace("\n", " ")


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(x) for x in r) + " |")
    return "\n".join(out)


def mm(v_m, nd=3):
    """mét -> chuỗi mm."""
    return None if v_m is None else round(v_m * 1e3, nd)
