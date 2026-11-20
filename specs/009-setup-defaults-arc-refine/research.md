# Research: setup defaults

## R1 — What a run stores today

`user_settings.json` → `interfaces.<name>.values` = only keys the engineer entered (board1 requests 0.7.0 / 0.9.0 /
0.11.0: 3-4 keys, sweep only). `tool_version` is the version of the LAST save of the document. Template defaults are
read at apply time. → Changing a default changes every later re-cut / re-apply of old runs unless the old default is
recorded somewhere.

## R2 — Options

| Option | Result |
|---|---|
| A. Only change the template | re-cut of a 0.7.x run silently uses 30; re-apply of an old design rewrites arc 30 → violates FR-005 / FR-007 |
| B. History table + freeze on write (chosen) | old runs resolved by their tool_version; from now on the effective value is stored with the run; one-time fill when an old document is first written by a new version (before its tool_version is overwritten) |
| C. Read the arc step from the existing design on re-apply | exact for re-apply, but not for re-cut (no design) and not shown in the GATE B table before apply |

## R3 — Max refinement per pass

Template `setup.max_refine_per_pass` = 10 (int); `cutter.apply_setup` sets `adaptive_settings.max_refine_per_pass`;
`apply.read_setup` reads it back; engineer confirmed AEDT 2026 R1 shows 10 %. Missing: range validation → add to
`build_params` (whole number 1..100).

## R4 — Version

Default change + validation = patch → 0.11.1. `HISTORY` arc entry `(0, 11, 1): 30`.
