"""Guide (guides/*.md), prompt (prompts/*.md) và nội dung tool about cho MCP server. Chỉ đọc file."""
import glob
import os
import re

from .. import __version__, aedt_env
from .tasks import ROOT

GUIDES = os.path.join(ROOT, "guides")
PROMPTS = os.path.join(ROOT, "prompts")


def guides():
    """{tên: mô tả} - mô tả = dòng <!-- ... --> đầu file."""
    out = {}
    for p in sorted(glob.glob(os.path.join(GUIDES, "*.md"))):
        with open(p, encoding="utf-8") as f:
            first = f.readline().strip()
        out[os.path.splitext(os.path.basename(p))[0]] = first[4:-3].strip() if first.startswith("<!--") else ""
    return out


def guide(topic=""):
    gs = guides()
    if not topic:
        return {"guides": gs}
    t = topic.strip().lower().replace("-", "_").replace(".md", "")
    if t not in gs:
        return {"error": f"Không có guide '{topic}'", "guides": gs}
    with open(os.path.join(GUIDES, t + ".md"), encoding="utf-8") as f:
        return {"topic": t, "version": __version__, "content": f.read()}


def prompt_files():
    """{tên: mô tả} của prompts/*.md (front matter description:)."""
    out = {}
    for p in sorted(glob.glob(os.path.join(PROMPTS, "*.md"))):
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        m = re.match(r"---\s*\n(.*?)\n---\s*\n", txt, re.S)
        desc = re.search(r"description:\s*(.*)", m.group(1)).group(1).strip() if m else ""
        out[os.path.splitext(os.path.basename(p))[0]] = desc
    return out


def prompt_path(name):
    return os.path.join(PROMPTS, name + ".md")


def prompt_text(path, arguments=""):
    """Thân prompt (bỏ front matter), $ARGUMENTS thay bằng arguments. Đọc lại mỗi lần: sửa file có hiệu lực ngay."""
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", txt, flags=re.S)
    return body.replace("$ARGUMENTS", arguments or "(chưa có - hỏi người dùng)")


