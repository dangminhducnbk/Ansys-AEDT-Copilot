# Data model: 035

## user_settings.json → `interfaces.<name>.review`

| Field | Type | Meaning |
|---|---|---|
| measured_at | str | review time (025) |
| review_json | str | `<interface>/review.json` |
| html | str | report path (NEW, always for a full review) |
| approval | object / null | NEW, set by GATE A |
| decisions, override | list / object | 2.12.0 history only; never read as approval |

`approval`:

| Field | Type | Meaning |
|---|---|---|
| measured_at | str | must equal `review.measured_at` to count |
| time | str | approval time |
| report | str | HTML path shown to the engineer |
| review_json | str | review data |
| counts | {HIGH, MEDIUM, INFO} | findings at approval |
| incomplete | bool | review had a failed check |
| failed_checks | list | check + error |
| preview_json | str | preview the engineer saw |
| user_words | str | engineer's words (optional) |

## Review gate status (state machine)

`not_reviewed` → (isim_review) → `ready` → (GATE A) → `approved` → (cut allowed)
Any of board / ends / nets / checks / thresholds change → `out_of_date` → (isim_review) → `ready`.
`ready` with report file missing → `no_report`.

## preview.json
`image` = final cut region (`cut_region.png`); NEW `detail` = `cut_detail.png`; `zooms` unchanged (detail views).
