# MCP tools changed by 035 (3.0.0)

| Tool | Change | Safety / flag |
|---|---|---|
| `isim_review` | full review always returns `html` (report path); `html` arg only matters for partial checks; no verdict / stop_md; description: "send the report to the user" | read |
| `isim_cut_preview` | `image` = FINAL cut region; `detail` + `zooms` = diagnostic | read |
| `isim_confirm_content` | GATE A = the one approval: refused without current review + report + error-free preview for the same settings; records `review.approval`; new optional `user_words` | state write; `user_confirmed_content` |
| `isim_cut` | refused without approval of the current review; result `next` | copy |
| `isim_check_ends` | result `next` = settings form | read |
| `isim_status` | Review column: not reviewed / out of date / no report / report ready / approved | read |
| `design_review` | no verdict text | read |
| `isim_review_decide` | REMOVED | — |
| `isim_review_override` | REMOVED (flag `user_approved_review_override` gone) | — |
| `design_review_decide` | REMOVED | — |

Refusal messages (server, Vietnamese as today):
- no review → "chưa review layout: chạy isim_review"
- out of date → "review đã cũ (<diffs>): chạy isim_review lại"
- no report → "chưa có file review HTML: chạy isim_review lại"
- no preview → "chưa có vùng cut dự tính: chạy isim_cut_preview"
- cut without approval → "người dùng chưa đồng ý sau khi đọc review: gửi report + vùng cut, hỏi, rồi isim_confirm_content"

CLI: `isim --op=review_decide|review_override` and `review-decide` removed (exit 2 unknown op).
