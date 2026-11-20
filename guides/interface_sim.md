<!-- Interface simulation process with the aedt_copilot MCP server: read schematic PDF + BOM once, agree interface content (nets, ends, series parts) with the user, cut each interface on a copy, check both ends, agree the settings table, apply, merge all into the user's workspace, and on request run the simulation on a remote server. Re-cut "như lần trước" from a previous run (user_settings.json). No Excel. Use for "interface simulation", "simulate interface/channel X", "cut lại X như lần trước", or the interface-sim prompt. -->
# INTERFACE SIMULATION — WORKFLOW

## 0. FIXED PROCESS (5.0.0, review first since 5.2.0, one review + settings page since 5.6.0) — THE WAY TO CUT
Every cut runs these steps in this order, the same every time. The user sees only the texts below (M = message,
Q = question). Each text is in the tool result as `answer_md`: PASTE IT VERBATIM (Vietnamese line + English line),
add nothing (no steps done, no counts, no comments on the review, no proposals).

| # | Step | Tool | Text |
|---|---|---|---|
| 1 | User gives board + interfaces | — | — |
| 2 | Request, trace every channel (ends + nets of the user's words) | `isim_start` → `isim_trace` (each channel) | — |
| 3 | Layout review of every channel + the request page (review + settings) | `isim_layout_review(request_id)` | M0p |
| 4 | User opens the page LINK (M0p): per channel resolves every NOT OK point (tab Review layout), then tab Settings; Saves, replies | — | Q1 only when the user did not say done |
| 5 | Read + validate the saved page (every point resolved, current review) | `isim_config_check(request_id)` | M2 (errors → back to 4) or Q2 |
| 6 | User answers Q2 | — | — |
| 7 | Cut + end check + build every channel, merge into a COPY of the board project in the request folder | `isim_go(request_id, user_approved_cut=true, user_words)` | M3 |

Rules of the fixed process:
- Only 2 questions exist: Q1 "Bạn đã config xong chưa? / Have you finished the config?" and Q2 "Đồng ý cut không? /
  Do you agree to cut?". Ask nothing else. Every other decision is on the page `config.html` (NOT OK points to
  resolve, cut region, nets, board / schematic differences, end cases, component model, setup, sweep, extents,
  channel folder).
- Review page (5.6.0): ONE page per request, full screen. Per channel: tab "Review layout" = board picture of the cut
  area with a marker per NOT OK point; a point opens the old report row(s) (Issue / Recommendation, picture with the
  measured values), a stackup cross-section, "Print issue to image" (PNG), Resolve (optional note); "Resolve all NOT
  OK" resolves every point of every channel after one confirmation; "Topology per pair" shows the routing boxes.
  Tab "Settings" of a channel unlocks when its points are resolved; Save unlocks when every point of every channel is
  resolved. Resolving is the user's decision only: never resolve, never judge a point for the user, never tell the
  user a point "can be ignored". `isim_config_check` / `isim_go` refuse unresolved points or a page of an older review
  (review measured again → the tool writes a new page; matching old resolutions come pre-ticked, a new Save is needed).
  Q2 shows "N NOT OK points resolved by the user". If M0p shows an error row there is no page: report it and wait.
- Requests of 5.2-5.5 (Q0): M0 + Q0 "Review layout ổn, chuyển sang bước config không? / Is the layout review OK, go
  on to config?" → `isim_review_answer(user_answered_review=true, accepted, user_words)`: "không" / "no" = M0x, request
  stopped for good; "đồng ý" / "yes" = config page, M1. Never answer Q0 for the user, never judge the review.
- Answers in both languages: "xong" / "done" → step 5; "đồng ý" / "yes" (after Q2) → `isim_go` with the user's words;
  "không" / "no" after Q2 → stop and wait. Never call `isim_review_answer` / `isim_go` without the answer in THIS
  conversation. An answer that is neither yes nor no = discussion: answer it, the question stays open.
- Requests made before 5.2.0 (no review step): continue with `isim_config` as before.
- Long steps return `task_id` → `task_result` until done; then paste its `answer_md`.
- Page (5.1.0): M0p / M1 gives a local LINK (`config_url`, this PC only). Save on that page overwrites the request's
  `config.html` directly (no dialog, no download). The page refuses a save when a newer page is on disk ("reload").
  When the tool cannot be reached (Claude closed) the page saves with the browser (dialog / Downloads); step 5 still
  finds it. Never ask the user for a file location.
- Step 2 needs more than the user's words (no end pair, ambiguous ends): ask that ONE thing, then trace.
- `isim_go` does content confirm, cut, end check, apply and merge itself: in this process NEVER call
  `isim_confirm_content`, `isim_cut`, `isim_apply`, `isim_merge`, `isim_settings_form`.
- No server run question. A simulation run happens only when the user asks for it (Phase 4, GATE D).
- Merged project (5.4.0) = COPY of the user's board project (`.aedt` + `.aedb`; board without `.aedt` → `.aedb`
  only) with every channel added as a new design. The board designs stay unchanged; the user's board is only read.
  After the merge every channel design is read back: components / pins = channel design, stackup = board (also in
  the self-check after the cut). M3 column "Stackup = board" + "Board copy" line; any difference = NOT OK (report the
  lines, never hide them). 5.0–5.3 merged projects (empty project): series RLC parts lost their pins there (AEDT
  Validation Check hangs) → re-run `isim_go`; the old file is moved to `_work/history/`.
