# Contracts: MCP tools `isim_*` (mcp_server/server.py)

Format: `specs/CONTRACTS.md`. All tools: thin (validate args, check gate, call CLI `python -m aedt_copilot isim-*`
in a subprocess with `aedt_env.child_env()`), return dict; refusal = `{"ok": false, "refused": "<gate / reason>"}`;
long work returns `{"task_id"}` (read with existing `task_result`). Errors from the package come back as
`{"ok": false, "error": "<CopilotInputError message>"}`. No existing tool changes.

| Tool | Inputs (type, rule) | Gate / precondition | Output |
|---|---|---|---|
| `isim_start(workspace, board="", cell="", stackup="", schematic="", bom="", interfaces="")` | paths exist; `schematic` = `;`-separated PDFs; `interfaces` = `;`-separated names (optional) | none | `{request_id, folder, schematic_status}` |
| `isim_bom(request_id, bom="")` | BOM path (else from request) | request exists | `{rows, columns_map, unmapped_columns, bom_json}` |
| `isim_schematic_status(request_id)` | — | request exists | `{exists, up_to_date, path, sources}` |
| `isim_save_schematic(request_id, markdown)` | markdown with required sections | request exists | `{path, components, nets, unreadable, warnings}` |
| `isim_trace(request_id, name, refdes="", nets="")` | at least one of refdes / nets; name rules | request exists | `{content proposal, end types (pre-check), schematic_diffs, structural settings, warnings, content_md}` |
| `isim_confirm_content(request_id, name, content, user_confirmed_content=false)` | `content` JSON (data-model) | GATE A: flag true | `{step: content_agreed, content_md}` |
| `isim_cut(request_id, name)` | — | step == `content_agreed`; not busy | `{task_id}` → `{stage1}` |
| `isim_check_ends(request_id, name)` | — | step == `cut` | `{ends, ends_md, settings_proposal, settings_md}` |
| `isim_validate_settings(request_id, name, values)` | `values` JSON `{key: value}`, `handling` optional | step == `ends_checked` | `{valid, errors[], table_md}` |
| `isim_apply(request_id, name, values, handling="", user_agreed_settings=false)` | as validate | GATE B: flag true AND valid AND step == `ends_checked` | `{task_id}` → `{result, self_check}` |
| `isim_status(request_id="")` | "" = latest request | — | `{interfaces[{name, step, open_questions, warnings}], table_md}` |
| `isim_merge(request_id, names="", port=0, user_approved_merge=false)` | names subset of `applied` | GATE C: flag true; workspace not locked unless `port` | `{task_id}` → `{merge}` |
| `isim_run(request_id, server, port=17878, sim_dir="", sim_dir_server="", designs="", mode="service", aedt_port=50000, client_port=18050, user_requested_run=false)` | server host; ports 1..65535; mode `service` (sim_dir optional, empty = upload; sim_dir_server required) or `grpc` (sim_dir required) | GATE D: flag true; ≥ 1 merged design | `{task_id, run_id, folder}` |
| `isim_run_status(request_id, run_id="")` | — | — | `{designs[...], table_md}` |

New MCP prompt `interface-sim` (`prompts/interface-sim.md`): starts the process (`get_guide("interface_sim")` first).
