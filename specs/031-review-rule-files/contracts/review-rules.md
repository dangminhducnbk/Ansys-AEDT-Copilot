# Contract: review rule files (feature 031)

## Steering file `review_rules/<id>.md` (team) or `<personal folder>/<id>.md`

```
<!-- one-line description -->
# <Rule title>

| Field | Value |
|---|---|
| id | <id> (= file name, = code NAME) |
| findings | <finding name> = <report title>; <finding 2> = <title 2> |
| section | reference / trace_stub / via / routing / <new section title> |
| severity | <severity rule in words> |
| thresholds | review.<key>, review.<key> (or "none") |
| limit key | review.<key> (hover) or none |
| code | yes / no |

## What
## Why          (exact report sentence; `- \`<variant>\`: text` bullets when several)
## Fix          (same form)
## Discuss      (how Claude talks about it with the engineer)
```

Mandatory: id, findings (unless code = no), section, severity, thresholds, What, Why, Fix, Discuss.

## review_checks._rules

- `team_dir()` = `<repo>/review_rules`; `personal_dir()` = env `AEDT_COPILOT_REVIEW_RULES` or `~/.aedt_copilot/review_rules`.
- `parse(text)` → dict; `missing(rule)` → list of missing parts.
- `rules()` → [{id, title, source team|personal, shadowed, has_code, enabled, steering, code, findings, section,
  severity, thresholds}] (team first; personal with a team id → shadowed).
- `get(id)` → {rule, text} (team first); unknown id → `CopilotInputError` with closest ids.
- `text(id, part, variant=None, **fmt)` → Why / Fix sentence.
- `report(id, describe, layers)` → `{finding: {section, title, limit_key, describe, layers}}` (describe returns why /
  fix read from the steering).
- `enable(id)` / `disable(id)` (personal code only) → `<personal>/enabled.json`; `personal_modules()` → loaded
  enabled personal code modules (not shadowed).

## MCP tool `review_rules(op="list", rule_id="", user_approved_personal_code=False)` (CLI `review-rules`)

- `list` → {rules, personal_dir}; `get` → {rule, text}; `enable` (needs `user_approved_personal_code=true`) /
  `disable` → {rule}. CLI `review-rules --op=list|get|enable|disable|guide-list --args-file=`.
