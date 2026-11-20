# Feature Specification: Cut config up front (HTML), one approval, folder per channel

**Feature Branch**: `main` (spec folder `specs/038-cut-config-html`)

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Khi nhận yêu cầu cut từ người dùng, cần phải có bảng hiện lên để người dùng config các thông
số trước và sau khi cut. Ví dụ vùng cut là bao nhiêu (0.06 hay một số khác, mặc định 0.06), các settings khác cũng config
từ đầu từ đây. Sau đó, tool đưa ra vùng cut dự kiến và layout review file. Nếu người dùng đồng ý thì bắt đầu cut. File
thông số cut, settings tôi muốn đổi lại là file HTML. Bạn cứ tạo ra một file mẫu để tôi xem và review trước khi code.
Các channel cần có thư mục riêng để chứa gồm file edb, aedt, file review và file config. Thư mục tổng sẽ là thư mục chứa
file ansys aedt và edb sau khi đã merge toàn bộ các channel cần cut."

## Context (today, 4.1.0)

| Step today | What the user sees |
|---|---|
| trace → review → cut preview → GATE A | cut settings form (022) + preview + review HTML; one go |
| cut → end check → GATE B | settings form (005) for ports / solder ball / setup / sweep / airbox, a second go |
| apply → GATE C merge | designs pasted into the user's own workspace `.aedt` (backup first) |
| files | `<request>/<channel>/` holds state.json, stage1/, final/<channel>.aedb + .aedt, preview/, logs; agreed values in `<request>/user_settings.json` (JSON); review HTML in `<board dir>/autocut/` |

The user wants ALL settings asked once, at the start, in one table; one approval after the cut preview + review; config
kept as a readable HTML file; and a clean folder per channel plus one merged project for the whole request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure every setting before the cut (Priority: P1)

The engineer asks to cut one or more channels. Right after the channel content (nets, ends, series parts) is known, the
tool shows ONE config table with every setting of the cut and of the simulation design: cut region expansion (default
0.06), extent options, GND cleanup, series parts, ports, solder balls, HFSS setup, sweep, airbox. One tab per channel.
Every value is pre-filled from the team defaults except the mandatory sweep start / stop / step. The engineer edits what
they want and confirms the table once.

**Why this priority**: it removes the second settings round (GATE B) and makes the cut region size a decision the user
takes before anything is cut.

**Independent Test**: start a request for 2 channels, trace them, open the config table: both tabs show all settings with
team defaults, expansion 0.06, sweep fields empty; set expansion 0.08 on one channel and a sweep on both; the tool accepts
and stores the values; invalid values (sweep start ≥ stop, expansion ≤ 0) are refused with the row named.

**Acceptance Scenarios**:

1. **Given** traced channels, **When** the tool presents the config, **Then** one table per channel lists every
   channel-scope setting with value, default, unit and description, and values differing from the default are marked.
2. **Given** the table, **When** the user leaves a mandatory sweep field empty or breaks a rule, **Then** the tool refuses
   and names the channel + setting; nothing is cut.
3. **Given** the user changes a value on one tab, **When** they choose "apply to all channels", **Then** every tab gets
   the value.

---

### User Story 2 - Preview + review, then one go cuts and builds the designs (Priority: P1)

After the user says the config is done ("xong"), the tool computes the predicted cut region WITH the configured expansion and writes the
layout review HTML. It shows both (image + file path + one question). On the user's go the tool cuts, checks the ends and
builds the simulation design (ports, solder balls, setup, sweep, airbox) with the configured values, without a second
settings question.

**Why this priority**: one decision point instead of two; the cut region the user approves is the one that is cut.

**Independent Test**: confirm the config with expansion 0.08, check that the preview region equals the region of a cut
with 0.08; give the go; the channel design is produced with the configured sweep and no further settings question is
asked (unless an end needs a decision, see edge cases).

**Acceptance Scenarios**:

1. **Given** a confirmed config, **When** the preview is shown, **Then** it is computed from that config (changing the
   expansion changes the preview) and the review HTML path is given.
2. **Given** preview + review shown, **When** the user gives the go, **Then** cut + end check + design build run with the
   confirmed values and the result reports the values used.
3. **Given** the user changes the config after the preview, **When** they ask to cut, **Then** the tool refuses until a
   new preview of the changed config is shown and approved.
4. **Given** the server, **When** a cut is requested without an approval bound to the current config + review + preview,
   **Then** it refuses (gate locked in code, Principle I).

---

### User Story 3 - Config file in HTML (Priority: P2)