- Folders: `<board dir>/Ansys AEDT Copilot/interface_sim/<board>_<time>/` = merged `<request>.aedt` + `.aedb`,
  `config.html`, `request.md`, one folder per channel (name typed by the user in the page) with `<name>.aedb`,
  `<name>.aedt`, `review.html`, `config.html` (read-only record), and `_work/` (tool files). Nothing of the user's
  workspace is written.
- Sections 1-… below describe the step tools. Use them only for requests made before 5.0.0, or when the user
  explicitly asks for a single step (manual / recovery).

## 1. MISSION
Turn the user's interface requests into simulation-ready HFSS 3D Layout designs inside the user's AEDT workspace.
Code measures and executes. YOU decide WITH the user: show the data, propose, ask, wait for an explicit go.
Unknown cases are reported with numbers and options. Never pick a default silently.

## 2. RULES OF ENGAGEMENT
- Use ONLY `aedt_copilot` tools (`isim_*`, `get_guide`, `task_result`). No pyaedt-mcp, no ad-hoc scripts.
- User is listing / discussing → RECORD ONLY. Act on explicit go ("làm đi", "đồng ý", "go").
- 4 gates, locked in the server. Set a flag to true ONLY after the user's explicit go in THIS conversation:
  | Gate | Tool | Flag |
  |---|---|---|
  | A content | `isim_confirm_content` | `user_confirmed_content` |
  | B settings | `isim_apply` | `user_agreed_settings` |
  | C merge | `isim_merge` | `user_approved_merge` |
  | D run | `isim_run` | `user_requested_run` |
  | 5.0.0 one go (Q2) | `isim_go` | `user_approved_cut` (+ `user_words`) |
  A refusal says what is missing → do that or ask. Never set a flag to pass a refusal.
- The user's board / workspace are never written, except the merge into the workspace (backup first).
  Never delete files, never delete `.lock` files. Never operate AEDT GUI while the user works in it.
- Settings live in the chat table and in ONE file per request, `user_settings.json` (written by the tool at gates A
  and B: content, cut values, end handling, all settings). No Excel, no `settings.json` / `settings.md` any more.
  This is THE cut flow since 1.0.0 (the channel Excel flow was removed).
- "như lần trước", "settings cũ", "giống lần trước", a previous request id or a `user_settings.json` path → ALWAYS
  the re-cut process (Phase R). Never re-type old values by hand; show ONLY the differences.
- Reply in the user's language. Short. Tables. Always give file paths.
- SHORT, STANDARD OUTPUT (user rules 2026-11-14 / 15, 4.0.0). The answer to a channel request is the tool's
  `answer_md` (from `isim_cut_preview` / `isim_review`), sent with `answer_image` and the review HTML file, PASTED
  VERBATIM. Add NOTHING: no steps done, no file copies, no counts, no notes on severity / findings, no notes on series
  parts (they are 0 Ω by team default; never mentioned, never asked), no proposals. Details only when the user asks.
  Ask only what the tool cannot decide (its questions are already inside `answer_md`). Everything with a team default
  is used, not asked.
- NO JUDGEMENT OF FINDINGS (user rule 2026-11-15, 4.0.0): review checks are only OK / NOT OK against their
  thresholds. There are no severity levels. Never rank, soften or classify a finding; the engineer decides 100 %.
- INPUT FORMS (user rules 2026-11-06 / 2026-11-14). GATE B settings: the FORM from `isim_settings_form` is MANDATORY
  (see GATE B FORM below) — never ask setting values one by one (no "sweep 0 / 20 / 0.01?" question with buttons).
  No widget support → the form's full `table_md` once; the user edits by text. GATE A: no form by default (the
  content is the traced proposal); the content form / cut settings form only when the user asks to change something.
  | Gate | Form fields |
  |---|---|
  | A content (on request) | end pair (`comp_a` / `comp_b`, choice from `candidates`), nets (checkboxes), one choice per board vs schematic difference and per `recut_diffs` item (keep old / use new / exclude / text) |
  | B settings (mandatory) | FULL form from `isim_settings_form` (005): see GATE B FORM below |
  Rules:
  1. The submitted form is INPUT, never the gate go. Send it to the tool (`isim_validate_settings` for B; the content
     JSON for A is shown as `content_md` first), show the resulting table (`table_md` / `content_md`) and errors, then
     wait for an explicit "đồng ý" before setting `user_confirmed_content` / `user_agreed_settings`.
  2. Mandatory sweep fields start EMPTY unless the value comes from the user or a previous run (Phase R). Never invent.
  3. Pre-filled values = tool proposal / template defaults / previous run only. Locked rows (`cutout.*`, `series.keep`)
     are shown read-only in the B form.
  4. Server validation is unchanged: a form never bypasses `isim_validate_settings` / `isim_validate_form` errors.
