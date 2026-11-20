# Contracts: edit_layout (013)

Board paths resolve with `core.edb.aedb_path` (`.aedb`, `.aedt`, `.aedb/edb.def`, quotes / spaces stripped) and EDB
opens with `core.edb.edb_session(path, cell or None, readonly, config.machine()["aedt_version"])` (closed on exit,
also on error). Lengths use `core.units.MM`.

## `run.region(board, bbox, layers=None, nets=None, cell="", images=True, log=None) -> dict`

| Input | Type | Unit | Valid | Default |
|---|---|---|---|---|
| board | str / PathLike | — | existing `.aedb` (or `.aedt` / `edb.def` next to it) | — |
| bbox | str `"x0,y0,x1,y1"` or list of 4 | mm | finite numbers, x0 < x1, y0 < y1 | — |
| layers / nets | list[str] / None | — | filters | None |
| cell | str | — | cell name ("" = first) | "" |

Output unchanged (`aedb`, `box`, `signal_layers`, `layers`, `padstacks`, `components`, `region_json`, `images`,
`seconds`). Board opened read-only, never saved. Writes `<board dir>/Ansys AEDT Copilot/layout_edit/_region/<time>/`.

Errors:
| Raised | When |
|---|---|
| CopilotInputError (`board`) | no `.aedb` folder — was RuntimeError "Không thấy thư mục .aedb" |
| CopilotInputError (`bbox`) | not 4 numbers or empty box — was ValueError / IndexError later |

Validation at entry: board path, bbox — before EDB opens.

## `run.edit(plan, log=None) -> dict`

| Input | Type | Valid |
|---|---|---|
| plan | dict, JSON text or path to a JSON file | object with `board` (as region), `ops` non-empty list, each `op` in `OPS`; `region` (optional) 4 numbers |

Output unchanged (`ok`, `aedb`, `source`, `out_dir`, `region`, `ops`, `checks`, `summary`, `images`, `seconds`,
`total_s`, `changes_md`; on op error `ok: false`, copy removed). Original board never opened for write.

Errors:
| Raised | When |
|---|---|
| CopilotInputError (`plan`) | not an object / unreadable JSON |
| CopilotInputError (`board`) | no `.aedb` folder |
| CopilotInputError (`ops`, `op`) | empty, or op not supported — now raised BEFORE the board is copied (was after) |
| CopilotInputError (`region`) | not 4 numbers |
| RuntimeError | output folder exists / equals source (unchanged) |

## `run.defaults() -> dict`

Unchanged: `{key: float(default)}` from `core.config.template_rows(template_path("layout_edit"))`.

## Removed private helpers

`run._aedb`, `run._open`, `extract.MM`, `ops.MM` (local constants) → core. `extract.MM` / `ops.MM` names stay
importable (re-export of `core.units.MM`).
