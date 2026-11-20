<!-- Template for a new layout review rule (copy to <id>.md; this file is not a rule). -->
# <Rule title>

| Field | Value |
|---|---|
| id | <id> (file name; code file aedt_copilot/review_checks/<id>.py, NAME = <id>) |
| findings | <Finding name> = <title shown in the report>; <Finding 2> = <title 2> |
| section | reference / trace_stub / via / routing / <new section title> |
| not ok when | condition in words against the threshold; everything else is OK |
| thresholds | review.<key>, review.<key> (rows of templates/autocut_template.csv) or none |
| limit key | review.<key> (shown in the hover) or none; per finding: <Finding> = review.<key>; <Finding 2> = none |
| code | yes / no (no = judged by Claude, never stops a cut) |

## What
What is measured, how, what is skipped.

## Why
The exact sentence of the report ({placeholders} filled by the code). Several findings / variants:
- `<variant>`: sentence

## Fix
Same form as Why.

## Discuss
How Claude talks about it with the engineer (what to give, what to ask, never decide for them).

## Report
- <Check name>: <one short line shown under "This section checks:" in the HTML report>.

## Issue
<one sentence for the report Description, placeholders {net} {layer} {planes} {group} {other_net} {what} + fields of the rule code; variants as `- \`<finding>\`: sentence`>

## Recommendation
<one sentence: what the designer should change>
