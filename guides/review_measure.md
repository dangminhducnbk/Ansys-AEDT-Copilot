<!-- Layout review as data: code measures each check (reference / SOV, trace stubs, vias, routing) on any board or cut design, gives OK / NOT OK per check against its threshold and NOT OK counts per channel (no severity levels, no verdict) and stores a review record; the engineer reads the report and decides. Use for "review layout", "kiểm tra via stub / SOV / GND via / chiều dài", the standalone layout-review workflow, and the MANDATORY review step of interface simulation. -->
# REVIEW MEASURE — CODE MEASURES, YOU INTERPRET

## 1. MISSION
Give the engineer an honest picture of the layout for a channel: OK / NOT OK and numbers from code, explanations on
request from you, decisions from the engineer.

## 2. RULES OF ENGAGEMENT
- Measure ONLY with `design_review` (any board / design) or `isim_review` (agreed interface of a request). Never
  compute geometry yourself, never estimate numbers not in the result.
- HTML report with images (old `review_layout`, removed in 1.0.0): `design_review(..., html=true)`; rules below.
- Rules (`checks=` comma list of rule ids, empty = all): one steering per rule, list in section 2d; read a rule's
  steering (`review_rules(op="get", rule_id)`) before interpreting its findings. One rule alone when the engineer asks
  for one ("via stub của net X") — it is faster.
- Each item is OK / NOT OK against its rule's threshold (4.0.0, user 2026-11-15: no severity levels). Never
  re-classify, rank, soften or judge a finding; give the numbers and the limit. Never drop a point silently.
- Rule-specific judgement (via stub vs data rate, via clearance, ...) lives in that rule's steering
  ("Discuss"). Each evidence line of a point appears once (identical lines are merged by code).
- A check returning `error` (e.g. `no plane layer`) → report it; do not guess its result.
- Thresholds live in the template `review.*`; change only on the engineer's request (`show_defaults`).
- Reply in the user's language. Tables. Short.

## 2b. LAYOUT SNAPSHOT (2.2, feature 023)
- `design_review` / `isim_review` measure on a LAYOUT SNAPSHOT by default: the board is read once into files under
  `<board folder>/Ansys AEDT Copilot/snapshots/` (never inside the `.aedb`; the board is never written). Results are
  identical to reading EDB live; a re-run (other checks, other thresholds, next day) takes seconds.
- First review of a board / interface builds it (board1: ~45 s instead of ~90 s live). To hide that time, build it in
  the background as soon as the nets are known: `layout_snapshot(op="build", board, nets="<nets or patterns>")` →
  `task_id` → do not wait; the review reuses it.
- The result's `source` says `snapshot` (index / window `built` or `reused`) or `live`. `live` with a `warning` = the
  snapshot could not be used (board open in AEDT while a build was needed, primitive that could not be converted —
  ids listed): the review ran live, numbers are still valid; mention the warning in one line.
- The board changed (saved in AEDT) → the old snapshot is stale and is rebuilt automatically; never reused silently.
- `layout_snapshot(op="status", board, nets)` → `valid / stale / missing / too_small`; `op="list"` → snapshots of a
  board. Old snapshots are kept; deleting one = the user's decision (they delete the folder).
- Compare with the live path only on request: `snapshot="off"` (or template `review.use_snapshot = false`).
- HTML report (2.6): built from the same snapshot (no second live read; seconds once the snapshot exists). The header
  line "Board data: snapshot | live" says which; `live` + warning = fallback (tell the user why). Numbers / ids /
  statuses equal the live report; pictures may differ only in drawing (arcs as chords ≤ 1 µm).

## 2c. COUNTS + REVIEW RECORD (025; 3.0.0: no verdict; 4.0.0: no severity)
- Every review gives per channel the number of NOT OK points and NOT OK findings per check (`findings` =
  `{counts: {"NOT OK": n}, by_check}`, `findings_md`) and `incomplete` + `failed_checks` (a check returned `error`,
  the channel could not be traced). There is NO verdict and NO severity: a count never blocks or allows anything
  (user rules 2026-11-14 / 15). The engineer reads the report and decides.
- Every full review is stored as a record next to the board: `<board folder>/Ansys AEDT Copilot/reviews/<board>/
  review_<time>.json` (`review_file` in the result; never overwritten; the board is never written). Give the path.