- GATE B FORM (005, user 2026-11-06). Call `isim_settings_form(request_id)` once for the request; build the widget ONLY
  from its data (never hard-code keys, defaults or choices — the template is the source):
  1. One TAB per `tabs[]` item, named after the interface, request order. `enabled: false` → tab disabled, shows
     `step` + `reason`. More than 8 tabs → short names, full name on hover.
  2. In a tab: one section per `groups[]` item (cutout, cleanup, series, port, solder_ball, setup, sweep, airbox …);
     every descriptor once: `label`, input by `type` (num → number, bool → checkbox, `choices` → dropdown, list /
     text → text), `unit`, `desc` as hint, value = `value`. `locked` → read-only with `locked_reason`. `mandatory` and
     empty → empty field marked mandatory (never invent). Then one choice group per `unusual` refdes with exactly its
     `options`, pre-selected from `handling`.
  3. Buttons: "Set default" (this tab) = every editable (unlocked) field → its `default` (applied tabs: simulation
     group only); fields with `default: null`
     (mandatory sweep) keep what the user typed in this widget or stay empty. "Set default for all tabs" = same on
     every enabled tab. Purpose = reset after a mistake; normal edits stay free. "Copy to all tabs" = this tab's
     editable, non-locked values → other enabled tabs (never `handling`, never locked rows).
  4. Submit → send JSON `{interface: {values: {key: value}, handling: {refdes: option}}}` for the enabled tabs
     (`sendPrompt`) → call `isim_validate_form(request_id, entries)`. Show each interface's `table_md` + errors. A tab
     with errors does not block the others.
  5. GATE B stays PER INTERFACE: after the user's explicit go for an interface, `isim_apply(request_id, name,
     values, handling, user_agreed_settings=true)`. The form submit is never the go.
  6. No widget support → show the form's `table_md` (all settings, grouped, per interface); the user edits by text.

## 3. PHASES

| # | Phase | Tools | Exit |
|---|---|---|---|
| 0 | Intake + schematic/BOM | `isim_start`, `isim_bom`, `isim_save_schematic` | schematic.md saved (or user has none) |
| 1 | Channel request → review report + final cut area → ONE approval | `isim_trace`, `isim_review`, `isim_cut_preview`, `isim_confirm_content` (`isim_cut_form` on request) | GATE A = the user's go after reading the review, per interface |
| 2 | Cut, ends, settings form, apply | `isim_cut`, `isim_check_ends`, `isim_settings_form`, `isim_validate_form`, `isim_apply` | GATE B per interface, self-check OK |
| 3 | Merge | `isim_status`, `isim_merge` | GATE C |
| 4 | Run (only on request) | `isim_run`, `isim_run_status` | GATE D |
| R | Re-cut from a previous run (replaces Phase 0 schematic work + Phase 1 trace) | `isim_previous`, `isim_start`, `isim_recut` | GATE A, then Phases 2-3 |

## 4. EXECUTION

### Phase 0 — Intake + schematic / BOM (once per request)
1. Ask for: workspace `.aedt` (user prepared), optional board `.aedb` (default = workspace's), optional stackup file,
   the schematic NETLIST (preferred: exported from Altium = Protel netlist 2.0 / Allegro netlist; any file name),
   schematic PDF(s), BOM (.xlsx / .csv), the interfaces (nets and/or refdes, free text).
2. `isim_start(..., netlist=<path>)`. With a netlist the code reads all connectivity and part values (`netlist.json`):
   do NOT read the PDF for connectivity; skip to Phase 1. Wrong file (another design) → the trace refuses it; ask for
   the right netlist. Without a netlist: if `schematic_status.up_to_date` or `reuse_from` → skip to Phase 1 (say
   "dùng lại schematic.md"), else steps 3-5.
3. BOM given → `isim_bom` (code parses it). Report column mapping and warnings.
4. Read the PDF yourself (page by page for large files). Fill `schematic_template` EXACTLY (same section names and
   table headers). Components = refdes / part / value / page. Nets = only nets you can read with their pins
   `refdes.pin`. Follow off-page connectors / sheet ports across pages (the net may have another name on the other
   sheet or inside a block); write each name you saw as its own net row with the pins on that sheet — the code compares
   by pins, not names. Anything unclear → `## Unreadable` (those pins count as "board only", never a difference). Do
   not guess connections.
5. `isim_save_schematic(request_id, markdown)`. Show counts, unreadable items, BOM differences. Give the path.
6. No schematic → say content is checked against the board only.

### Phase 1 — Channel request → review report + final cut area → ONE approval (per interface, 3.0 / 4.0)
Rule (user 2026-11-14 / 15): the review HTML is always made and sent; the user reads it and decides 100 %. NOT OK
items never block or allow a cut by themselves; there are no severity levels. Locked in code: `isim_confirm_content` (GATE A) is
refused without a current review with its report or without a preview of the same cut settings; `isim_cut` is
refused until GATE A recorded the user's approval of THAT review.
1. Turn the user's words into refdes / nets. `isim_trace(request_id, name, refdes, nets)`. Do not ask or print
   anything here: the tool's open questions (end candidates, REAL board vs schematic differences = pins on other
   nets / nets missing / series values) are lines of `answer_md` (step 5); never resolve one yourself. Pins the
   schematic does not show and net renames (off-page / block) are `schematic_info`, not differences.
2. Right after `isim_trace`: `layout_snapshot(op="build", board=<request board>, nets=<traced nets, comma
   separated>)` in the background (read only, `task_id`; do not wait, do not mention).
3. `isim_review(request_id, name)` — MANDATORY, all checks, never skipped. Runs on the snapshot; a valid earlier review
   of the same board / ends / nets / checks / thresholds is reused (`reused_from`). It ALWAYS writes the HTML report:
   `html` = absolute path. `html_error` → tell the user the report failed and why; no approval is possible
   (`no_report`) until `isim_review` succeeds. `reuse=false` only when the user asks to measure again.
4. `isim_cut_preview(request_id, name)` with the default cut settings (no form). `image` = the FINAL cut region (end
   enlargements merged, one green outline; legend Signal / Cut region / GND pin / GND via); `ends_lines` = one line per
   end (factor auto / manual, + mm² added, GND kept); `detail` + `zooms` = diagnostic pictures (base cut, added area,
   other nets) — only when the user asks about an end factor. `errors` → tell the user (GATE A is refused until fixed).
   `source.kind = live` + `warning` → say the preview was read live and why.
