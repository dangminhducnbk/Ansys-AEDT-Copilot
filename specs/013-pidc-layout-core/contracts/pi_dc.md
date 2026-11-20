# Contracts: pi_dc (013)

## Skill entry (registry `aedt_copilot.pi_dc.skills`)

Every module in `pi_dc/skills/` (not starting with `_`) is a skill, loaded by `core.registry.load(..., ("NAME",
"ORDER", "TITLE", "run"))`.

| Attribute | Type | Meaning |
|---|---|---|
| NAME | str | unique; result file `results/<NAME>.json`; guide `guides/pidc_<NAME>.md` |
| ORDER | int | position in the default run (10 current_density, 20 via_current, 30 voltage_distribution, 40 power_tree) |
| TITLE | str | report heading |
| NEEDS_EXPORT | bool (optional, default True) | skill needs `raw/manifest.json` from `pidc_export` |
| run(ctx, log=print, **kw) -> dict | callable | result with `verdict`, `counts`; saved by the skill |

Errors: `RegistryError` at import of `workflow` when a skill lacks an attribute or names clash.

Tests: `tests/unit/test_pidc_layout_core_013.py` (table, order, export set equal pre-013 golden).

## `workflow.SKILLS: dict[str, module]`, `workflow.DEFAULT: list[str]`, `workflow.NEEDS_EXPORT: set[str]`

Built from the registry. Values equal pre-013: keys / DEFAULT `current_density, via_current, voltage_distribution,
power_tree`; NEEDS_EXPORT the first three.

## `workflow.run_skill(folder, name, sim="", log=print, **kw) -> dict`

| Input | Type | Valid | Default |
|---|---|---|---|
| folder | str / PathLike | existing folder | — |
| name | str | one of `SKILLS` | — |
| sim | str | DC sim name in the `.siw` ("" = the only one) | "" |
| kw | — | skill options (power_tree: `voltage`, `current`); None values dropped | — |

Output: the skill result dict (unchanged). Side effects: `<folder>/Ansys AEDT Copilot/` results / images (unchanged).

Errors:
| Raised | When |
|---|---|
| CopilotInputError (`name`) | unknown skill — was RuntimeError "Không có skill" |
| CopilotInputError (`folder`) | folder missing — was a later error in `Ctx` |
| RuntimeError | no `.siw` / sim / export missing (unchanged) |

Validation at entry: name, folder — before reading the project.

## `workflow.run(folder, sim="", skills=None, skip_export=False, log=print) -> dict`

| Input | Type | Valid | Default |
|---|---|---|---|
| folder | str / PathLike | existing folder | — |
| skills | list[str] / None | each one of `SKILLS`; None = `DEFAULT` | None |
| skip_export | bool | — | False |

Output unchanged (`export`, per skill `{verdict, counts}`, `report`, `seconds`).

Errors: CopilotInputError (`folder`, `skills`) before export starts; others unchanged.

## `common.TEMPLATE`, `common.params() -> dict`

`TEMPLATE` = `core.config.template_path("pidc")` as `Path` (same file). `params()` values unchanged (golden).
