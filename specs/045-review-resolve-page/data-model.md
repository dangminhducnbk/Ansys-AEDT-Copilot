# Data model — 045

## Request (`_work/request.json`)
+ `review_page: true` (045, set by `isim_start` from 5.6.0). Requests without it keep 038 / 039 behaviour.

## Page data (`cfg-data`, 038 + 045)
`data.review = {channel: ReviewData}` (only on 045 pages); `data.kind = "review"`.

ReviewData:
| key | type | from |
|---|---|---|
| measured_at | str | review.json |
| review_html | str (path) | review.json `html` |
| points | [Point] | review.json channel points with status NOT OK (report order) |
| sections | {section title: intro html} | report HTML |
| topo | html | report HTML "Signal routing per pair" (class `xs` → `xs2`) |
| stackup | [{name, type, material, thickness_um}] | config data `stackup` (live read) |

Point: `{id, net, x, y, act (layer), inv [layers], items [Item], rep [ReportRow]}`
Item: `{id, check, fam (ref|via|rt|ts|stk), value, net, layer, ref, used [layers], issue, rec}`
ReportRow: `{rid, sec, desc (html), pic (html)}`

Channel config data gains `stackup` (same rows as above).

## Page state (`cfg-state`, 038 + 045)
`state.review = {channel: {measured_at: str, resolved: {point id: Resolution}}}`
Resolution: `{check: str, net: str, x: float, y: float, time: str, note: str, carried?: true}`

Rules: a point counts as resolved only when `state.review[ch].measured_at == data.review[ch].measured_at` and its id
is in `resolved`. Channel with 0 NOT OK points = resolved.

## Record (`_work/resolutions.json`, written by isim_config_check)
`{time, saved_page, channels: {name: {measured_at, points, resolved [ {id, check, net, x, y, time, note} ]}}}`
