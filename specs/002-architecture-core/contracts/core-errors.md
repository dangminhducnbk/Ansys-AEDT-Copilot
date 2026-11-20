# Contracts: `aedt_copilot.core.errors`

## `CopilotInputError(name, expected, got=MISSING)` — class, subclass of `ValueError`

Purpose: the one error for a bad input to a public function (Principle VII).

| Input | Type | Valid | Default |
|---|---|---|---|
| name | str | non-empty: input name as the caller sees it (`sweep.stop_ghz`, `board`) | — |
| expected | str | non-empty: expected value / range (`> 0`, `one of a, b`, `existing folder`) | — |
| got | any | value received; omitted = not shown | MISSING |

Output: exception; attributes `.name`, `.expected`, `.got`; `str(e)` = `"<name>: expected <expected>, got <got!r>"`
(without `, got ...` when `got` omitted).

Side effects: none. Errors: `TypeError` if `name` or `expected` is not a non-empty str (programming error).

Tests: `tests/unit/test_core_errors.py` (message format, `isinstance(e, ValueError)`, attributes).

## `RegistryError` — class, subclass of `RuntimeError`

Purpose: a registry package is malformed (duplicate `NAME`, missing attribute, import failure).
Message names the package, the module and the problem. Tests: `tests/unit/test_core_registry.py`.