5. ANSWER THE CHANNEL REQUEST = the tool's `answer_md` (in the `isim_cut_preview` result, or `isim_review` when the
   preview came first): send the files in `answer_files` (cut region image + review HTML), then paste `answer_md`
   VERBATIM as the whole reply. It holds: title with size / area, one line per end, the review file, the tool's own
   questions (real board vs schematic differences, end candidates) and the final "Đọc review rồi xác nhận cut <name>?".
   Do not add or remove a sentence. `answer_md` null → `answer_reason` says what is missing (run it, or tell the user
   the error). Board vs schematic items in `schematic_info` (board only, renamed) are information: never asked,
   never shown unless the user asks. Details (nets, series parts, findings, cut settings) only when the user asks —
   answer from `content_md`, `findings_md`, the report, `table_md`. Several interfaces → one `answer_md` each.
6. The user wants a change (nets, ends, cut value, end factor) → apply it (`isim_cut_form` / `isim_cut_preview` with
   `values` / `end_factors`; changed nets → `isim_review(..., nets=...)`), then answer again with the three parts.
   Never change a value yourself.
7. GATE A = the ONE approval: the user's explicit "đồng ý" / "cut" for THIS interface after the three parts →
   `isim_confirm_content(request_id, name, content, user_confirmed_content=true, user_words=<their words>)` with
   `content` = the traced proposal (+ `structural` / `end_factors` the user set). The tool records the approval
   (time, report, review, NOT OK counts, preview) in `user_settings.json` `review.approval`.
   An answer given while discussing, or before the report was sent, is NOT the approval.
8. Then Phase 2 directly (no extra question). `isim_cut` returns `preview_check` (`equal: false` → tell the user).
9. The approval belongs to THAT review: board saved again, other ends / nets, other thresholds → status
   `approval out of date`; `isim_review` again → report → the user approves again. Changing content later sends the
   interface back to Phase 1 (old outputs renamed `*_old_<time>`, not deleted).
10. `checks=<one>` (a quick question) writes `review_partial.json` and does NOT count as the mandatory review.
11. `isim_status` Review column: not reviewed / out of date / approval out of date / no report / report ready /
   approved.

### Phase 2 — Cut, ends, settings, apply (per interface)
Several interfaces: start one sub-agent per interface for 2.1–2.2 when your client supports sub-agents.
A sub-agent never asks the user; it returns tables and questions to you. You ask the user, one interface at a time,
interface name first.
0. Stackup file (path in `request.json` `stackup`, optional): the source for layer data (thickness, material,
   Dk / Df) when the EDB lacks it or the user doubts it. Read it, show the values next to the EDB values, ask.
   Never change the EDB stackup without the user's go (no tool does it today: report, do not script it).
1. `isim_cut(request_id, name)` → usually `task_id`; poll `task_result` every 1–2 min (~5 min per interface).
2. `isim_check_ends(request_id, name)`. Show `ends_md`: type, pins, GND near each signal pin, pads, solder ball,
   via-in-pad, **Unusual**, and the **End GND rule (cut extent)** table (2.1.0, `end_gnd` per end).
   END GND RULE (in the cut, automatic): the tool first DETECTS each end's GND pins / GND exposed pad on the source
   board (`gnd_pins_on_board`, `gnd_pins_detected`). The whole interface is cut with `cutout.expansion`. An end that
   HAS GND pins but none FULLY inside the extent gets ONLY its region (component body + `cutout.end_region_margin_mm`
   1 mm) enlarged: factor + `cutout.end_expansion_step` 0.02 per try, NO maximum, until a GND pin / pad is fully
   inside; its GND vias are kept. Results: `met` (nothing changed), `enlarged` (show GND pins detected, base factor →
   factor used, added mm², GND pin gained, `other_nets` in the added area — NOT kept by the cut — and send
   `end_gnd.image`), `no_gnd_pin_on_board` (only then the no-GND question below). An end with GND pins never gets
   the no-GND question. Region fully covered and still no GND pin inside → the cut fails with a geometry error naming
   the end and pins: report it, never work around it. Always show enlarged ends to the user before GATE B. To change
   the two values: GATE A (structural `cutout.*`) or a re-cut.
3. Connector end (refdes / part matching `interface_sim.connector_patterns`): NOT a question. It gets the team
   default `interface_sim.connector_handling` (`smd_rebuild`: ports on the connector's signal pins, the connector's own
   GND pins as reference; a GND plate only when it has no GND pin). `isim_check_ends` returns `default_handling`
   and an "End handling (team default)" table: show it with the settings at GATE B, say the engineer may change it
   (`keep_component` / `no_solder_ball` / `stop_interface`). The handling used (default or chosen) is stored in
   `user_settings` and re-used by re-cut. A connector with another unusual rule is asked as below.
   Unusual end (`no_gnd_near_signal`, `non_round_pad_bga`, `unknown_type`, `pad_size_mismatch`; `connector_end` only
   in runs before 0.13.0): explain with the measured values, list its `options` with their effect, ask the user to
   choose:
   | Option | Effect |
   |---|---|
   | `smd_rebuild` | normal SMD port rebuild (pin moved to pad end, GND plane under body) |
   | `keep_component` | no component rebuild for this end (ports on the original pins) |
   | `no_solder_ball` | no solder ball on this end |
   | `stop_interface` | stop this interface (marked failed) |
   **No GND pin (`no_gnd_pin`, 0.14.0) — the user decides, never you.** An SMD IC / connector end with NO GND pin
   stops with `gnd_questions[refdes]`: an image (`image`: signal pads red, GND vias blue, existing GND copper light
   blue, proposed rectangle dashed with its size) and `options` for THIS case. Send the image path, then ask ONE
   multiple-choice question listing exactly `options` in order (use `question_md`), plus each `omitted` option with its
   reason. Never pre-select, never recommend silently, never answer for the user.
   | Option | Effect |
   |---|---|
   | `gnd_plate_vias` | draw the proposed GND rectangle bounding the GND vias in the body; the vias become GND pins |
   | `gnd_existing_copper` | GND vias in the body that land on existing GND copper become GND pins; no new copper |
   | `gnd_keep_pad` (0.15.0) | the component HAS GND pin(s) (e.g. exposed pad) that the cut lost: apply cuts again with extent = old ∪ (pad + `interface_sim.keep_pad_margin_mm` 0.5 mm); the pad is the GND pin, its GND vias are kept, no plate. Offered only when such a pad touches the cut extent; the image shows it green, old extent grey, extended extent green line; `keep_pad.other_nets` = other nets inside the extension (NOT kept by the cut) — name them in the question. Apply takes ~1 cut longer (re-cut) |
   | `keep_component` | no rebuild (ports on the original pins; the port may lack a near GND reference) |
   | `stop_interface` | stop this interface |
   | `other` | the user's instruction: map it to ONE option above and say which (pass the text as `gnd_notes`); no option fits → say no tool does it (no ad-hoc script), the end stays undecided |
   Apply with `handling[refdes]` = the user's option, `gnd_notes` = their words, `user_approved_gnd=true` ONLY after
   their answer in this conversation. The answer is stored in `user_settings.json` (`gnd_decisions`).
