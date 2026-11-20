# Contracts: MCP tools (025)

| Tool | Inputs | Safety / gate | Output | Refusals / errors |
|---|---|---|---|---|
| `isim_review(request_id, name, checks="", html=False, snapshot="auto", reuse=True, nets="")` | request + interface traced (any step; needs proposal or content) | read (writes `<iface>/review.json` or `review_partial.json`, a record under `reviews/`, `user_settings.json` decisions on reuse) | 2.2.0 measure output + `basis`, `verdict`, `gate`, `stop_md`, `review_json`, `record`, `reused_from` | snapshot not auto/off → refuse; interface not traced → input error |
| `isim_review_decide(request_id, name, decisions)` | decisions JSON list (as 011) | read (writes `user_settings.json`) | saved decisions + `verdict` + `gate` | no review.json → input error; unknown point / decision / severity change without reason → input error |
| `isim_review_override(request_id, name, reason, user_approved_review_override=False)` (NEW) | reason = the engineer's words | read (writes `user_settings.json`); gate `user_approved_review_override` | `{interface, override, gate}` | flag false → refuse; reason empty → refuse; no review / verdict not STOP / review out of date → input error |
| `isim_confirm_content(...)` (changed) | as 003 | gate `user_confirmed_content` | as before | + refuse when review gate not ok: `{refused, reason, review_gate}` |
| `isim_cut(request_id, name)` (changed) | as 003 | copy | as before | + refuse when review gate not ok |
| `design_review(...)` (changed) | as 011 / 023 | read (writes a record under `reviews/`) | + `review_file`, `channels[i].verdict`, `verdict_md` | as before |
| `design_review_decide(review_file, channel, decisions)` (NEW) | record path from `design_review`, channel name, decisions JSON list | read (writes only that record) | `{review_file, channel, decisions, verdict, verdict_final}` | file not a review record / channel unknown / decisions invalid → refuse / input error |

Gate refusal message (Vietnamese, from code): status + reason, HIGH points (id, issue, net, layer, x/y) or
out-of-date fields, and the ways forward: sửa board + `isim_review` lại; quyết định từng điểm
(`isim_review_decide`, có lý do); hoặc người dùng nói rõ "vẫn cut" + lý do → `isim_review_override`.

CLI: `isim --op=review|review_decide|review_override --args-file=`; `review-measure` (output + `review_file`);
`review-decide --file= --channel= --decisions-file=` (new).
