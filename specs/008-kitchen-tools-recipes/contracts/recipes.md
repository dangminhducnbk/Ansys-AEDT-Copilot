# Contracts: `aedt_copilot.kitchen.recipes`

Tests: `tests/unit/test_kitchen.py` (temp personal folder via env `AEDT_COPILOT_RECIPES`).

## `team_dir() -> str` / `personal_dir() -> str`

`<repo>/recipes`; `env AEDT_COPILOT_RECIPES` or `~/.aedt_copilot/recipes` (created on first save only).

## `parse(text, source, path="") -> dict`

| Input | Type | Valid |
|---|---|---|
| text | str | `---\n<yaml>\n---\n<body>` |
| source | str | `team` \| `personal` |

Output: recipe (data-model) incl. `broken`. Errors (CopilotInputError naming the field): no front matter / bad YAML
(`front matter`), `name` not a slug (`name`), `steps` not a list of mappings with `utensil` (`steps`), neither steps nor
guide (`steps`), `checkpoint` not bool (`steps[i].checkpoint`).

## `list_recipes() -> list[dict]`

Every `*.md` of both folders, team first, then personal, each sorted by name. A file that fails `parse` is listed with
`error` (never raises). Same name in both → two entries.

## `get(name, source="") -> dict`

Full recipe + body. `source` "" and the name exists in both → CopilotInputError(`source`, `team or personal`, name).
Unknown name → CopilotInputError(`name`, closest names).

## `save(name, markdown, overwrite=False) -> dict`

Writes `<personal_dir>/<name>.md` (UTF-8) after `parse(markdown, "personal")` and `name` == front matter name.
Existing file and not `overwrite` → CopilotInputError(`name`, `new name or overwrite=true`). Never writes the team
folder. Output: the parsed recipe + `path`.

## `list_md(entries) -> str`

`| Recipe | Source | Steps | Checkpoints | Description | Status |` (status `ok`, `broken: <utensils>`, `error: ...`).
