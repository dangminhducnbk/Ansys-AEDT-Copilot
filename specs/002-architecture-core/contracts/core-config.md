# Contracts: `aedt_copilot.core.config`

Constants: `ROOT` (repo root, abs str), `TEMPLATES_DIR` (`<ROOT>/templates`), `CONFIG_FILE` (`<ROOT>/config.yaml`),
`TEMPLATES = {"autocut": "autocut_template.csv", "pidc": "pidc_template.csv", "layout_edit": "layout_edit_template.csv"}`.
Imports: stdlib + PyYAML only. Tests: `tests/unit/test_core_config.py` (golden JSON captured from pre-002 code).

## `template_path(name) -> str`

| Input | Type | Valid |
|---|---|---|
| name | str | key of `TEMPLATES` |

Output: absolute path in `TEMPLATES_DIR` (existence not checked). Errors: CopilotInputError(`name`, `one of ...`).

## `template_rows(path) -> list[dict]`

Purpose: read any team-defaults CSV by header name (data-model.md TemplateRow).

| Input | Type | Valid |
|---|---|---|
| path | str \| PathLike | existing file |

Preconditions: UTF-8 (BOM allowed); first non-comment, non-blank line = header containing `Key` and `Default`.

Output: TemplateRow dicts in file order, deep copy. For `autocut_template.csv` EQUAL to pre-002
`cut_board.config.template_rows()` (golden). Cached by (abs path, mtime).

Side effects: none. Errors: missing file → CopilotInputError(`template`, `existing file`, path); header without
`Key` or `Default` → CopilotInputError(`template header`, `columns Key and Default`, header).

## `coerce(value, typ) -> None | bool | int | float | str | list`

Purpose: cell / default text → Python value. Moved verbatim from `cut_board.config.coerce`.

| Input | Type | Valid |
|---|---|---|
| value | any | — |
| typ | str | `num`, `bool`, `text`, `list` |

Output: None for None / blank; bool from `true/yes/1/on/x` and `false/no/0/off`; `num` → int when integral and
written without `.` / `e`, else float; `list` → split on `,` / `;`, int where possible; `text` → stripped str.

Errors: bad bool / num text → `ValueError` with TODAY's message (deviation, plan Complexity Tracking);
`typ` not one of the 4 → CopilotInputError(`typ`, `one of num, bool, text, list`, typ).

## `machine(config_file=CONFIG_FILE) -> dict`

Purpose: per-PC config (data-model.md MachineConfig). Same result as pre-002 `cut_board.config.machine()`.

Preconditions: none (missing file allowed). Output: new dict per call. Side effects: none.
Errors: invalid YAML → `yaml.YAMLError` (unchanged).

## Re-exports kept (`aedt_copilot.cut_board.config`)

`ROOT`, `CONFIG_FILE`, `TEMPLATE_FILE`, `machine()`, `template_rows()` (no argument = autocut template), `coerce`,
`build_params(values)`, `defaults()` — signatures and results unchanged (contract = pre-002 behaviour).
