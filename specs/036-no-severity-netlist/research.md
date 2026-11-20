# Research: 036

Decisions taken by the agent while the user was asleep (2026-11-15), within the agreed 6 points.

| # | Decision | Rationale | Alternatives |
|---|---|---|---|
| R1 | Finding key `status` ("NOT OK" / "OK") replaces `severity` everywhere | One concept, readable in JSON; user: no classification at all | boolean `ok` (less readable in reports / JSON) |
| R2 | Former INFO cases are OK (ref plane change with GND via, via clearance, no stackup table / value) | They are within the rule's limit or not measurable; user: "trong ngưỡng → OK" | a third state "info" (rejected: it is a classification) |
| R3 | Counts = number of NOT OK points + NOT OK findings per check | Points are what the report lists; per-check numbers tell where | counts per section (report already shows them) |
| R4 | Review record SCHEMA 4 | Old records carry severities; reuse would leak them and bypass a fresh measure | migrate old records (risk of mixing) |
| R5 | Steering field `not ok when`; old field `severity` read for personal rules | Team files rewritten; personal rules keep working | hard break for personal rules |
| R6 | `answer_md` built by code in Vietnamese | Prose rule in the guide was not followed (3.0.0 test) | a guide template only (already failed) |
| R7 | Netlist formats detected by content, not extension | User file `BLOCK DIAGRAM - I2C.NET` is a full Protel netlist; Allegro export was `.txt` | by extension |
| R8 | Netlist parsed at `isim_start` into `netlist.json` (~ seconds) | One parse per request; trace / compare read JSON | parse on every trace |
| R9 | 2-pin parts compared without pin numbers | Orientation of C / R / L does not change the model; user rule | per-part list |
| R10 | Pins absent from the schematic = board only | PDF reading may miss pins (off-page); netlist may lack mechanical parts | difference (old behaviour, false questions) |
| R11 | `missing_on_board` with a netlist only for nets matching the trace patterns | A full-board netlist has every other net between the same two ends (power, sideband) | all nets (hundreds of false differences) |
| R12 | Design check: < 50 % of traced refdes in the netlist → refused | Wrong file (user sent a X100 netlist first) | warning only |
| R13 | pi_dc PASS / WARN / FAIL untouched | Different feature (current density verdicts are physical limits, not review severities) | rename too (out of scope) |

Netlist samples checked:
- BOARDA Protel 2.0 (Altium): 9 339 components, 4 084 nets; `PCIE_HSA2HSB_L0_P*` = C951-1, U14-AT54;
  `PCIE_HSA2HSB_L0_P` = C951-2, J25-C19. Component blocks: `[`, DESIGNATOR, rd, FOOTPRINT, fp, PARTTYPE, pt, then
  key / value lines, `]`. Net blocks: `(`, name, `rd-pin <text>` lines, `)`.
- VendorX X100 Allegro: header `(NETLIST)`, `(FOR DRAWING: …brd)`, `$PACKAGES` lines `fp ! 'part' ! 'value' ; refs ,`,
  `$NETS` lines `NAME ; rd.pin … ,`, sections repeated after `$A_PROPERTIES`.
