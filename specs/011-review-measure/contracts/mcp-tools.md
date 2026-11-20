# Contracts: MCP tools (011)

| Tool | Inputs | Safety | Output |
|---|---|---|---|
| `design_review(board, channels, checks="", cell="", html=False)` | board / cut design, channels `A-B:pattern; ...`, checks comma list (empty = all) | read | `review_checks.measure` output (+ `html` path when html=true, from `review_layout`'s report code) |
| `isim_review(request_id, name, checks="", html=False)` | request + agreed interface | read (writes `review.json` in the request) | measure output for the agreed nets |
| `isim_review_decide(request_id, name, decisions)` | decisions JSON list | read (writes `user_settings.json` of the request) | saved decisions |

CLI: `python -m aedt_copilot review-measure --board= --channels= [--checks=] [--cell=] [--html]`;
`isim --op=review|review_decide`. Long runs → `{pending, task_id}`.
