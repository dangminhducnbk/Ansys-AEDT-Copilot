"""Danh mục tool (contract: specs/020-rename-catalog-workflows/contracts/catalog.md). Mỗi tool MCP của server = một mục.

safety = mức cao nhất tool có thể chạm tới:
  read      - không đổi design / board của người dùng (có thể ghi báo cáo vào thư mục của tool)
  copy      - tạo design / file MỚI (bản copy, kết quả cắt, thư mục workflow cá nhân); file đã cho không đổi
  original  - sửa file đã cho (chỉ khi `condition`), cần cờ `gate`
  workspace - sửa project / workspace AEDT của người dùng (thêm design), cần cờ `gate`
  remote    - chạy trên máy khác, cần cờ `gate`
kind = tool (dùng được trong mọi workflow) | process (bước của một quy trình có sẵn, chỉ chạy trong quy trình đó).
Test giữ danh mục khớp với các hàm @mcp.tool của server và cờ gate có thật trong chữ ký tool.
"""
from ..core.errors import CopilotInputError

SAFETY = ("read", "copy", "original", "workspace", "remote")
KINDS = ("tool", "process")
GATED = ("original", "workspace", "remote")


def _u(name, group, kind, safety, summary, inputs, outputs, gate=None, condition=None):
    return {"name": name, "group": group, "kind": kind, "summary": summary, "inputs": list(inputs),
            "outputs": list(outputs), "safety": safety, "gate": gate, "condition": condition}