The agreed settings of each channel are kept as an HTML file the engineer can open in a browser: readable table grouped
by section, changed values highlighted, who / when approved, links to the review HTML, preview image and the channel
design. The tool can read the values back from this file for a re-cut "như lần trước".

**Why this priority**: the user reads and archives settings; JSON is not readable for them.

**Independent Test**: after an approval, open `<channel>/config.html` in a browser: all values shown, approval time,
links work; a re-cut from this request reuses exactly these values.

**Acceptance Scenarios**:

1. **Given** an approved channel, **When** the user opens its config HTML, **Then** every setting value, its default and
   unit are shown and changed values are visibly marked.
2. **Given** a config HTML, **When** a re-cut "like last time" is requested, **Then** the values used are the ones in
   that file (no re-typing).
3. **Given** a request made before this feature (only `user_settings.json`), **When** a re-cut is requested, **Then** it
   still works (old files read).

---

### User Story 4 - One folder per channel, one merged project per request (Priority: P2)

Each channel has its own folder holding its EDB, its AEDT project, its review HTML and its config HTML. The request
folder ("thư mục tổng") holds the AEDT project + EDB with all channels of the request merged as designs.

**Why this priority**: the user finds every file of a channel in one place and hands one merged project to simulation.

**Independent Test**: cut 2 channels and merge: the request folder lists one `.aedt` + `.aedb` with 2 designs and one
folder per channel with exactly `<channel>.aedb`, `<channel>.aedt`, review HTML, config HTML (internal working files in
a separate sub-folder).

**Acceptance Scenarios**:

1. **Given** a finished channel, **When** the user opens its folder, **Then** the top level shows the EDB, the AEDT
   project, `review.html` and `config.html`; working files (state, stage, logs, preview images) are in a sub-folder.
