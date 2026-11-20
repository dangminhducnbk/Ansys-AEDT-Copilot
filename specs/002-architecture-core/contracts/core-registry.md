# Contracts: `aedt_copilot.core.registry`

Tests: `tests/unit/test_core_registry.py` with throw-away packages in a temp dir on `sys.path`.

## Entry interface (all registries: review checks 003, cleanup 005, port handlers 006 / 011-013, PI-DC skills 009, layout-edit ops / checks 009)

| Attribute | Type | Valid |
|---|---|---|
| `NAME` | str | non-empty, unique in the package |
| `ORDER` | int (not bool) | run order ascending, ties by NAME |
| `run` | callable | signature fixed by the contract of the feature that owns the registry |

A registry may require extra attributes (e.g. `TITLE`) via `required`. Modules whose name starts with `_` are
helpers, never entries. Sub-packages are not scanned. New rule = new file; no existing file is edited.

## `load(package, required=("NAME", "ORDER", "run")) -> list[module]`

| Input | Type | Valid |
|---|---|---|
| package | str (dotted name) \| module | importable package (has `__path__`) |
| required | tuple[str, ...] | contains `NAME`, `ORDER`, `run` |

Output: entry modules sorted by `(ORDER, NAME)`; empty list if none. Side effects: imports the modules.

Errors: not a package → CopilotInputError(`package`, `importable package`, value); module import fails →
RegistryError naming the module (original error chained); missing attribute / wrong type → RegistryError
(`<pkg>.<mod>: missing ORDER`, `ORDER must be int`); duplicate NAME → RegistryError naming both modules.

## `by_name(entries) -> dict[str, module]`

Input: list from `load`. Output: `{NAME: module}` in the same order. Errors: duplicate NAME → RegistryError.