- Interface simulation REUSES a record when the board is unchanged (snapshot key), same two ends, same nets, all four
  checks, same `review.*` thresholds; anything else → measured again (never reused silently; `reused_from` says it).
- No per-point decision / override tools any more (removed in 3.0.0). Inside interface simulation the review always
  writes the HTML report; the user's ONE approval at GATE A (after reading it) is what allows the cut (guide
  interface_sim Phase 1).

## 2d. RULES — ONE FILE PER RULE (2.9, feature 031)
- Every rule has its OWN steering (what it checks, thresholds, when it is NOT OK, why, fix, how to discuss) and, when it
  measures, its own code file. Before you interpret findings of a rule, read ITS steering:
  `review_rules(op="get", rule_id=<id>)` (finding name → rule: the table below). Do not explain a rule from memory.
- `review_rules(op="list")` → all rules: team (repo `review_rules/`) and personal (`AEDT_COPILOT_REVIEW_RULES` or
  `~/.aedt_copilot/review_rules/`); a personal rule with a team id is `shadowed` (team rule used). A personal rule
  with code runs only after the user enabled it: `review_rules(op="enable", rule_id, user_approved_personal_code=true)`
  only after the user said so in this conversation. A rule without code (`has_code=false`) is judged by YOU on
  request from the review data / pictures, labelled "judged by Claude".
- No NOT OK item stops a cut (3.0.0 / 4.0.0): the engineer reads the report and decides.
- `design_review(checks=...)` takes rule ids; old names still work: `reference` = sov, ref_other_net,
  loss_of_reference, via_clearance; `vias` = ref_plane_change, via_stub, nearest_gnd_via.