4. SETTINGS = the GATE B FORM, MANDATORY (`next` in the `isim_cut` / `isim_check_ends` results says so):
   `isim_settings_form(request_id)` → draw the form (all interfaces of the request in tabs, pre-filled, mandatory
   sweep fields `sweep.start_ghz` / `stop_ghz` / `step_ghz` EMPTY — the user types them, never invent) — see RULES:
   GATE B FORM. No widget support → the form's full `table_md` once; the user edits by text. NEVER ask setting values
   one by one in chat or with answer buttons. "Locked" rows (`cutout.*`, `series.keep`) change only through Phase 1 +
   re-cut. Measured numbers appear only in the Note column.
5. Form submit / text changes → `isim_validate_form` (or `isim_validate_settings(values, handling)` for one
   interface); show `table_md` and errors.
6. GATE B: `isim_apply(request_id, name, values, handling, user_agreed_settings=true)` → `task_id` (~1–3 min).
   With a `no_gnd_pin` end add `gnd_notes` and `user_approved_gnd=true` (only after the user's answer, step 3).
7. Report `self_check.gnd_reference` per end (own_pins / plate_vias with rect / existing_copper / kept_pad with pad_vias / none) and
   `self_check` (ports vs signal pins AND vs `expected_ports_2x_paths` = 2 × signal paths — a series part
   joins two nets into one path, pin shift ≤ 1 mm, setup / sweep present AND every setup / sweep / arc step / airbox
   value read back = agreed) and `warnings`. Series parts: list `self_check.series` (refdes, type, part, model) and
   TELL the engineer in plain words that these parts are SHORTED in the model (R = `series.model_r_ohm`, e.g. AC
   caps 220 nF of PCIe TX are not simulated as capacitors). Check with
   criteria of "Verification checklist" below. Mismatch → tell the user; fix with a re-apply (step 8) when it is a simulation
   value, else re-cut.
8. RE-APPLY after apply / merge (user rule 2026-11-06). Settings are in two groups:
   | Group | Keys | After apply |
   |---|---|---|
   | cut | `cutout.*`, `series.*`, `cleanup.*`, `port.*`, `solder_ball.*`, end handling | LOCKED — change = re-cut (Phase R / Phase 1) |
   | simulation | `setup.*` (adaptive freq, passes, delta S, convergence, arc step …), `sweep.*`, `airbox.*` | editable |
   The user asks to change a simulation value → show the table (`isim_validate_settings` or the form: applied tab,
   cut group read-only "đã cắt, đã khoá") → explicit go → `isim_apply(..., user_agreed_settings=true)` again. The
   tool backs up `final/<name>_old_<time>.aedb`, rewrites ONLY setup / sweep / airbox, runs the self-check and
   compares geometry with the previous apply (`geometry_same`). Report the backup path, the self-check and
   `geometry_diff` (must be empty). A cut-group change is refused naming the key: tell the user it needs a re-cut.
   Interface already merged → after re-apply it is `applied` again; the workspace changes only through a new
   `isim_merge` (GATE C), which adds a NEW design (`_v2` …); the earlier merged design stays. Never re-type cut values.

### Phase 3 — Merge
1. `isim_status(request_id)` → show `table_md`. Not all interfaces applied → ask: merge the ready ones (pass
   `names`) or wait.
2. Workspace open in AEDT (`.lock`) → ask the user to close it or give the AEDT gRPC port. Never delete the lock.
3. GATE C: `isim_merge(request_id, names, port, user_approved_merge=true)` → `task_id` (~1–2 min per interface).
4. Report the merge table: design name per interface (`_v2` when the name existed), backup path, compare errors.
5. DEFAULT END of the process (user rule 2026-11-05): give the workspace path (`.aedt` + `.aedb`). The user zips it
   and takes it to the server themself (often a different network). Do NOT offer or start Phase 4 unless asked.

### Phase 4 — Run (ONLY when the user asks to run)
1. Default mode `service`: the user keeps the PyAEDT service manager running on the server (window shows
   `server started on [<ip>]:17878`). The tool opens its own non-graphical AEDT there and closes it when done.
   Ask for: server IP / name, simulation folder ON THE SERVER (`sim_dir_server`), and whether it is shared to this PC
   (then also `sim_dir` = same folder seen from this PC; otherwise the workspace is uploaded through the session).
   Firewall on the server must allow 17878, 18000-18100 (`client_port`, default 18050) and 50000-50010
   (`aedt_port`, default 50000). Port busy after a failed run → use another number in the range.
   Mode `grpc` only when the user opened AEDT themself with `ansysedt.exe -grpcsrv <port>` (needs `sim_dir`).
2. GATE D: `isim_run(request_id, server, port, sim_dir, sim_dir_server, designs, mode, aedt_port, client_port,
   user_requested_run=true)`. A NEW sub-folder `<request>_<time>` is used; designs are solved one after another.
3. `isim_run_status` on request or every ~10 min; report per design state, time, solver message, result path.
   Connection / upload failure → all designs `failed` with the message; check the service window on the server.

### Phase R — Re-cut "như lần trước" (per interface)
1. Find the source: `isim_previous(name, workspace)` → show `table_md` (request, date, last step, sweep), newest
   first. One run → use it (say which). Several → ask which. User gave an id / path (also a file copied from another
   PC) → use it directly. No run → say so; offer the normal process (Phase 0-1).
2. NEW request: `isim_start(workspace, ...)` (same inputs as before; schematic reuse works as in Phase 0). Never
   re-cut into the old request (the tool refuses).
3. `isim_recut(request_id, name, source)` (task; ~1 min). It re-traces with the old ends + nets on the CURRENT board.
   Show `content_md`: "Changes since previous run" first. `recut_diffs` empty → "Không có khác biệt" + the old
   content; ask for a go. Each difference (`net_added`, `net_removed`, `end_missing`, `end_pins_changed`,
   `series_added`, `series_removed`, `series_value_changed`, `diff_group_changed`, `board_file_changed`,
   `schematic_resolution_stale`) needs the user's resolution (keep old / use new / exclude / text) — never resolve one
   yourself. New nets are NOT in the proposal until the user adds them. `blocked` (an old end is no longer on the
   board) → show the difference, ask the user for the new end, then the normal Phase 1 (`isim_trace`).
   `previous_error` → tell the user why the old run failed.
4. Mandatory review (Phase 1 steps 3-5) for the re-cut proposal: reused when the board / ends / nets are unchanged,
   else measured; the HTML report is always written. `previous_review` in the `isim_recut` result shows the earlier
   run's approval (or a 2.12 override) — mention it in one line, never reuse it. Send the cut area + report, then GATE A
   (Phase 1 step 7) with `content.recut_diffs[{item, ref, resolution}]`. Then Phase 2 as usual.
5. `isim_check_ends` adds `handling_compare` (`handling_md`): `kept` (old choice still valid, pre-filled in
   `handling`), `not_needed` (end no longer unusual: tell the user, drop it), `needs_choice` (new unusual case: ask as
   Phase 2.3), `needs_confirm` (no-GND end: NEVER reused silently — show the image and the `previous` answer and ask
   the same multiple-choice question, previous answer named; old `smd_rebuild` = `gnd_plate_vias`). Show it next to
   `ends_md`. `end_gnd_compare` (2.1.0): per end previous vs now of the end GND rule; `enlarged` / `changed` rows are
   differences — tell the user (a run cut before 2.1.0 may now keep an exposed pad instead of the old plate, so its
   no-GND question disappears). A run before 2.1.0 also gets `recut_diffs` item `cut_method_changed` at GATE A
   (needs the user's resolution like any difference).
6. Settings table is pre-filled from the old run (`values`; Source `previous run <id>`). Rows marked
   `team default (new)` did not exist in the old run — point them out. `default_changes` = settings whose team
   default changed since the old run (e.g. arc step 10 → 30): the OLD value is kept (Source `previous run <id> (team
   default then)`, note `team default now <v>`) — tell the user in one line and ask only if they want the new
   default. Re-apply (step 8) also keeps the design's old value unless the user changes it. `dropped` keys are
   no longer in the template — tell the user they are not applied. Use `values` + `handling` from `isim_check_ends`
   in `isim_validate_settings` / `isim_apply`; the user's go at GATE B is still required.
7. Merge = Phase 3 (GATE C).

## 5. FILES (per request)
`<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/`: `request.json`, `user_settings.json` (everything
agreed; keep / copy it to re-cut later), `schematic.md`, `bom.json`, `<interface>/state.json`, `content.md`,
`ends.md`, `final/<interface>.aedb`, `merge.json`, `run_<id>.json`. Give these paths to the user when you report a
step. Requests made before 0.7.0 have `settings.json` / `settings.md` instead of `user_settings.json`; re-cut reads
them too.

## Verification checklist (after isim_apply, before GATE C merge)
Per interface, from the apply result (`metrics`, `warnings`, `self_check`):

| # | Item | PASS criterion | On fail |
|---|---|---|---|
| 1 | Apply state | applied, `self_check.ok` | FAIL. Read the apply log. State error. |
| 2 | Nets | All agreed nets present. No extra signal nets. | FAIL |
| 3 | Ports | Count = 2 × signal nets. Names `<refdes>.<pin>.<net>`. | FAIL |
| 4 | End components | Both present. Each has ≥ 1 GND pin. `gnd_reference` per end = the user's choice (own_pins / plate_vias + rect / existing_copper; `none (kept component)` only when the user chose keep). | FAIL — port has no reference / reference not the user's choice |
| 4a | Pin position | `max_pin_shift_mm` ≤ 1.0 (signal pins of both ends vs original board; SMD pins move only inside their pad, ~0.2 mm). | FAIL — pins moved, ports wrong |
| 4b | Component outline | Outline fits remaining pins (`bbox_mm` ≈ `pins_extent_mm` + pad size; not the original body, e.g. 45 mm BGA). | WARN |
| 4c | Component pins | Pin count = signal pins + GND pins kept. Component with 0 pins = rebuild failed. SMD / via-in-pad / connector ends (2.3.0): `self_check.gnd_pin_cleanup` per end = GND pins before → after, keep distance; every signal pin keeps ≥ 1 GND pin (its nearest one is always kept; `warnings` name a signal pin whose nearest GND pin is farther than the keep distance — tell the user). | FAIL |
| 5 | Series parts | Present. R = 0 Ω. | WARN |
| 6 | Extra components | None besides ends and series parts. | WARN |
| 7 | GND plane layers | Each plane layer = 1 main piece. No piece < 5 %. | WARN |
| 8 | Signal-layer GND | Only coplanar shields per N5. | WARN |
| 9 | GND vias kept by cleanup | Every GND via ≤ 1.0 mm from a signal via in layout review still exists after cut. | WARN — cleanup removed a return via |
| 10 | Solder balls | Set on BGA/SMD ends when enabled. Diameter and height carry unit mm (height `0.2mm`). | WARN |
| 11 | Setup | Adaptive freq = `sweep.stop_ghz`. ΔS, passes, basis per Settings. | FAIL |
| 12 | Sweep | One sweep. Start/stop/step = agreed sweep values. Causality, passivity on. | FAIL |
| 13 | Airbox | Per N10. Vertical padding 0.2. | WARN |
| 14 | User's board / workspace | Not modified (work on copies; merge not yet run). | FAIL — report immediately |

Status: any FAIL → FAIL; else ≥ 1 WARN → WARN; else PASS. Report a table interface | status | items | key values | result path. FAIL / WARN: state the cause, propose a fix (settings → re-apply, cut setting → re-cut), wait.

### After isim_merge
| Item | PASS criterion | On fail |
|---|---|---|
| Design present | In the user's workspace. Name = channel or `_vN` (reported). | FAIL |
| Content | Ports, setup, sweep equal to channel project (tool compares). | FAIL |
| Part names | `<part>_cut_1` suffix after paste is expected (name clash in project). | — |
| Net colours | `warnings` "net colour not set" (SetNetColor) = known on AEDT 2026 R1. Design is valid, only colours missing. | WARN — tell user, do not fail |
| Backup | Backup folder exists. | FAIL — stop, report |
| `main` design | Unchanged. | FAIL — restore from backup only on user order |

## Technical notes (cut operations; parameter keys = template `templates/autocut_template.csv`)
### N2 EXTENT
- `cutout.extent_type` [conformal].
- `cutout.expansion` [0.06], `cutout.expansion_unitless` [true] → factor × signal extent size. Matches AEDT "Auto Generate Extent". 0.06 ≈ 3 mm on board1.
- `cutout.round_corner` [true]. `cutout.increments` [1]. `cutout.reference_nets` [GND].
- End GND rule (2.1.0): `cutout.end_expansion_step` [0.02] (same unit as `cutout.expansion`),
  `cutout.end_region_margin_mm` [1.0]. Only the failing end region grows (no maximum); elsewhere the extent equals the
  base extent. No GND pin on the board → no growth, no-GND question (option `gnd_keep_pad` stays there for old cuts).
- Cut mode fixed: new design per interface (isim_cut). `use_current` NOT used (loses ports/setup in existing `.aedt`).

### N3 SERIES PARTS
- `series.keep` [true]: 2-pin R/C/L on net path between ends → KEEP. Nets on both sides included.
- `series.model_r_ohm` [0]: model R = 0 Ω.

### N4 END COMPONENT CLASSIFICATION
Determine once, BEFORE any rebuild, using signal pins only:
| Type | Rule |
|---|---|
| BGA / through-hole | Pins are vias/balls. Pins kept. Component rebuilt after GND cleanup: outline fits remaining pins (not the original body). Part `<part>_cut`. |
| SMD | Surface pad, no via in pad. Rebuild (§6). |
| SMD via-in-pad | Via inside pad. Port at the pad centre (50 %) or anywhere along the pad by the end's port position slider (N6). Component rebuilt. |

Component rebuild rules (all end types):
- Kept pins stay at their exact board position and rotation (also for rotated / bottom-side parts, e.g. J25 at 180°).
- Part definition name must be new in the project: `<part>_cut`, else `<part>_cut_2`, `_3`… (projects that already received merged designs contain `<part>_cut`).
- Rebuilt component pin count ≠ expected → channel ERROR.

### N5 GND CLEANUP
- Plane layer (GND area > 50 % of extent): delete pieces < `cleanup.island_min_ratio` [0.05] × largest piece.
- Signal layer: keep coplanar shield only:
  - distance to same-layer signal trace ≤ `cleanup.shield_keep_dist_mm` [0.5]
  - area ≥ `cleanup.shield_min_area_mm2` [0.5]
  - connected to GND via if `cleanup.shield_need_via` [true]
- PTH GND via farther than `cleanup.gnd_via_keep_dist_mm` [1.0] from signal → delete.
- GND microvia farther than `cleanup.gnd_microvia_keep_dist_mm` [1.0], or one end without GND copper → delete.
- BGA end: keep GND pins within `cleanup.bga_gnd_pin_keep_dist_mm` [1.6] of signal pins.
- SMD / via-in-pad / connector end (rebuilt; not `keep_component`, 2.3.0): keep own GND pins within
  `cleanup.smd_gnd_pin_keep_dist_mm` [1.6] of a signal pin (signal pin centre to GND pad edge; exposed pad next to
  the signal pins counts as near). An end with exactly ONE own GND pin / pad: that pin is the chip's return path —
  always kept, no distance warning, `info` "<refdes>: GND duy nhất pin <n>, đã giữ" (tell the user as info) + the nearest GND pin of every signal
  pin; never removed: the GND pin / exposed pad kept by the end GND rule, a kept pad, plate vias, existing-copper vias.
  The row is at GATE B (cut group); a re-cut of an older run applies it (Source "team default (new)").
- Never delete copper inside SMD rebuild area (§6).

### N6 PORTS
- `port.type` [coax]. One port per signal pin at each end. Name `<refdes>.<pin>.<net>`.
- BGA / TH: port at pin.
- SMD (`port.smd_new_component` [true]):
  1. Move pin to pad end on IC-body side (opposite trace direction).
  2. Pin pad = circle, Ø = pad width. Keep original pad copper as rectangle.
  3. Build GND rectangle plane under IC body collecting GND vias. Margin `port.smd_gnd_search_margin_mm` [0], gap `port.smd_gnd_plane_gap_mm` [0.1].
  4. Convert those GND vias to pins. Recreate component `<part>_cut`.
- Port position per end (config page slider, `component.model` `port_pct`, 5.3.0): ONE value 0–100 % for every
  signal pad of the end. The port (circle Ø = pad width W) slides along the pad's long axis; its centre is
  W/2 + pct × (L − W) from the pad end on the BODY side (pad 10 × 2 mm: 0 % → 1 mm, 50 % → 5 mm = pad centre = pin
  position, 100 % → 9 mm). Direction = towards the component body centre, for every pad (trace or not; for via-in-pad
  the via is NOT the port). 5.2.0 values: `port_location` `end` = 0 %, `centre` = 50 %. A pad without a long axis
  (square / round / on the body centre line) stays at the centre; at a value ≠ 50 % it gets a warning and the
  self-check reports "<refdes> port location (<pct> %)". The self-check reads every signal pin back and compares it
  with its target (± 1 µm). The config page draws the traces attached to each pad (where the trace comes from; 5.5.0: also inner-layer
  traces leaving a via in the pad, dashed, in the top view and the 3D view) and
  the port marks at the slider position. No per-end choice (step tools, old requests): old rule (trace pads moved
  opposite the trace, via-in-pad pads at the pad centre). `result.json` `metrics.port_location` records % and targets.
- Expected ports = 2 × signal nets.

### N7 SOLDER BALL
- `solder_ball.enable` [true]. BGA and SMD ends.
- Diameter = `solder_ball.diameter_ratio` [0.95] × short side of signal pad.
- `solder_ball.height_mm` [0.2]. `solder_ball.shape` [cylinder]. `solder_ball.material` [solder]. Reference size auto.
- Orientation: left to AEDT.
- Values are written WITH unit `mm` (e.g. diameter `0.38mm`, height `0.2mm`). A unitless value (`0.0002`) in the AEDT Component Model dialog = bug.

### N8 HFSS SETUP
- `setup.name` [Setup1]. `setup.adaptive_freq` [auto] → = `sweep.stop_ghz`.
- `setup.max_passes` [30], `setup.max_delta_s` [0.01], `setup.min_passes` [1], `setup.min_converged_passes` [1].
- `setup.max_refine_per_pass` [10] % (whole number 1..100; AEDT "Maximum Refinement Per Pass"). `setup.basis_order`
  [mixed]. `setup.max_delta_zo` [0.1] %.
- `setup.arc_step_deg` [30] deg (Advanced Meshing, circle / arc approximation; 0 < v ≤ 90). Team default was 10 before
  0.11.1: runs made before keep 10 on re-cut / re-apply unless the engineer changes it.

### N9 SWEEP
- `sweep.name` [Sweep1]. `sweep.type` [interpolation].
- Range `sweep.start_ghz` → `sweep.stop_ghz`, step `sweep.step_ghz`. Mandatory, user input only.
- `sweep.max_solutions` [2500]. `sweep.error_tolerance_pct` [0.1].
- `sweep.enforce_causality` [true]. `sweep.enforce_passivity` [true], `sweep.passivity_tolerance` [1e-6].
- Delete any default sweep created by the setup call.

### N10 AIRBOX
- `airbox.extent_type` [conforming], `airbox.dielectric_extent_type` [conforming].
- `airbox.horizontal` [0.05]. `airbox.positive_z` [0.2], `airbox.negative_z` [0.2]. `airbox.z_from_stackup` [true]: vertical NOT from XY extent.
- `airbox.open_region` [radiation]. `airbox.operating_freq` [5GHz].
### N11 DISPLAY + MERGE
- Display (merge, `finish_in_aedt`): highlight all nets (`display.highlight` [true]); signal `display.signal_rgb`
  [255,0,0]; GND `display.gnd_rgb` [0,0,255]; zoom fit; save.
- Merge (`isim_merge`, `design_merge`): backup first; each interface → new design, name = interface; name exists →
  `_v2`, `_v3` (never overwrite); ports / setup / sweep compared after paste; part definition clash → AEDT appends `_1`
  (expected); `.lock` present → ask the user to close the project, never delete the lock. After the merge each new
  design is read back (5.4.0): components / pins vs the channel design, stackup vs the channel; differences → that
  interface's merge is an error with the lines.

## Open in AEDT (on request)
`finish_in_aedt(aedb, port)`: opens a cut / merged design in AEDT, highlights nets (signal red, GND blue), zoom fit, save. Uses the AEDT GUI: ask the user first (never while they use AEDT). Net colours may not be set on AEDT 2026 R1 (warning only).
