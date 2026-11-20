# Research — 042 merge into a copy of the board

All runs on COPIES (scratchpad `val\`), AEDT 2026.1 non-graphical, validation = `oDesign.ValidateCircuit()` (the
3D Layout "Validation Check"), each run limited to 7–10 min then the AEDT process started by the run is killed.

## R1 Why the 5.0.0 merged project hangs

| Run | Result |
|---|---|
| board1 sample design CPHY_U26_U14 (user's) | OK 28 s |
| board1 CPHY_U14_U26 channel (5.3.0) | OK 29 s |
| board1 merged project (5.3.0, new empty project) | OK 26 s |
| BOARDA PCIE_HSA_HSB channel design (5.0.0) | OK 31 s (warnings: series C elements > λ/20) |
| BOARDA merged project (5.0.0, new empty project) | HANG > 600 s |
| merged copy + materials of the channel imported | HANG |
| merged copy, 4 series C (0 pins) deleted from EDB | HANG |
| merged copy, 4 series C recreated from their orphan pins + 0 Ω | HANG |
| merged copy, solder balls off | HANG |
| merged copy, 4 series C AND their 8 pins deleted | OK 23 s |
| channel copy with series C rebuilt as `C0402_cut`, merged into a NEW project by `merge_designs` | C 0 pins again |

Decision: the hang comes from pasting a design with series RLC parts into an EMPTY project: the parts lose their pins
(pins stay in the layout without a component, part name empty). Repairing in the merged design does not help.

## R2 Merge into a copy of the board project

`merge_designs` (old mode, target = copy of `BOARDA_PN00000000-A_01_EDB_20260915.aedt` + `edb.def`):
designs after merge `PCIE_HSA2HSB_L0L1`, `main`, `PCIE_U14_J25`; C951 / C958 / C959 / C1015 2 pins each, part
`C0402` (= channel); stackup merged design == channel (31 layers); Validation Check OK 32.5 s.

Decision: target = copy of the board project (what the user asked). Alternatives rejected: repair in place (R1: does
not help), rebuild series parts with a new definition (R1: still lost).

## R3 What to copy

Board given as `.aedb` (BOARDA: `board` = `.aedb`, `workspace` = the `.aedt` beside it, 153 MB `edb.def` +
`edb.def.bak`). Copy: `<stem>.aedt` → `<request>/<request_id>.aedt`, `<stem>.aedb/edb.def` (+ other files except
`edb.def.tmp`, `edb.def+`, `*.lock`, `stride/`, `edb.def.bak`) → `<request>/<request_id>.aedb`. AEDT binds a 3D Layout
project to `<same stem>.aedb`. Board with no `.aedt` beside it: copy the `.aedb`, open it in AEDT (it creates the
project file), save, then merge.

## R4 Stackup data

PyEDB per design: `stackup.layers` (name, type, material, fill_material, thickness m) in order; `materials[name]`
(permittivity, loss_tangent / dielectric_loss_tangent, conductivity). The cut keeps the stackup (cutout copies the
cell), so the board stackup read once at the cut (stage1) is the reference.