TOOLS = [
    # ---- help
    _u("about", "help", "tool", "read", "What the tool can do: version, processes, prompts, guides", [], ["JSON"]),
    _u("get_guide", "help", "tool", "read", "Read a guide (rules of a process / tool)", ["topic"], ["guide text"]),
    _u("show_defaults", "help", "tool", "read", "Team defaults (templates/autocut_template.csv) + machine config",
       [], ["defaults"]),
    _u("task_result", "help", "tool", "read", "Result of a tool that returned {pending, task_id}", ["task_id"],
       ["result"]),
    # ---- catalog
    _u("list_tools", "catalog", "tool", "read", "List tools (filter by group / kind / safety)",
       ["group", "kind", "safety"], ["tool table"]),
    _u("list_workflows", "catalog", "tool", "read", "List workflows (team + personal) with status",
       [], ["workflow table"]),
    _u("get_workflow", "catalog", "tool", "read", "Read one workflow (steps, checkpoints, body)", ["name", "source"],
       ["workflow"]),
    _u("save_workflow", "catalog", "tool", "copy", "Save a workflow to the PERSONAL folder (never the team folder)",
       ["name", "markdown"], ["workflow file"], condition="overwrite only with overwrite=true"),
    # ---- board (read)
    _u("inspect_board", "board", "tool", "read", "Board summary: designs, layers, nets, big components",
       ["board .aedt/.aedb"], ["summary"]),
    _u("design_trace", "board", "tool", "read", "Trace a channel: nets, diff groups, series R/C/L, end types",
       ["board .aedb", "refdes", "nets"], ["trace JSON"]),
    # ---- review
    _u("design_review", "review", "tool", "read", "Measure review checks (reference, stubs, vias, routing) as data",
       ["board / design", "channels", "checks"], ["measurements", "OK / NOT OK per item", "summary_md",
                                                  "review record + counts per channel"]),
    _u("review_rules", "review", "tool", "read",
       "Layout review rules: list, read one rule's steering, enable / disable a personal rule's code",
       ["op", "rule_id"], ["rules list / steering text"], gate="user_approved_personal_code", condition="op=enable"),
    _u("review_stackup_table", "review", "tool", "read",
       "Stackup width / gap table per layer for review rule 6 (get / template / save after the user confirmed)",
       ["board .aedb", "op", "table (from the fab stackup PDF / Excel)"], ["stackup table JSON"],
       gate="user_confirmed_table", condition="op=save"),
    _u("layout_snapshot", "review", "tool", "read", "Read a board once into a cached layout snapshot (build / status / list)",
       ["board .aedb", "nets or scope=board"], ["snapshot folder", "snapshot.json report"]),
    # ---- cut
    _u("design_cutout", "cut", "tool", "copy", "Cut one channel from a COPY of the board into a new design",
       ["board .aedb", "comp_a", "comp_b", "nets", "series"], ["design .aedb", "stage1.json", "report"]),
    _u("design_cleanup", "cut", "tool", "original", "GND cleanup of a cut design (planes, shields, far GND vias)",
       ["design .aedb", "ends", "nets"], ["design .aedb", "report"], gate="user_approved_in_place",
       condition="in_place=true"),
    # ---- design (atomic, 007 + 008)
    _u("design_read", "design", "tool", "read", "Read setups / sweeps, airbox, ports, solder balls",
       ["design .aedb"], ["snapshot"]),
    _u("design_setup", "design", "tool", "original", "Create / replace HFSS setup + sweep",
       ["design .aedb", "values"], ["design .aedb", "report"], gate="user_approved_in_place",
       condition="in_place=true"),
    _u("design_sweep", "design", "tool", "original", "Replace the sweep of a setup",
       ["design .aedb", "values"], ["design .aedb", "report"], gate="user_approved_in_place",
       condition="in_place=true"),
    _u("design_airbox", "design", "tool", "original", "Set airbox / open region / operating freq",
       ["design .aedb", "values"], ["design .aedb", "report"], gate="user_approved_in_place",
       condition="in_place=true"),
    _u("design_ports", "design", "tool", "original", "Coax ports <refdes>.<pin>.<net>",
       ["design .aedb", "refdes", "nets"], ["design .aedb", "report"], gate="user_approved_in_place",
       condition="in_place=true"),
    _u("design_solder_ball", "design", "tool", "original", "Solder balls on components",
       ["design .aedb", "refdes", "values"], ["design .aedb", "report"], gate="user_approved_in_place",
       condition="in_place=true"),
    _u("design_end_check", "design", "tool", "read", "Measure ends: type, pads, GND near signal, unusual cases",
       ["design .aedb", "refdes", "nets"], ["ends", "ends_md"]),
    _u("design_check", "design", "tool", "read", "Self-check: ends present, ports, setup / sweep, airbox",
       ["design .aedb", "ends", "nets", "values"], ["ok", "mismatches"]),
    _u("finish_in_aedt", "design", "tool", "copy", "Open a cut result in AEDT, highlight + colours, save",
       ["result .aedb", "port"], ["saved result"], condition="writes the given cut RESULT, never a source board"),
    # ---- merge
    _u("design_merge", "merge", "tool", "workspace", "Merge designs into a workspace .aedt (backup first, _v2)",
       ["workspace .aedt", "designs", "port"], ["merge result"], gate="user_approved_merge"),
    # ---- layout edit
    _u("layout_region", "layout", "tool", "read", "Read an area: polygons, traces, vias, PNG per layer",
       ["board .aedb", "box"], ["region JSON", "PNG"]),
    _u("layout_edit", "layout", "tool", "copy", "Apply a layout plan (copper, voids, traces, vias, deletes) on a COPY",
       ["plan"], ["design .aedb", "changes.md"]),
    # ---- PI-DC (solved SIwave folder, works in place, never saves)
    _u("pidc_export", "pidc", "tool", "read", "Export SIwave DC report images (6x)", ["SIwave folder"],
       ["raw images"]),
    _u("pidc_current_density", "pidc", "tool", "read", "Current density per power net x layer",
       ["SIwave folder"], ["CD images", "table"]),
    _u("pidc_via_current", "pidc", "tool", "read", "Via current vs IPC capacity", ["SIwave folder"],
       ["VIA images", "table"]),
    _u("pidc_voltage_distribution", "pidc", "tool", "read", "All rails voltage overlay, load Vmin, VRM",
       ["SIwave folder"], ["VLT image", "table"]),
    _u("pidc_power_tree", "pidc", "tool", "read", "SIwave DC power tree + Pass/Fail per load",
       ["SIwave folder"], ["POWER_TREE image", "table"]),
    _u("pidc_report", "pidc", "tool", "read", "PI-DC HTML / MD / JSON report", ["SIwave folder"], ["report"]),
    # ---- process: interface simulation (guide interface_sim)
    _u("isim_start", "interface-sim", "process", "read", "Start a request for a workspace (+ schematic netlist)",
       ["workspace", "board", "netlist"], ["request", "netlist.json"]),
    _u("isim_bom", "interface-sim", "process", "read", "Read the BOM", ["request_id", "bom"], ["bom.json"]),
    _u("isim_schematic_status", "interface-sim", "process", "read", "Is schematic.md present / current",
       ["request_id"], ["status"]),
    _u("isim_save_schematic", "interface-sim", "process", "read", "Save schematic.md written by the agent",
       ["request_id", "markdown"], ["schematic.md"]),
    _u("isim_trace", "interface-sim", "process", "read", "Propose interface content", ["request_id", "refdes", "nets"],
       ["content proposal"]),
    _u("isim_previous", "interface-sim", "process", "read", "Earlier runs of an interface", ["name", "workspace"],
       ["runs"]),
    _u("isim_recut", "interface-sim", "process", "read", "Re-cut from earlier settings: differences only",
       ["request_id", "name", "source"], ["diffs"]),
    _u("isim_confirm_content", "interface-sim", "process", "read",
       "GATE A = the user's one approval after reading the review report + seeing the cut area",
       ["request_id", "name", "content", "user_words"], ["user_settings.json (content, review.approval)"],
       gate="user_confirmed_content"),
    _u("isim_review", "interface-sim", "process", "read",
       "MANDATORY layout review right after isim_trace (reuses a valid record); always writes the HTML report",
       ["request_id", "name", "checks", "nets"], ["review.json", "review record", "HTML report", "counts", "gate"]),
    _u("isim_cut_form", "interface-sim", "process", "read", "Gate A cut settings form (tab per interface, end factor per end)",
       ["request_id"], ["form"]),
    _u("isim_cut_preview", "interface-sim", "process", "read", "Cut preview before cutting: per-end table + cut-region image (board read only)",
       ["request_id", "name", "values", "end_factors"], ["preview table", "images", "preview.json"]),
    _u("isim_cut", "interface-sim", "process", "copy", "Cut the interface on a COPY of the board",
       ["request_id", "name"], ["stage1 design"]),
    _u("isim_check_ends", "interface-sim", "process", "read", "Measure ends + settings table",
       ["request_id", "name"], ["ends", "settings table"]),
    _u("isim_validate_settings", "interface-sim", "process", "read", "Validate a settings table",
       ["request_id", "name", "values"], ["validation"]),
    _u("isim_settings_form", "interface-sim", "process", "read", "Full settings form (tab per interface)",
       ["request_id"], ["form"]),
    _u("isim_validate_form", "interface-sim", "process", "read", "Validate a submitted form",
       ["request_id", "entries"], ["validation"]),
    _u("isim_apply", "interface-sim", "process", "copy", "Apply agreed settings on a copy of the cut (GATE B); no-GND end needs user_approved_gnd",
       ["request_id", "name", "values"], ["final design"], gate="user_agreed_settings"),
    _u("isim_status", "interface-sim", "process", "read", "State of every interface", ["request_id"], ["table"]),
    _u("isim_merge", "interface-sim", "process", "workspace", "Merge applied interfaces into the workspace (GATE C)",
       ["request_id", "names"], ["merge result"], gate="user_approved_merge"),
    _u("isim_run", "interface-sim", "process", "remote", "Solve merged designs on a server (GATE D)",
       ["request_id", "server", "sim_dir"], ["run"], gate="user_requested_run"),
    _u("isim_run_status", "interface-sim", "process", "read", "Progress of a remote run", ["request_id", "run_id"],
       ["status"]),
    # 038: fixed process - config page, check (Q2), one go (cut + build + merge into a NEW project of the request)
    _u("isim_config", "interface-sim", "process", "copy", "Write the config page (config.html) of the request: review, "
       "cut regions, layers, end pads; M1", ["request_id"], ["config.html", "answer_md"]),
    _u("isim_config_check", "interface-sim", "process", "copy", "Read + validate the saved config page; channel "
       "folders + previews; M2 or Q2", ["request_id"], ["previews", "answer_md"]),
    _u("isim_go", "interface-sim", "process", "copy", "After the user's go on Q2: cut + end check + build every "
       "channel and merge into a new project of the request folder; M3", ["request_id", "user_words"],
       ["channel folders", "merged project", "answer_md"], gate="user_approved_cut"),
    # 039: review question (Q0) before the config page
    _u("isim_layout_review", "interface-sim", "process", "copy", "Review of every channel of the request (HTML "
       "reports); 5.6.0+: the request page (review with NOT OK points to resolve + settings, config.html), M0p; "
       "5.2-5.5: M0 table + Q0 'review OK, go on to config?'", ["request_id"], ["channels", "config.html",
                                                                              "answer_md"]),
    _u("isim_review_answer", "interface-sim", "process", "copy", "The user's answer to Q0: no -> request stopped "
       "(M0x); yes -> config page (M1)", ["request_id", "accepted", "user_words"], ["config.html", "answer_md"],
       gate="user_answered_review"),
]


