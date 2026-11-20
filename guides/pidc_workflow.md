<!-- PI-DC workflow controller: report of a SOLVED SIwave DC-IR folder (works in place, never saves) - export 6x SIwave images, run the PI-DC skills (current density, via current, ...), build the HTML/Markdown report. Separate from interface simulation. Read FIRST for any PI-DC request. -->
# PI-DC WORKFLOW — CONTROLLER

## 1. MISSION
Turn a solved SIwave DC-IR simulation into a slide-ready PI-DC report: per power net × layer current density and per via current, with verdicts, images and text.
Independent of interface simulation (no cut guides, no cut gates).

## 2. RULES OF ENGAGEMENT
- Input = a FOLDER given by the user that contains the solved `.siw` and its `.siwaveresults/`. Work DIRECTLY in that folder.
- NEVER copy the project. NEVER save the project. (SIwave itself rewrites `.siwaveresults/dcReport.cfg` on export — expected.)
- All output goes to `<folder>/Ansys AEDT Copilot/` (name: `pidc.output_folder` in `templates/pidc_template.csv`).
- No confirmation needed before opening SIwave: the user guarantees the working environment. SIwave opens a window (needs a desktop with GPU).
- Use only this server's `pidc_*` tools. Do not compute results yourself. Do not open the board with other tools.
- GND / return nets are never rated.
- Reply in the user's language; the report itself is English.

## 3. EXECUTION
| Step | Action | Tool |
|---|---|---|
| 0 | Get the folder path. If several solved `.siw` or several DC sims: ask which (`sim_name`). | — |
| 1 | Export SIwave DC report images at 6x (`EXPORT_REPORT_IMAGE_WIDTH/HEIGHT`), filters per job, via-current plots, element data. ~15–25 min → poll `task_result` every 60 s. | `pidc_export(folder, sim_name)` |
| 2 | Check `missing_jobs`: `ALL_NETS` or `ALL_POWER` missing → STOP, report (GPU/desktop problem, see `raw/export_*_log.txt`). A per-net job missing → its pairs are PENDING (never PASS). Check `image_size` (expect 10000×6000; smaller = env vars not honoured → say so). Report `warnings` (e.g. `pidc.image_width` > 10000: SIwave caps it). Error "no power/ground net list" → STOP, tell the user to mark the nets in SIwave and re-run. | — |
| 3 | Run every skill in SKILLS LIST (section 4), in order. Read each skill guide first. | `pidc_<skill>(folder, sim_name)` |
| 4 | Build the report. | `pidc_report(folder, sim_name)` |

Older exports without voltage plots: the voltage skill reports PENDING; export only the ALL_POWER voltage job with
`python -m aedt_copilot pidc-export --dir "<folder>" --voltage-only` (~2 min) instead of a full export.
| 5 | Hand-off (section 6). | — |

Re-running analysis or report only (images already exported): skip step 1. Command line equivalent (no Claude):
`python -m aedt_copilot pidc --dir "<folder>" [--sim "<DC sim>"] [--skills current_density,via_current,voltage_distribution,power_tree] [--skip-export]`;
one skill: `python -m aedt_copilot pidc-skill --dir "<folder>" --name power_tree [--pt-voltage 3] [--pt-current 100]`.

## 4. SKILLS LIST
| Order | Skill | Guide | Tool | Result |
|---|---|---|---|---|
| 1 | current_density | `get_guide("pidc_current_density")` | `pidc_current_density` | `results/current_density.json`, `images/CD_*.png` |
| 2 | via_current | `get_guide("pidc_via_current")` | `pidc_via_current` | `results/via_current.json`, `images/VIA_*.png` |
| 3 | voltage_distribution | `get_guide("pidc_voltage_distribution")` | `pidc_voltage_distribution` | `results/voltage_distribution.json`, `images/VLT_ALL_POWER.png` (info only) |
| 4 | power_tree | `get_guide("pidc_power_tree")` | `pidc_power_tree` (own SIwave run, ~1 min; voltage/current only if the user asks) | `results/power_tree.json`, `images/POWER_TREE.png` |

### Adding a skill (developer)
1. Module `aedt_copilot/pi_dc/skills/<name>.py` with `NAME`, `TITLE`, `run(ctx, log) -> dict` (save with `ctx.save_result`, images to `ctx.images`).
2. Register it in `aedt_copilot/pi_dc/workflow.py` (`SKILLS`, `DEFAULT`).
3. Guide `guides/pidc_<name>.md` (first line `<!-- description -->`), MCP tool in `mcp_server/server.py`, a row in the table above, a section in `pi_dc/report.py`.
4. Thresholds in `templates/pidc_template.csv` (`pidc.<name>_*`).

## 5. OUTPUT (`<folder>/Ansys AEDT Copilot/`)
| Path | Content | Reuse |
|---|---|---|
| `PIDC_report_<time>.html` | English report: header, Summary (suspect points only), DC IR, current density, via current, reference (collapsed) | open in a browser |
| `images/*.png` | every figure, 2800×1400, colour bar left, clear names (`CD_ALL_POWER_<layer>.png`, `CD_<net>_<layer>.png`, `VIA_POWER_TOP.png`, ...) | drag into PowerPoint |
| `report.md`, `summary.json`, `current_density.csv`, `vias.csv` | all text and numbers | copy to slides / scripts |
| `results/*.json` | raw skill results | re-render |
| `raw/` | SIwave 6x export (`reports/<job>/report_files`), filters, export scripts and logs, `manifest.json`, `element_data/Vias.txt` | `--skip-export` |

## 6. HAND-OFF
Send the HTML path and the images folder. Summarize:
- Verdicts: current density, via current.
- Every FAIL / WARN / PENDING point: net, layer (or via x, y), value, limit, util.
- Worst current-density region per layer of ALL_POWER (label value) and worst 5 vias (net, x/y mm, I, I_cap, util).
- Voltage: VRM output voltage(s) and the 5 lowest load Vmin (refdes.pin, rail, mV, drop) — information only.
- Power tree: settings used (current A, voltage %/V), FAIL count and every failing load (rail, V, drop %).
- Count of single-point colour-bar peaks above the limit and of pin-node artefacts on component pads (INFO only — SIwave injects pin current at a node; never report them as violations).
State caveats: values quantised to 1/14 of each colour bar; window average depends on `pidc.cd_window_mm`.