2. **Given** all channels finished, **When** the merge runs (on the user's go), **Then** the request folder contains one
   project + EDB with one design per channel; name clashes get `_v2`, nothing is overwritten.

---

### Edge Cases

- An end needs a decision found only after the cut (no-GND end, unusual end, connector override): the run stops at that
  channel and asks only that question; the other settings are not asked again.
- The board changes (edb.def touched) between preview and go: the approval is out of date, preview + review re-run.
- The user edits the config HTML by hand outside the flow: values are validated again before use; a broken file is
  refused with the row named, never silently replaced by defaults.
- The end GND rule (022) grows one end beyond the configured expansion: the preview shows the grown end and the config
  HTML records both the configured value and the per-end factor actually used.
- Two channels with the same settings: "apply to all" keeps them equal; a channel later changed alone is marked.
- A channel already cut / merged in this request is re-configured: a new run is a new version; the old channel folder
  is moved aside (renamed), never deleted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: After the content of the channels is known (trace), the tool MUST present one config table covering every
  channel-scope setting of the team template (cut, cleanup, series, port, solder ball, setup, sweep, airbox), one tab per
  channel, pre-filled with team defaults; sweep start / stop / step mandatory and empty.
- **FR-002**: The cut region expansion MUST be in that table with default 0.06 and MUST be the value used by both the
  preview and the cut.
- **FR-003**: The tool MUST validate the whole table (type, range, sweep rule, unknown key) before any preview, and MUST
  name channel + setting for each error.
- **FR-004**: After a valid config, the tool MUST produce the predicted cut region (image) and the layout review HTML
  for each channel and ask ONE question.
- **FR-005**: The user's go on that question MUST be the single approval for cut + end check + design build of the
  approved channels; the server MUST refuse a cut / build without an approval bound to the current config, review and
  preview (any change → re-approve).
- **FR-006**: Questions that only the cut result can raise (end decisions) MUST still stop the channel and be asked; no
  other setting is asked after the approval.
- **FR-007**: The agreed config of each channel MUST be written as an HTML file in the channel folder: grouped table
  (setting, value, default, unit, description), changed values marked, approval time and the user's words, links to the
  review HTML, preview image and channel design. Values MUST be readable back by the tool from that file.
- **FR-008**: Each channel MUST have its own folder whose top level holds `<channel>.aedb`, `<channel>.aedt`, the review
  HTML and the config HTML; working files go to a sub-folder of it.
- **FR-009**: The request folder MUST hold, after the merge, one AEDT project + EDB containing one design per channel of
  the request. The merge writes ONLY this new project; the user's own workspace `.aedt` is never written (Q1 A).
- **FR-010**: The user fills the config in the HTML file itself: opened in the browser, edited, saved; then tells Claude
  "xong". The tool reads the saved file (Q2 A).
- **FR-011**: Order of questions (Q3, user's words): (1) after the HTML is filled Claude asks "đã config xong chưa?";
  (2) on "xong" the tool validates the file and shows the predicted cut region (+ review HTML) and asks "đồng ý cut
  không?"; (3) that go = the single approval for cut + end check + design build (FR-005 / FR-006).
- **FR-012**: Requests made before this feature (user_settings.json, old folder layout) MUST stay readable for status
  and re-cut; their files are not moved.
- **FR-014**: The HFSS setup part of the table MUST include the Solution Frequency mode as in the AEDT Adaptive
  Solutions dialog: Single (one frequency, default = sweep stop) or Multi-Frequencies (list of frequencies). No
  Broadband (user 2026-11-16). Only the fields of the chosen mode are shown and validated; the design gets that mode
  (user review of the mock, 2026-11-15). Default Single = today's behaviour. Details: FR-027.
- **FR-013**: Team defaults stay in `templates/autocut_template.csv` only (Principle III); the HTML stores the agreed
  values, never new defaults.

### Key Entities

- **Channel config**: the agreed values of one channel (setting key → value, default, unit), approval (time, user's
  words, review measured_at, preview key). Lives in `<channel>/config.html`.
- **Channel folder**: `<request>/<channel>/` = EDB, AEDT, review HTML, config HTML + working sub-folder.
- **Request folder** ("thư mục tổng"): `<request>/` = merged AEDT + EDB of all channels, request-level files.
- **Approval**: one per channel; bound to config hash + review record + preview; refused when any of them changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A 2-channel request needs ONE settings round and ONE go from the user before designs are built (today:
  two forms, two gos).
- **SC-002**: 100 % of cuts use the expansion shown in the approved preview (preview region = cut region, area diff 0).
- **SC-003**: Every channel folder, after the build, shows exactly 4 top-level items (EDB, AEDT, review, config) plus
  one working sub-folder.
- **SC-004**: A re-cut "như lần trước" from a 038 request reproduces the same settings with 0 values re-typed.
- **SC-005**: Cut numbers on the reference boards are unchanged with default settings (board1 regression, BOARDA PCIe
  check).

## Assumptions

- Applies to interface simulation (`isim_*`). Design tools (`design_*`) keep their own forms.
- Review HTML and config HTML are in English (team rule for HTML reports); chat answers stay Vietnamese.
- The request folder stays `<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/`.
- Merge still backs up and never overwrites (Principle II).
- A mock `mock/config_demo.html` is reviewed by the user before planning.

## Approved UI — "Auto Generate Extent" frame (user review 2026-11-15, mock v5)

Approved by the user ("Đồng ý với giao diện này") on `mock/config_demo_v5.html` (BOARDA / PCIE_HSA2HSB_L0L1) and
`mock/config_demo_v5_board1.html` (board1 / CPHY_U14_U26, U26 with one GND pad). Both are 8–14 MB, not committed;
`mock/config_demo_v4.html` (committed) has the same left column with a simpler picture.

- **FR-015** Frame title "Auto Generate Extent" (AEDT dialog name). Main fields only: Expansion type (Bounding box /
  Convex hull / Conformal, tiles with icons) and Expansion (large value, slider 0.02–0.20 step 0.01 with ticks, − / +).
- **FR-016** Below them a **Nets** table as in the AEDT cutout dialog: Net / Include / Clip at extents; channel nets
  Include, reference nets (GND) Include + Clip; changed rows marked.
- **FR-017** "Advanced" button inside the same frame opens the other cut settings (corner style, increments, unitless,
  reference nets, end step / margin, GND cleanup, series parts), pre-filled with team defaults. No description column;
  changed values marked with the default shown next to them. All text black (no grey text).
- **FR-018** Picture = the REAL layout of the board, every signal layer (copper minus voids, pads of vias / pins),
  colour by net class: signal nets pink, GND blue, other nets grey; the cut region outline on top. No label on the
  picture (no type / factor / area badge, no "grown by end GND rule" drawing); legend in a strip BELOW the picture.
- **FR-019** The cut region shown = the FINAL region that will be cut (AEDT expanded extent + end GND rule 022), for
  every step of the slider and every expansion type, pre-computed by AEDT and cached with the board snapshot, so the
  slider is instant. Measured on copies: BOARDA conformal 19 steps 57 s + hull 22 s + box 21 s after a 44 s open;
  board1 incl. end GND rule 78 + 20 + 21 s after 49 s.
- **FR-020** Layer panel at the right of the picture like the AEDT layer list: Active (radio, drawn on top / bright),
  layer name (• = channel routed on it), AEDT layer colour swatch, Visible checkbox (centred under "Visible"); first
  row "All layers" toggles every layer; buttons All / Routed / Active. Default visible = routed layers.
- **FR-021** Zoom / pan on the picture: wheel zooms at the cursor, drag pans, + / − / zoom % / Fit buttons,
  double-click = fit; the zoom stays when the slider, type or layers change.
- Picture data cost on copies (unoptimised mock scripts): reading the copper of 16 layers 3 min + shapes 5 min; the
  real code reads it from the layout snapshot. Target to measure in the plan: first build 1.5–2 min, then seconds.

## Approved UI — Component Model, Analysis Setup, Set HFSS Model Extents (user review 2026-11-16, mock v5)

Approved by the user ("Tôi đồng ý với giao diện này") on `mock/config_demo_v5.html` (not committed, 14 MB). Page text
is English only (no Vietnamese words such as "xong"; the bar reads "Check every frame, then Save and tell Claude you are
done."). Every field not listed below keeps the Ansys / team default and is not shown.

### Component Model (ports + solder balls, replaces separate port / solder ball settings)

- **FR-022** One frame "Component Model"; one bordered block per end component, title bar ABOVE the pictures
  `<refdes>:<part>_cut · <placement layer>`. Left: Top view + 3D view side by side, same height as the form (no empty
  space), symbol legend under the pictures of EACH block (Signal pad, GND pad kept, Pad removed by the cut, Solder ball,
  ⊕ Port). Right: form with 2 tabs; a tab with a changed field shows an orange dot.
- **FR-023** Tab "Component Info": Part name, Part type, Ref des, No. pins (signal + GND kept, of total) read-only;
  Die Properties: Type (None / Flip chip / Wire bond, default Flip chip), Orientation (Chip down / Chip up), Height (mm,
  editable only for Wire bond). Port Properties are NOT shown.
- **FR-024** Tab "Solder Ball Properties": Shape (Cylinder / Spheroid / None), Diameter = ratio 0–1 of the pad
  (slider step 0.01, default 0.95; shows "= x mm diameter (pad y mm)"), Mid diameter (read-only = diameter), Height
  (mm, default 0.2), Material (default solder); then Port location.
- **FR-025** Port location: round pads (BGA) → no choice, port at the pad centre. ANY non-round pad (IC / connector),
  with or without via-in-pad → choice Pad centre / Pad end (the end on the IC-body side); default Pad end. The pictures
  redraw the real port position of the choice.
- **FR-026** Pictures follow the form live: Top view = real pads (signal / GND kept / removed), balls, ports with pin
  numbers; 3D view = oblique view (drag rotate, wheel zoom, double-click reset; hint in the view label), pads, balls as
  cylinders / spheroids of the set diameter and height, ports, translucent body. The diameter slider redraws only the
  balls (smooth drag); slider = custom track (grey) + blue fill that always matches the knob.

### Analysis Setup (2 panels: Setup | Sweep)

- **FR-027** Setup, tabs like the AEDT setup dialog, only these fields:
  General / Adaptive Solutions: Solution Frequency Single / Multi-Frequencies. Single: Frequency + unit (default = sweep
  end, follows the sweep until edited), Maximum Number of Passes 30, Maximum Delta S 0.01 (no Use Matrix Convergence).
  Multi: table Frequency / Units / Max Delta S with Add / Remove, Maximum Number of Passes 10.
  Options: Maximum Refinement Per Pass 10 %, Order of Basis Functions (Zero / First / Second / Mixed, default Mixed).
  Advanced / Vias: Mesh as a 3D via (default on) + Number of sides for meshed vias (default 6) — NEW template rows.
  Solver / Port Options: Maximum Delta Zo 0.1 %.
- **FR-028** Sweep, tabs Edit Frequency Sweep / Interpolation: Sweep Type Interpolating / Discrete (Discrete hides the
  Interpolation tab); Use Q3D to solve DC point (default off — NEW template row); Frequency Sweeps table with several
  rows (Add Above / Add Below / Delete Selection), Distribution Linear Step / Linear Count / Log Scale (4th column
  label Step size / Count / Samples per decade), Start, End; points per row + "[N points defined]" total; wrong row
  marked ⚠ with the reason (start < end, 0 < step ≤ end − start, count ≥ 2, Log Scale start > 0). Default one row
  Linear Step 0 → sweep stop, step = template. Interpolation: Max Solutions 2500, Error Tolerance 0.1 %, Enforce
  Passivity (on) + Passivity Error Tolerance 1e-06, Enforce Causality (on).

### Set HFSS Model Extents (was "Airbox")

- **FR-029** Fields: Dielectric Type + Horizontal Padding (default Conformal, 0 — padding is a NEW template row);
  Airbox Type + Horizontal Padding (Conformal, 0.05); Vertical Positive Padding 0.2 + Sync (default on; off shows
  Negative Padding). Types: Bounding Box / Conformal / Convex Hull (no Polygon). Open region (radiation, 5 GHz) not
  shown, team default kept.
- **FR-030** Picture next to the fields, live: Top view (cut region of the Auto Generate Extent frame, signal copper,
  dielectric, airbox) + 3D oblique view (dielectric slab with traces at their layer height, airbox as a glass box
  ±Z). Legend names only: Cut region, Dielectric, Airbox, Signal nets. The mock converts padding as ratio × largest XY
  size of the model — to be checked against AEDT in the plan (preview only; AEDT builds the exact shape).

## Fixed workflow, questions and folder layout (user 2026-11-16)

The process is the SAME for every cut; the user always sees the same messages / questions in the same order.

- **FR-031** Steps (fixed order): (1) user gives board + interface; (2) tool: trace, snapshot, pre-computed cut regions,
  review — automatic; (3) tool writes the config HTML, message **M1**; (4) user edits, saves, answers; **Q1** only when
  the user did not already say done; (5) tool reads + validates the configs, errors → message **M2** (table channel /
  frame / field), back to (4); (6) final cut region picture + review file of EVERY channel in one answer, **Q2**;
  (7) cut + end check + design build, message **M3** (ports, GND vias, self-check per channel); (8) merge into the new
  project of the request folder — automatic (writes nothing of the user's). END. No question about a server run (the
  user asks for it separately; user 2026-11-16).
- **FR-032** Fixed texts, every one in Vietnamese AND English (Vietnamese line first, English line below; user
  2026-11-16). Tables (M2 / M3) once, English headers.
  | id | Vietnamese | English |
  |---|---|---|
  | M1 | File config: `<path>`. Mở, kiểm tra từng khung, Save rồi trả lời *xong*. | Config file: `<path>`. Open it, check every frame, Save, then reply *done*. |
  | Q1 | Bạn đã config xong chưa? | Have you finished the config? |
  | M2 | Config có lỗi, sửa rồi Save lại: | The config has errors, fix them and Save again: |
  | Q2 | Đồng ý cut không? | Do you agree to cut? |
  | M3 | Kết quả cut: | Cut result: |
  Answers accepted in both languages: "xong" / "done", "đồng ý" / "yes", "không" / "no". Every message / question is
  generated by the tool (`answer_md`); the guide makes Claude paste it verbatim, nothing added or removed. A test checks
  each step returns at most one question.
- **FR-033** Interface content (nets, ends, series R/C/L) is a read-only first frame **Content** of the config HTML,
  with a note field for corrections — no separate chat question (decision A).
- **FR-034** Unusual cases (end without GND pin, keep exposed pad, connector handling, ...) are choice fields in the
  config HTML, pre-filled with the proposal — chat keeps only Q1–Q2 (decision B).
- **FR-035** One Q2 "go" covers all channels of the request (decision D); merge needs no extra question (decision C).

Folder layout:

```
<board dir>/Ansys AEDT Copilot/
├─ snapshots/<board>/...                 board read once, shared (exists)
└─ interface_sim/<request_id>/           REQUEST folder
   ├─ <request_id>.aedt / .aedb          merged project of all channels
   ├─ request.md                         board, channels, step, times
   ├─ _work/                             request intermediates: backups, merge log, netlist.json
   └─ <channel folder>/                  CHANNEL folder (name typed by the user, FR-037)
      ├─ <channel>.aedt / .aedb
      ├─ review.html
      ├─ config.html
      └─ _work/                          stage1, preview, images, state.json, logs
```

- **FR-036** Top level of a channel folder = exactly edb, aedt, review, config + `_work/`; of the request folder =
  merged aedt + aedb, `request.md`, channel folders, `_work/`. A re-cut moves the previous files to
  `_work/history/<time>/` (never deleted). Requests made before 038 stay where they are and stay readable (FR-012).
  Request id = `<board>_<yyyymmdd_hhmmss>` (proposal accepted with the workflow; collision rule of 024 kept).
- **FR-037** Channel folder name: a REQUIRED field "Channel folder" above Save, one per channel, empty by default,
  shows the resulting path `…/interface_sim/<request_id>/<name>/`. Valid = not empty, no space or `< > : " / \ | ? * ;`,
  unique among the channels (case-insensitive). Save is refused while any channel is missing / invalid: the page
  switches to that channel, focuses the field and says "Not saved: fill the channel folder of …" (demo approved
  2026-11-16 in `mock/config_demo_v5.html`). The same name is the design name in the merged project.