# 010: contract của từng tool (Principle VII); test kiểm tra file có và nêu tên tool trong backtick.
_C003, _C004 = "specs/003-interface-simulation/contracts/mcp-tools.md", "specs/004-recut-previous-settings/contracts/mcp-tools.md"
_C005, _C007 = "specs/005-settings-form-tabs/contracts/mcp-tools.md", "specs/007-atomic-design-tools/contracts/mcp-tools.md"
_C020, _C020T = "specs/020-rename-catalog-workflows/contracts/catalog.md", "specs/020-rename-catalog-workflows/contracts/tools.md"
_C011 = "specs/011-review-measure/contracts/mcp-tools.md"
_C022 = "specs/022-cut-keeps-end-gnd/contracts/cut-preview.md"
_C023 = "specs/023-layout-snapshot/contracts/mcp-tools.md"
_C035 = "specs/035-review-approval-gate/contracts/mcp-tools.md"
CONTRACTS = {
    **{n: _C020T for n in ("about", "show_defaults", "inspect_board", "finish_in_aedt", "layout_region",
                          "layout_edit", "pidc_export", "pidc_current_density", "pidc_via_current",
                          "pidc_voltage_distribution", "pidc_power_tree", "pidc_report")},
    **{n: _C003 for n in ("get_guide", "task_result", "isim_start", "isim_bom", "isim_schematic_status",
                          "isim_save_schematic", "isim_trace", "isim_confirm_content", "isim_cut", "isim_check_ends",
                          "isim_validate_settings", "isim_apply", "isim_status", "isim_merge", "isim_run",
                          "isim_run_status")},
    **{n: _C004 for n in ("isim_previous", "isim_recut")},
    **{n: _C035 for n in ("design_review", "isim_review", "isim_confirm_content", "isim_cut", "isim_check_ends",
                          "isim_cut_preview", "isim_status")},
    **{n: _C005 for n in ("isim_settings_form", "isim_validate_form")},
    **{n: _C022 for n in ("isim_cut_form", "isim_cut_preview")},
    "layout_snapshot": _C023,
    "review_stackup_table": "specs/030-review-rules-si/contracts/review-rules.md",
    "review_rules": "specs/031-review-rule-files/contracts/review-rules.md",
    **{n: _C007 for n in ("design_read", "design_setup", "design_sweep", "design_airbox", "design_ports",
                          "design_solder_ball")},
    **{n: _C020 for n in ("list_tools", "list_workflows", "get_workflow", "save_workflow")},
    **{n: _C020T for n in ("design_trace", "design_cutout", "design_cleanup", "design_end_check", "design_check",
                           "design_merge")},
    **{n: "specs/038-cut-config-html/contracts/config-flow.md" for n in ("isim_config", "isim_config_check",
                                                                          "isim_go")},
    "isim_layout_review": "specs/045-review-resolve-page/contracts/review-page.md",
    "isim_review_answer": "specs/039-review-before-config/contracts/review-step.md",
}
for _e in TOOLS:
    _e["contract"] = CONTRACTS.get(_e["name"])