<!-- rules:begin (generated: python -m aedt_copilot review-rules --op=guide-list) -->
| Rule id | Title | Findings | NOT OK when | Thresholds |
|---|---|---|---|---|
| `coupling` | Coupling to other nets (3W) | Coupling to other net | edge-to-edge gap < factor × width over ≥ the minimum length | `review.coupling_gap_factor`, `review.coupling_min_len_mm`, `review.neckdown_zone_mm` |
| `loss_of_reference` | Loss of reference | Loss of reference | no GND on any reference plane over a stretch | `review.sample_step_mm`, `review.pad_exclusion_mm` |
| `nearest_gnd_via` | Nearest GND via | Nearest GND via | the distance > the limit | `review.gnd_via_flag_mm` |
| `pair_gap` | Pair members split apart | Pair gap | gap > nominal gap × ratio over ≥ the minimum length | `review.pair_gap_ratio`, `review.pair_gap_min_len_mm`, `review.neckdown_zone_mm`, `review.bga_breakout_margin_mm` |
| `pair_skew` | Pair / trio lengths | (data) | data only (no finding): the allowed skew depends on the interface spec, which the engineer knows | - |
| `plane_edge` | Trace near reference plane / void edge (3H) | Near plane edge | trace nearer than factor × H to a plane / void edge over ≥ the minimum length | `review.plane_edge_factor`, `review.plane_edge_min_mm`, `review.plane_edge_min_len_mm`, `review.neckdown_zone_mm` |
| `ref_other_net` | Reference to another net | Ref to other net | a reference plane has copper of another net under the trace | `review.sample_step_mm`, `review.pad_exclusion_mm` |
| `ref_plane_change` | Reference plane change at a via | Ref plane change | no GND via within the limit (with one: OK, kept as data) | `review.ref_change_gnd_via_mm` |
| `routing` | Routing data (length, width, skew, layers) | (data) | data only (no finding); never judge skew (4.1.0) | - |
| `serpentine` | Serpentine (length matching) geometry | Serpentine | a serpentine breaks a geometry limit (one finding per serpentine; passing ones are not listed) | `review.serp_gap_factor`, `review.serp_amp_factor`, `review.serp_chamfer_factor`, `review.serp_chamfer_tol`, `review.serp_rise_factor`, `review.serp_bump_max_mm`, `review.serp_bump_spacing_mm`, `review.serp_bump_ratio`, `review.serp_min_bumps`, `review.serp_excl_mm`, `review.serp_step_mm` |
| `sov` | Signal over void (SOV) | SOV | a reference plane has no copper under the trace | `review.sample_step_mm`, `review.pad_exclusion_mm` |
| `stackup_width` | Trace width / pair gap vs the stackup table | Width vs stackup, Gap vs stackup, No stackup value, No stackup table | measured − table > the tolerance (no table / layer entry: OK, kept as data) | `review.stackup_tol_mm`, `review.neckdown_zone_mm` |
| `trace_stubs` | Trace stub | Trace stub | an open trace end or a T-branch | - |
| `via_clearance` | Trace over via clearance | Trace over via clearance | never: OK, kept as data (trace over another net's via clearance) | `review.sample_step_mm`, `review.pad_exclusion_mm` |
| `via_stub` | Via stub / backdrill | Via stub | the stub > 0 | - |
<!-- rules:end -->

### Changing a threshold (the user asks "đổi ngưỡng ...")
- Thresholds are the `review.*` rows of `templates/autocut_template.csv` (team defaults; `show_defaults` lists them).
  There is no per-run argument: tell the user which row and value to change; the repo owner edits the CSV (text
  editor, `.` decimal). It applies from the next review; review records measured with other thresholds are not
  reused (025) → the next review measures again.
- Never change a threshold on your own; never "interpret away" a finding — report it with its numbers.

### Stackup table (rule stackup_width)
- Stored per board: `<board folder>/Ansys AEDT Copilot/stackup/<board name>.json` (never inside the `.aedb`).
- Import: the user gives the fab stackup (PDF / Excel). `review_stackup_table(board, op="template")` → the board's
  signal layers. Read the file (pdf / xlsx skills), fill per layer `se_width_mm` (single-ended trace width) and
  `pairs: [{name, width_mm, gap_mm}]` (diff pair width / gap; one entry per impedance class, e.g. "PCIe 85", "USB
  90"), in mm. SHOW the table to the user (layer × width / gap) and ask them to confirm. Only after "đúng / OK":
  `review_stackup_table(board, op="save", table=<JSON>, source_file=<fab file>, user_confirmed_table=true)`.
- Re-import / edit: same steps; `op="get"` shows the current table; save again (the old file is kept as
  `<name>_old_<time>.json`). A changed table makes the next review measure again.
- No table → each channel has an OK data row "No stackup table" (offer the import). A layer missing in the table →
  OK data row "No stackup value" (ask the user for that layer's values).

## 3. EXECUTION
1. Ask for missing inputs: board or design, channels `A-B:pattern` (or the agreed interface).
2. Run the measure. Long run → `task_result`.
3. Chat summary (default): per channel, table of NOT OK points (`summary_md`: point, status, net, layer, x/y mm,
   evidence) + one line per check (NOT OK count, errors). No ranking or judgement of points; explain a point only when
   the engineer asks, with its numbers and limit. Pair lengths (P / N) are in the report: never judge skew, never ask
   for a skew limit (the allowed skew depends on the interface spec, which the engineer knows).
4. Discuss when the engineer asks; the engineer decides what to do with each point (nothing is recorded per point).
5. End with the counts per channel (`findings_md`) and the record path. No verdict words.
6. HTML with images only when asked: `html=true` (layout review HTML, see "HTML report" below). When summarising the
   HTML for the engineer, use OK / NOT OK per section.

## DEVELOPER: ADD A REVIEW RULE (2.9, feature 031)
Only when the repo owner (team rule) or the user (personal rule) asks for a new rule. Its own files, nothing else:
1. Steering: copy `review_rules/_template.md` to `review_rules/<id>.md` (team) or `<personal folder>/<id>.md`; fill
   the header table (id, findings = report titles, section, not ok when, thresholds, limit key, code) and What / Why /
   Fix / Discuss. Why / Fix go to the JSON / chat; `## Report` (one `- Name: short text` line per check, listed under
   "This section checks:") and `## Issue` / `## Recommendation` (one sentence each, `{placeholders}` filled by the code,
   one bullet ``- `<finding>`: sentence`` per finding / variant) ARE the HTML report sentences (2.11.0).
2. Code (when it measures): copy `aedt_copilot/review_checks/_example.py` to `review_checks/<id>.py` (team) or
   `<personal folder>/<id>.py`; NAME = id; `TITLE, RULE = X.meta(NAME)`; `run(cc)` → `{items, data}`;
   `REPORT = X.report(NAME, describe, layers, picture=None, fields=None)` with `describe` returning labelled rows and
   `X.text(NAME, "why" / "fix", variant, **values)`; optional `fields(f, P)` → extra placeholders for Issue /
   Recommendation, `picture(f, paths)` → own picture HTML (e.g. serpentine arrows).
3. Thresholds: template rows `review.<key>` (team) — the steering names them, never holds values.
4. Tests: `python -m unittest discover -s tests/unit -t .` (`test_review_rules_031` checks every team rule: complete
   steering, code ↔ steering, report text from the steering, guide list current:
   `python -m aedt_copilot review-rules --op=guide-list` prints the table above). Then `design_review(..., html=true)`
   on a board COPY.

## HTML report and check definitions (design_review html=true)
### H3. SCOPE
- Nets: all signal nets of each requested channel, including nets through series R/C/L.
- Reference nets: `cutout.reference_nets` (default GND).
- Units: mm. Coordinates: board coordinate system, (x, y), layer name.
- Plane layer: largest GND polygon ≥ `review.plane_area_ratio` × largest GND polygon of the board.
- Reference layers of a trace: nearest plane layer above and below (outer layer: one).
- Via stack: same-net vias within `review.stack_merge_mm` (stacked microvias) = one via.

### H4. RULES AND STATUS
Per-rule definitions, thresholds and when an item is NOT OK: the rule's own steering (`review_rules(op="get",
rule_id)`, list in section 2d). OK / NOT OK only; the engineer decides.

### H6. HTML REPORT
File: `<board_dir>/autocut/layout_review_<timestamp>.html` (`design_review(..., html=true)`). Self-contained (inline SVG, CSS, JS). Opens in any browser.
Language: English (user requirement).
Form (2.11.0, feature 033; numbers = the review data, nothing re-measured; ONE measurement run for all tabs):
1. Header: **Layout version** (board name, no `.aedb`), **Review date** `dd/mm/yyyy - hh:mm:ss` (3.0.0: no gate
   verdict line).
2. One tab per connection (channel). Each tab is a full report of that connection only.
3. Only **OK** (blue) / **NOT OK** (red), in the report and in the JSON results. Issue = a NOT OK finding (beyond
   its rule's threshold); OK rows are data and not listed.
4. `1. Summary`: Index · Section (name + one sentence) · <connection> (OK, or NOT OK + "N issue(s)") · Verdict. Rows in
   order 1 Routing, 2 Reference, 3 Trace stub, 4 Via, 5 Stackup; another section (e.g. Crosstalk) only when it has
   findings.
5. `2.x <section>`: "This section checks:" numbered list (from each rule's steering `## Report`), lead line `OK` or
   `NOT OK — N issues`, then (only when NOT OK) table Index · Verdict · Description · Picture with NOT OK rows only.
   Row = one abnormal point (findings at the same net + location merged) within that section.
   Description = two lines `Issue:` / `Recommendation:` (from the rule's steering `## Issue` / `## Recommendation`).
   Picture: fault marked by a pink dashed frame / ring, no colour legend, `Location: X = … mm, Y = … mm` under it;
   reference findings: one panel per reference plane; a point with several issues = one frame style per issue type
   (Loss of reference pink dashed, Near plane edge orange dotted, SOV purple dash-dot, Ref to other net brown long
   dash; 5.4.1) — two frames at one place are two different issues, not a duplicate. Serpentine: measuring arrows A / G / c / W and the compare lines
   "X = … must be ≤ / ≥ … → OK / NOT OK". Rows beyond `review.max_images` per connection: no picture (said in the row).
6. `2.1 Routing` starts with **Signal routing per pair** (view only, no verdict): one collapsed box per pair / trio
   (`<channel>: <P> / <N> (<comp_a> → <comp_b>)`) with a top view (P dark / N light, colour per layer, end bodies and
   series parts with real pads; zoom locked by default: click to unlock, wheel = zoom, drag = move, double-click =
   reset), a cross-section from the first pin to the last pin (trace red with segment length, via black, stub pink,
   backdrilled part dashed pink; a through-hole connector pin is drawn as a via but not counted; line "Vias · Backdrilled
   · With stub"; a member with another topology gets its own cross-section) and a length table (Total + per layer).
   Via counts are read here (rule `via_count` was removed in 2.11.0). ESD / hanging branches are not drawn.

Hand-off: send the HTML file (absolute path). Inside interface simulation that is all (the user reads it; guide
interface_sim Phase 1 step 5). Standalone, a summary only when asked: per connection per section OK / NOT OK + number
of issues, then the NOT OK rows (section, index, net, x, y mm, layer, Issue line). Use OK / NOT OK only.
