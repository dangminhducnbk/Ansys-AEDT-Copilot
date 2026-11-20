# Contracts: `aedt_copilot.core.validate`

All functions: pure (except `require_path`, which reads the file system), no side effects, raise
`CopilotInputError(name, expected, got)`, return the cleaned value. `name` must be a non-empty str.
Tests: `tests/unit/test_core_validate.py`.

## `require_type(name, value, types) -> value`

| Input | Type | Valid |
|---|---|---|
| value | any | — |
| types | type \| tuple[type, ...] | — |

Errors: value not an instance of `types` → expected `"<type names>"`. `bool` is NOT accepted where `int` / `float`
is asked unless `bool` is listed.

## `require_number(name, value, lo=None, hi=None, lo_incl=True, hi_incl=True) -> int | float`

| Input | Type | Valid | Default |
|---|---|---|---|
| value | int \| float (not bool) | finite (not NaN / inf) | — |
| lo, hi | int \| float \| None | lo <= hi when both given | None (no bound) |
| lo_incl, hi_incl | bool | — | True |

Errors: not a number / bool / NaN / inf → expected `"number"`; outside a bound → expected e.g. `">= 0"`,
`"> 0 and <= 10"`. Returns the value unchanged (type kept).

## `require_int(name, value, lo=None, hi=None) -> int`

As `require_number` with inclusive bounds; value must be `int` (not bool); `3.0` rejected → expected `"integer"`.

## `require_choice(name, value, choices) -> value`

`choices`: non-empty iterable. Errors: value not in choices → expected `"one of <c1>, <c2>, ..."` (given order).

## `require_text(name, value, pattern=None, forbidden="") -> str`

Returns `value.strip()`. Errors: not str / empty after strip → expected `"non-empty text"`; `pattern` (regex,
full match) fails → expected `"text matching <pattern>"`; contains any char of `forbidden` → expected
`"text without <chars>"`.

## `require_path(name, path, kind="any") -> str`

| Input | Type | Valid | Default |
|---|---|---|---|
| path | str \| os.PathLike | non-empty; surrounding spaces / double quotes stripped | — |
| kind | str | `any`, `file`, `dir` | `any` |

Output: absolute normalised path (str). Errors: empty → `"non-empty path"`; missing → `"existing file"`,
`"existing folder"` or `"existing path"`; bad `kind` → CopilotInputError on `kind`.
