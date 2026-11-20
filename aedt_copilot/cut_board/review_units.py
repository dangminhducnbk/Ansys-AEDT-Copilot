"""2.11.2 (033 R10): đơn vị độ dài đổi được trong report review (mil / µm / mm, mặc định mil).

Mỗi độ dài trong HTML là một phần tử mang giá trị mét (`data-m`) + tiền tố (`data-k`); JS định dạng theo đơn vị đang
chọn (nhớ bằng localStorage trong try/catch). Không có JS: chữ sẵn ở mil. Diện tích (mm²), góc, %, tên via
`<pad>D<hole>` (mil) không đổi. Module thuần (không EDB).
"""
import re

MM = 1e-3
MIL = 0.0254 * MM
# đơn vị -> (hệ số từ mét, số lẻ, nhãn)
UNITS = {"mil": (1 / MIL, 1, "mil"), "um": (1e6, 0, "µm"), "mm": (1e3, 3, "mm")}
DEFAULT = "mil"


def fmt(m, unit=DEFAULT):
    f, nd, lab = UNITS[unit]
    return f"{float(m) * f:.{nd}f} {lab}"


def attrs(m, prefix=""):
    """Thuộc tính cho phần tử độ dài (HTML span hoặc SVG text)."""
    k = f' data-k="{prefix}"' if prefix else ""
    return f' class="ul" data-m="{float(m):.9g}"{k}'


def span(m, prefix=""):
    """<span> độ dài đổi được; chữ sẵn ở mil."""
    return f"<span{attrs(m, prefix)}>{prefix}{fmt(m)}</span>"


def num(m):
    """Số không kèm đơn vị (ô bảng; đơn vị ở tiêu đề cột qua unit_name())."""
    f, nd, _ = UNITS[DEFAULT]
    return f'<span class="ul" data-m="{float(m):.9g}" data-n="1">{float(m) * f:.{nd}f}</span>'


def unit_name():
    """Tên đơn vị đang chọn (vd. tiêu đề cột 'Total (mil)')."""
    return f"<span class='uu'>{UNITS[DEFAULT][2]}</span>"


_NUM = r"-?\d+(?:\.\d+)?"
_PAIR = re.compile(rf"\(({_NUM}), ({_NUM})\) mm(?![²\w])")
_RANGE = re.compile(rf"({_NUM}) ?[–-] ?({_NUM}) mm(?![²\w])")
_ONE = re.compile(rf"({_NUM}) mm(?: \({_NUM} mil\))?(?![²\w])")


def wrap(text):
    """Chữ (đã escape) -> độ dài 'x mm', 'x mm (y mil)', '(x, y) mm', 'a–b mm' thành span đổi được. mm² giữ nguyên."""
    s = _PAIR.sub(lambda m: f"({span(float(m.group(1)) * MM)}, {span(float(m.group(2)) * MM)})", text)
    s = _RANGE.sub(lambda m: f"{span(float(m.group(1)) * MM)} – {span(float(m.group(2)) * MM)}", s)
    # phần đã thành span có 'data-m=".."' + chữ mil -> không khớp lại (không còn ' mm')
    return _ONE.sub(lambda m: span(float(m.group(1)) * MM), s)


SWITCH_HTML = ("<div class='usw'><b>Units:</b> "
               + "".join(f"<button type='button' class='ub{' on' if u == DEFAULT else ''}' data-u='{u}'>{lab}</button>"
                         for u, (_, _, lab) in UNITS.items()) + "</div>")

CSS = (".usw{margin:6px 0}.ub{padding:2px 12px;border:1px solid #888;background:#fff;cursor:pointer;font-size:12px;"
       "margin-left:4px;border-radius:3px}.ub.on{background:#dce6f2;font-weight:bold}")

JS = """
(function(){const F={mil:[1/0.0000254,1,'mil'],um:[1e6,0,'\\u00b5m'],mm:[1e3,3,'mm']};
function set(u){if(!F[u])u='mil';const f=F[u];
 document.querySelectorAll('.ub').forEach(b=>b.classList.toggle('on',b.dataset.u===u));
 document.querySelectorAll('[data-m]').forEach(e=>{e.textContent=(e.dataset.k||'')+(+e.dataset.m*f[0]).toFixed(f[1])+(e.dataset.n?'':' '+f[2]);});
 document.querySelectorAll('.uu').forEach(e=>{e.textContent=f[2];});
 try{localStorage.setItem('aedt_copilot.unit',u)}catch(e){}}
document.querySelectorAll('.ub').forEach(b=>b.onclick=()=>set(b.dataset.u));
let u0='mil';try{u0=localStorage.getItem('aedt_copilot.unit')||'mil'}catch(e){}
set(u0);})();
"""