def about():
    return {"name": "Ansys AEDT Copilot", "version": __version__, "home": ROOT,
            "steps": ["Cut / simulate interfaces: interface simulation (guide interface_sim) - see 'interface_sim'",
                      "Anything else: list_workflows + list_tools (guide catalog)",
                      "finish_in_aedt -> open a cut / merged design in AEDT, signal red / GND blue (on request)",
                      "1.0.0: the channel Excel flow was removed (to finish an old Excel job: checkout tag v0.15.0)"],
            "pi_dc": ["Separate PI-DC report of a solved SIwave DC-IR folder (works in place, never saves) - guide pidc_workflow",
                      "pidc_export(folder) -> 6x SIwave DC report images into <folder>/Ansys AEDT Copilot/raw",
                      "pidc_current_density(folder) -> J_avg_max (0.5 mm window) per power net x layer, outstanding regions",
                      "pidc_via_current(folder) -> via current vs IPC capacity, circled via images",
                      "pidc_voltage_distribution(folder) -> one image, all power rails + all layers overlaid, load Vmin + VRM",
                      "pidc_report(folder) -> PIDC_report_<time>.html + report.md + summary.json + images/ (slide-ready)"],
            "layout_edit": ["Separate layout improvement on a COPY of an .aedb - guide layout_edit",
                            "layout_region(board, box) -> per-layer polygons/traces/vias + PNG of an area (read only)",
                            "layout_edit(plan) -> ops add_copper / carve / remove_copper / void / trace / via / delete in one EDB "
                            "session, automatic antipads + sliver cleanup, checks, before/after PNG, changes.md"],
            "interface_sim": ["Interface simulation (guide interface_sim, prompt interface-sim), no Excel:",
                              "isim_start(netlist=...) -> schematic netlist (Altium Protel 2.0 / Allegro) read by "
                              "code (4.0); without a netlist: schematic PDF + BOM read once into schematic.md",
                              "isim_trace -> nets / ends / series parts, board vs schematic compared by pins",
                              "channel answer (4.0): isim_review (HTML report) + isim_cut_preview (final cut region) "
                              "-> answer_md = cut area + review file + one question, pasted verbatim; the user's one "
                              "go = GATE A",
                              "isim_cut (copy of board) -> isim_check_ends -> settings table; user agrees (GATE B) -> isim_apply",
                              "isim_merge -> one design per interface in the user's workspace (GATE C)",
                              "isim_run -> copy to the server simulation folder, solve one by one (GATE D, on request)",
                              "re-cut 'như lần trước': isim_previous -> isim_start (new request) -> isim_recut "
                              "(only differences) -> same gates; all agreed values in user_settings.json",
                              "GATE B full form: isim_settings_form (tab per interface, all settings, Set default) -> "
                              "isim_validate_form -> user go -> isim_apply per interface",
                              "GATE A cut form: isim_cut_form (cut settings per interface) + isim_cut_preview (read-only "
                              "preview of the cut extent and images; end GND rule grows only a failing end until a GND "
                              "pin is fully inside)"],
            "design_tools": ["Atomic tools on ANY .aedb (guide design_tools, prompt design-tools), copy by default:",
                             "design_read -> setups / sweeps / airbox / ports / solder balls (read only)",
                             "design_setup, design_sweep, design_airbox -> simulation settings (template defaults + values)",
                             "design_ports -> coax ports <refdes>.<pin>.<net>; design_solder_ball -> solder balls",
                             "each: report (changes old -> new, skipped, read-back); in_place needs user_approved_in_place"],
            "catalog": ["Tool catalog (guide catalog, prompt catalog): every tool has a safety level, processes = workflows",
                        "list_tools -> every tool with group, kind, safety (read/copy/original/workspace/remote) + gate",
                        "list_workflows / get_workflow -> team workflows (repo workflows/) + personal workflows; "
                        "save_workflow (personal folder only, on request)",
                        "composable tools: design_trace, design_end_check, design_check (read), design_cutout (new design "
                        "from a board copy), design_cleanup (GND cleanup), design_merge (workspace, user_approved_merge)",
                        "example workflow cut-sweep-merge: trace -> cutout -> end check -> ports -> setup -> check -> merge"],
            "review_measure": ["Review as data (guide review_measure, workflow layout-review):",
                               "design_review(board, channels, checks) -> per check: reference (SOV / ref to other net / "
                               "loss of ref), trace_stubs, vias, routing; each item OK / NOT OK against its "
                               "threshold (4.0: no severity levels); chat summary, HTML on request",
                               "interface simulation (3.0): MANDATORY isim_review right after isim_trace, always with "
                               "the HTML report; the user reads it + the final cut area and gives ONE go (GATE A); "
                               "NOT OK counts never block or allow a cut by themselves",
                               "every review is stored as a record (Ansys AEDT Copilot/reviews/) with NOT OK counts per "
                               "channel; reused while board / nets unchanged",
                               "layout_snapshot(op=build|status|list) -> board read once into a cached snapshot; "
                               "reviews re-run in seconds with identical results",
                               "HTML report (2.5): summary per section (counts per channel), one table per category Index / Description / Picture (NOT OK rows), "
                               "pictures draw only the involved layers",
                               "2.6: HTML report and isim_cut_preview read the layout snapshot (preview extent = AEDT "
                               "extent cached per nets / settings / factor); issue text = labelled lines + Why / Fix",
                               "2.7: + pair skew, pair gap, coupling 3W, plane edge 3H, via count, width / gap vs "
                               "stackup table (review_stackup_table)",
                               "2.9: one file per rule - steering review_rules/<id>.md + code; review_rules(op=list|get) "
                               "reads one rule; personal rules (enable for code)",
                               "2.10: via clearance (antipad) is not loss of reference (other-net via = OK, data "
                               "via_clearance); one finding per stretch; one picture panel per reference plane"],
            "prompts": {k: v for k, v in prompt_files().items()}, "guides": guides(),
            "requires": "Windows, Ansys AEDT 2026 R1 (2025 R2 fallback), setup.bat run once",
            "aedt": aedt_env.info()}
