# Research (033)

All open points were decided in the spec Clarifications and the plan "Decided by agent" table. Technical findings:

| Topic | Decision | Rationale | Alternatives |
|---|---|---|---|
| Where routing data comes from | `_review_edb` builds `ch["routing"]` from the already collected paths / vias / pins + via rows + chains + `Board` (elevations, reference layers) | one measurement run (FR-001, FR-008); snapshot facade already serves all of it | mock wrapped `RV._collect` / `RV.lengths` (monkey-patch) |
| Pin pad sizes | `padstack_instance.bounding_box` for pins of the channel nets (snapshot `pin_bbox`) | real pads (FR-008) | padstack-name guess (`c40`, `r45_50`) of the mock |
| Component body | `edb.components.instances[ref].bounding_box` (snapshot `comps bbox`, schema 2) | true scale | none |
| H for serpentine | min positive dielectric distance between the trace layer and its reference planes (`Board.ref_layers`, `elev`) | same as mock (`_collect` wrapper) | stackup table (not always present) |
| Serpentine detection | port of mock `serp.find` (10 µm samples, bump = centre distance > base + 1.5W, < 2 mm, spacing < 2 mm, height ratio 0.7–1.43, ≥ 2 bumps, 1 mm exclusion around pair pins / vias) | user accepted mock results (10 on SERLINK) | — |
| Pair gap vs serpentine | drop raw stretches whose midpoint is inside a same-pair serpentine box + 0.5 mm | FR-010 | drop merged findings (mock) |
| Text source | steering parts `Report`, `Issue`, `Recommendation` with `{placeholders}` | FR-004 single source (031) | sentences in Python (mock `short()`) |
| Tabs | one HTML, `<div class='tabp'>` per channel, ids prefixed `t<k>-`, one script block | FR-001 | concatenating three reports (mock `tabs.py`) |
| Zoom | inline JS on `svg.tv` (lock button, wheel at cursor, drag, double-click reset, `text[data-fs]` keeps screen size) | US2-2 | external library (not allowed: self-contained) |
