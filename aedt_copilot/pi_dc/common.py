"""Dùng chung cho PI-DC: thông số (templates/pidc_template.csv), đọc .siw, thư mục kết quả DC, đường dẫn output."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ..core.config import coerce, template_path, template_rows

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path(template_path("pidc"))
GND_RE = re.compile(r"(^|_)(A|D|P|S)?GND|VSS|(^|_)GROUND", re.I)


def params() -> dict:
    """pidc.* -> {key_without_prefix: value} (num -> float/int, text -> str)."""
    return {r["key"].split(".", 1)[1]: coerce(r["default"], r["type"]) for r in template_rows(TEMPLATE)}


def spec(P: dict, layer: str, outer: set) -> float:
    return float(P["cd_outer_A_mm2"] if layer in outer else P["cd_inner_A_mm2"])


# ------------------------------------------------------------------ project
def find_siw(folder: Path) -> Path:
    sws = sorted(p for p in Path(folder).glob("*.siw") if p.with_suffix(".siwaveresults").is_dir())
    if not sws:
        raise RuntimeError(f"Không thấy .siw có thư mục .siwaveresults trong {folder}")
    if len(sws) > 1:
        raise RuntimeError(f"Có nhiều .siw đã giải trong {folder}: {[p.name for p in sws]}. Chỉ rõ --siw.")
    return sws[0]


def parse_siw(siw: Path) -> dict:
    """Net nguồn (bỏ GND), lớp kim loại trên -> dưới, tên DC sim (DC_SIM_NAME khác rỗng)."""
    t = Path(siw).read_text(encoding="latin-1")
    m = re.search(r"B_PWR_GND_NETS_MOD_GEN\s*\n\s*(\d+)\s*\n(.*?)E_PWR_GND_NETS_MOD_GEN", t, re.S)
    pg = re.findall(r'"([^"]+)"', m.group(2)) if m else []
    lm = re.search(r"B_LAYERS\s*\n(.*?)E_LAYERS", t, re.S)
    metals = re.findall(r"^\s*\d+\s+`([^`]+)`\s+METAL", lm.group(1), re.M) if lm else []
    sims = [s for s in re.findall(r'^\s*DC_SIM_NAME\s+"([^"]*)"', t, re.M) if s]
    return {"pg_nets": pg, "power_nets": [n for n in pg if not GND_RE.search(n)], "metal_layers": metals,
            "dc_sims": sims}


def check_nets(siw, info: dict):
    """016: .siw không có danh sách net nguồn / GND (hoặc chỉ GND) -> dừng, báo rõ (trước đây PASS với 0 cặp)."""
    if not info["pg_nets"]:
        raise RuntimeError(f"{siw}: no power/ground net list (B_PWR_GND_NETS_MOD_GEN is empty). In SIwave mark the power "
                           "and ground nets (Net Manager / Power-Ground nets), save the .siw, re-run the DC sim, then retry.")
    if not info["power_nets"]:
        raise RuntimeError(f"{siw}: the power/ground net list has only ground nets {info['pg_nets']}. Mark the power nets "
                           "in SIwave, save the .siw, re-run the DC sim, then retry.")


def sim_temperature(run_dir) -> tuple:
    """016: nhiệt độ mô phỏng DC = GlobalTemperature trong <run>/<run>.cfg -> (°C, đường dẫn cfg). Thiếu -> lỗi rõ."""
    run_dir = Path(run_dir)
    cfg = run_dir / f"{run_dir.name}.cfg"
    if not cfg.is_file():
        raise RuntimeError(f"Simulation temperature not found: no {cfg} (needed for via dT = T_sim - via_base_temp_C)")
    m = re.search(r"^\s*GlobalTemperature\s+(\S+)", cfg.read_text(encoding="latin-1"), re.M)
    try:
        return float(m.group(1)), cfg
    except (AttributeError, ValueError):
        raise RuntimeError(f"Simulation temperature not found: no 'GlobalTemperature <value>' in {cfg}") from None


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def find_run(siw: Path, sim: str) -> Path:
    """<project>.siwaveresults/NNNN_<sim, ký tự lạ -> _>/ (phải có .vcd)."""
    key = safe(sim)
    root = Path(siw).with_suffix(".siwaveresults")
    cands = sorted(p for p in root.glob("*_*") if p.is_dir() and p.name.split("_", 1)[1] == key)
    if not cands:
        raise RuntimeError(f"Không thấy thư mục kết quả của DC sim '{sim}' trong {root}")
    return cands[-1]


def siwave_exe(aedt_version: str | None = None) -> str:
    """siwave.exe của bản AEDT do aedt_env tìm (config aedt_root -> env -> registry -> quét). None = theo config.yaml."""
    from ..aedt_env import siwave_exe as _exe
    return _exe(aedt_version or None)


# ------------------------------------------------------------------ output folder
class Ctx:
    """Đường dẫn làm việc của một thư mục SIwave: <dir>/<output_folder>/{raw,results,images}."""

    def __init__(self, folder: str, siw: str | None = None, sim: str = ""):
        self.P = params()
        self.dir = Path(folder).resolve()
        self.siw = Path(siw).resolve() if siw else find_siw(self.dir)
        self.out = self.dir / str(self.P["output_folder"])
        self.raw = self.out / "raw"
        self.reports = self.raw / "reports"
        self.reports_vlt = self.raw / "reports_vlt"              # ảnh voltage xuất bổ sung (export voltage_only)
        self.results = self.out / "results"
        self.images = self.out / "images"
        self.info = parse_siw(self.siw)
        check_nets(self.siw, self.info)
        sims = self.info["dc_sims"]
        self.sim = sim or (sims[0] if len(sims) == 1 else "")
        if not self.sim:
            raise RuntimeError(f"Cần chỉ rõ tên DC sim. DC sim trong project: {sims}")
        if sims.count(self.sim) > 1:
            raise RuntimeError(f"Tên DC sim '{self.sim}' bị trùng (SIwave sẽ xuất run đầu tiên). Đổi tên trước.")
        self.run_dir = find_run(self.siw, self.sim)
        self.base = self.run_dir / self.run_dir.name            # <run>/<run>.vcd ...
        self.metals = self.info["metal_layers"]
        self.power = self.info["power_nets"]
        self.outer = {self.metals[0], self.metals[-1]}

    def mkdirs(self):
        for d in (self.out, self.raw, self.reports, self.results, self.images):
            d.mkdir(parents=True, exist_ok=True)

    def cur_png(self, job: str, kind: str, layer: str) -> Path | None:
        for root in (self.reports, self.reports_vlt):
            for lay in (layer.replace(" ", "_"), layer):
                p = root / job / "report_files" / f"{kind}_{lay}.png"
                if p.exists() and p.stat().st_size > 0:
                    return p
        return None

    def save_result(self, name: str, data: dict):
        self.results.mkdir(parents=True, exist_ok=True)
        (self.results / f"{name}.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")

    def load_result(self, name: str):
        p = self.results / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
