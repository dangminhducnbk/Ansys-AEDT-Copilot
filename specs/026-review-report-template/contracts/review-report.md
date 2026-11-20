# Contract: layout review report (feature 026)

Module `aedt_copilot/cut_board/review_report.py` (pure). Input = channels of `review.review()` (findings, points,
vias, lengths, `rows`), metres; output HTML in mm, English.

## section_of(check) -> str

Fixed: `reference` (Loss of reference, Ref to other net, SOV, Ref plane change), `trace_stub` (Trace stub), `via`
(Via stub, Nearest GND via), `routing` (none today). Other check name → key = the check name (own section).

## sections(chans) -> [{key, title, prefix}]

Fixed four in order, then unknown checks in first-seen order. Prefix of an unknown check = upper initials (≥ 3 chars).

## rows(chans) -> {section key: [row]}

Row = one abnormal point × one section, items = the point's HIGH / MEDIUM findings of that section.
`{index "<PREFIX>-<nn>", anchor, channel, ci, point, net, x, y, severity, items, img?, legend?, note?}`.
Order per section: severity (HIGH first), channel order, point order. `nn` 2 digits (3 when > 99).
Input check: `chans` list of dicts → else `CopilotInputError`.

## counts(chans) -> {section key: {channel: {HIGH, MEDIUM, INFO}}}

From `findings` (all severities). Channel with `error` → no counts, marked incomplete in the summary.

## danger(c) -> (worst, verdict)

c = {HIGH, MEDIUM, INFO} summed. HIGH → ("HIGH", "Dangerous — stop"); MEDIUM → ("MEDIUM", "Review needed");
INFO → ("INFO", "Information"); none → ("OK", "OK — no issue").

## row_layers(items, ref_layers, metal) -> (signals, planes, note)

| Check | signals | planes |
|---|---|---|
| SOV, Loss of reference | `layer` | `ref` split ", " |
| Ref to other net | `layer` | plane before ":" in `ref` |
| Trace stub | `layer` | `ref_layers(layer)` |
| Ref plane change | `used[0]`, `used[-1]` | `ref_layers` of both |
| Via stub, Nearest GND via | `used` | `ref_layers` of each |
| other / no layer known | `layer` if in `metal` | none; note "involved layers unknown — issue layer only" |

Union over items, ordered by `metal` (stack order); only names in `metal`.

## render(info, chans) -> str

Order: `<h1>` header (board, design, date, version, gate verdict per channel or "not recorded") → `#summary`
(table: Section | one column per channel | Worst | Verdict; section names link to `#sec-<key>`, first 8 row
indexes link to `#r-<index>`) → `#sec-<key>` per
section (lead line + table `Index | Description | Picture` or "No issue") → `#ref` Reference data (`<details>`).
No external resource. `info`: board, cell, date, version, planes, params, refs, gate (optional).

## review.svg_zoom(win, cu, planes, paths, signals, vrows, gnd_ps, items, oc=None) -> (svg, legend)

Draws GND coverage only for `planes`, traces only on `signals`; legend = [(colour, label)] naming every drawn layer.