# quy trình có sẵn -> guide của nó: tool kind 'process' chỉ dùng trong workflow có guide này
PROCESS_GUIDES = {"interface-sim": "interface_sim"}


def by_name():
    return {u["name"]: u for u in TOOLS}


def _check(name, value, allowed):
    if value in (None, ""):
        return ""
    if value not in allowed:
        raise CopilotInputError(name, "one of " + ", ".join(allowed), value)
    return value


def tools(group="", kind="", safety=""):
    groups = sorted({u["group"] for u in TOOLS})
    group, kind, safety = _check("group", group, groups), _check("kind", kind, KINDS), \
        _check("safety", safety, SAFETY)
    return [u for u in TOOLS if (not group or u["group"] == group) and (not kind or u["kind"] == kind)
            and (not safety or u["safety"] == safety)]


def safety_text(u):
    s = u["safety"]
    if u.get("gate"):
        s += f" ({u['gate']})"
    if u.get("condition"):
        s += f" when {u['condition']}" if u["safety"] in GATED else f"; {u['condition']}"
    return s


def catalog_md(entries=None):
    entries = TOOLS if entries is None else entries
    out, group = [], None
    for u in entries:
        if u["group"] != group:
            group = u["group"]
            out += ["", f"### {group}", "", "| Tool | Kind | Safety (gate) | What it does | Inputs → Outputs |",
                    "|---|---|---|---|---|"]
        out.append(f"| `{u['name']}` | {u['kind']} | {safety_text(u)} | {u['summary']} | "
                   f"{', '.join(u['inputs']) or '-'} → {', '.join(u['outputs']) or '-'} |")
    return "\n".join(out).strip() + "\n"
