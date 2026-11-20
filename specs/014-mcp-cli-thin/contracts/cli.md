# Contracts: aedt_copilot.cli (014)

Entry layers only: parse arguments, call the package API, print JSON. No business logic.

## `cli.main(argv=None) -> int`

Purpose: CLI entry (`python -m aedt_copilot <cmd> ...`).

| Input | Type | Valid | Default |
|---|---|---|---|
| argv | list[str] / None | commands and flags of `parser.build_parser()` | `sys.argv[1:]` |

Output: exit code (0 ok; 2 input error of `isim` / `design` / `kitchen` / `review-measure`; `worker` returns its own
code). JSON printed to stdout (`indent=1`, `ensure_ascii=False`). AEDT resolved (`aedt_env.ensure()`) and one
`[aedt_env] {...}` line written to stderr before any handler runs.

Errors: argparse exits 2 on unknown command / missing required flag (unchanged). Handler exceptions propagate
(exit 1, traceback on stderr) as before.

## `cli.parser.build_parser() -> argparse.ArgumentParser`

Purpose: the full command tree (prog `aedt_copilot`). Commands / flags / defaults equal pre-014 (golden pre014.json).
Side effects: none.

## `cli.commands.COMMANDS: dict[str, Callable[[Namespace], int | None]]`

One handler per command; keys = parser commands. A handler imports its feature module lazily, calls the package API
and prints JSON. `None` return = 0.

## `cli.io.json_args(args) -> dict`

| Input | Type | Valid |
|---|---|---|
| args | Namespace with `args` (JSON text) and `args_file` (path) | file wins when given; empty = `{}` |

Errors: `CopilotInputError("args", "valid JSON", ...)` on bad JSON. File read errors propagate.

## `cli.io.input_error(ex) -> dict`

`{"ok": False, "error": str(ex), "input": ex.name, "expected": ex.expected}`. Pure.

## `cli.io.print_json(obj) -> None`

`json.dumps(obj, ensure_ascii=False, indent=1, default=str)` to stdout.

## `cli.tasks.run(args, wait=45) -> dict`

Purpose: run `python -m aedt_copilot <args>` in a subprocess (python from machine config, env from
`aedt_env.child_env()`, stdin closed, no window); wait up to `wait` s.

| Input | Type | Unit | Valid |
|---|---|---|---|
| args | list[str] | — | CLI arguments |
| wait | float | s | ≥ 0 |

Output: `result(tid)` — parsed JSON of stdout, or `{"pending": True, "task_id", "hint"}` when still running.
Side effects: `.tasks/<tid>.log` (stderr) under the repo root.

## `cli.tasks.result(task_id) -> dict`

Output: `{"error": "Không có task <id>"}` for an unknown id; pending dict while running; else stdout JSON (from the
first `{`), or `{"output": ...}`; `error_log` (last 4000 chars of the log) added when the exit code is not 0.

## `cli.tasks.args_file(stem, data) -> str`

Writes `.tasks/<stem>_<hex8>.json` (str written as is, other values `json.dump(ensure_ascii=False)`) and returns the
path. Used by the server to pass long arguments.

## `cli.docs.guides() -> dict[str, str]`

`{name: description}` of `guides/*.md` (description = first-line `<!-- ... -->`), sorted. Read only.

## `cli.docs.guide(topic="") -> dict`

`""` → `{"guides": guides()}`; unknown → `{"error": "Không có guide '<topic>'", "guides": ...}`; else
`{"topic", "version", "content"}`. Topic normalised: strip, lower, `-` → `_`, `.md` removed.

## `cli.docs.prompt_files() -> dict[str, str]`

`{name: description}` of `prompts/*.md` (front matter `description:`), sorted.

## `cli.docs.prompt_text(path, arguments="") -> str`

Prompt body without front matter, `$ARGUMENTS` replaced (empty → `(chưa có - hỏi người dùng)`). Re-read each call.

## `cli.docs.about() -> dict`

Static description of the tool (steps per feature, prompts, guides, requires, live `aedt` info). Same keys and text as
pre-014 `about` tool.

Tests: `tests/unit/test_thin_layers_014.py` (golden pre014), `test_design_tools.TestServerCli`.
