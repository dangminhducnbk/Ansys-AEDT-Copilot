# Contracts: 036

## interface_sim.netlist.parse(path) -> dict
- `path`: existing file. Format detected from content: first non-empty line `PROTEL NETLIST 2.0` or `[` → Protel;
  any line starting `$PACKAGES` / `$NETS` → Telesis. Else `CopilotInputError("netlist", "Protel 2.0 (Altium) or
  Allegro / Telesis netlist", <first line>)`.
- Returns the netlist.json shape (data-model.md). Never writes the input.

## interface_sim.request.start(..., netlist="") -> {request_id, folder, netlist?}
- `netlist` optional; parsed and saved; result `netlist = {path, format, design, components, nets, warnings}`.

## interface_sim.content.compare(facts, sch, patterns=()) -> {diffs, board_only, renamed}
- Pure. Rules D4 in plan.md. `diff(facts, sch)` keeps its signature (= compare diffs).

## interface_sim.answer.build(request_id, name) -> {answer_md, answer_image} | {answer_md: None, reason}
- Pure on files (state, review.json, preview.json). Text per plan D2.

## review_checks._verdict.channel_findings(ch) -> {not_ok, by_check, failed_checks, incomplete}
## review_checks._verdict.findings_md(name, f) -> str  ("**name**: NOT OK n (check n, ...)")

## MCP
| Tool | Change |
|---|---|
| `isim_start` | + `netlist: str = ""` |
| `isim_review` | `counts = {"NOT OK": n}`, `by_check`; + `answer_md` / `answer_image` when available |
| `isim_cut_preview` | + `answer_md` / `answer_image` |
| `isim_trace` | `schematic_diffs` pin-based; + `schematic_info` |
| `design_review` | items `status`; `findings.not_ok` |
| `review_rules` | rows field `not_ok_when` (was `severity`) |
