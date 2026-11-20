# Contract format (all features, Principle VII)

Every public function (called by another module, the CLI or the MCP server) has one contract block in
`specs/<feature>/contracts/<package>-<module>.md`. One file per module; one `##` block per function.
A registry (checks / handlers / skills) also has one contract for the entry interface (`NAME`, `ORDER`, `run`).

## Template

```markdown
## `module.function(arg1, arg2=default) -> ReturnType`

Purpose: one line.

| Input | Type | Unit | Valid range / values | Default |
|---|---|---|---|---|
| arg1 | float | mm | > 0 | — |
| arg2 | str | — | one of `a`, `b` | `a` |

Preconditions:
- what must be true before the call (files exist, EDB open, AEDT resolved, ...)

Output / postconditions:
- return value: shape and meaning
- state after the call (files written, EDB modified / saved or not, nothing written)

Side effects: files written / none. EDB saved: yes / no.

Errors:
| Raised | When | Message names |
|---|---|---|
| CopilotInputError | arg1 <= 0 | `arg1`, expected `> 0`, got value |
| RuntimeError | PyEDB fails | original message kept |

Validation at entry: which checks run before any AEDT / PyEDB call.

Tests: offline unit test file / regression that covers it.
```

## Rules

- Units always explicit (m in EDB-facing code, mm in templates / reports).
- Inputs validated at entry with `core.validate.*` → `CopilotInputError` (name, expected, got) BEFORE any
  AEDT / PyEDB call. Deviations (hot paths) are listed in the feature's plan.md Complexity Tracking.
- Pure functions: "Side effects: none".
- A function whose contract changes in a restructure feature (002-010) is a defect (Principle IX) unless the plan
  justifies it.
