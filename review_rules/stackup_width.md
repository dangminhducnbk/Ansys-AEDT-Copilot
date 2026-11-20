<!-- Width and pair gap per layer compared with the fab stackup table -->
# Trace width / pair gap vs the stackup table

| Field | Value |
|---|---|
| id | stackup_width |
| findings | Width vs stackup = Trace width differs from the stackup; Gap vs stackup = Pair gap differs from the stackup; No stackup value = No stackup value for this layer; No stackup table = No stackup table for this board |
| section | Stackup |
| not ok when | measured − table > the tolerance (no table / layer entry: OK, kept as data) |
| thresholds | review.stackup_tol_mm, review.neckdown_zone_mm |
| limit key | review.stackup_tol_mm |
| code | yes |

## What
Width of each signal trace per layer (single-ended or pair width) and the median gap of each diff pair per
layer, compared with the stackup table (tool `review_stackup_table`; file `<board folder>/Ansys AEDT Copilot/stackup/
<board>.json`). No impedance calculation. Break-out segments (mostly inside the neck-down zone) skipped.

## Why
- `Width vs stackup`: a width that differs from the stackup design changes the impedance of this trace (reflection).
- `Gap vs stackup`: a pair gap that differs from the stackup design changes the differential impedance.
- `No stackup value`: width / gap cannot be checked without the stackup values.
- `No stackup table`: width / gap cannot be checked without the stackup values.

## Fix
- `Width vs stackup`: route with the stackup width for this layer, or correct the stackup table if it is out of date.
- `Gap vs stackup`: route the pair with the stackup gap for this layer, or correct the stackup table.
- `No stackup value`: import the fab stackup (review_stackup_table) and confirm the table.
- `No stackup table`: import the fab stackup (review_stackup_table) and confirm the table.

## Discuss
No table → offer the import: the user gives the fab stackup (PDF / Excel), you read it into a table
per layer (`review_stackup_table(op="template")`), show it, and save only after the user confirms
(`user_confirmed_table=true`). Re-import / edit the same way; the old file is kept as `_old_<time>`.

## Report
- Trace width: width matches the stackup.
- Pair gap: gap matches the stackup.

## Issue
- `Width vs stackup`: {net} ({layer}) trace width differs from the stackup.
- `Gap vs stackup`: Pair {group} gap on {layer} differs from the stackup.
- `No stackup value`: {net} ({layer}): no stackup value for this layer, width and gap not checked.
- `No stackup table`: {net} ({layer}): no stackup table, width and gap not checked.

## Recommendation
- `Width vs stackup`: Use the stackup width for this layer.
- `Gap vs stackup`: Use the stackup gap for this layer.
- `No stackup value`: Add this layer to the fab stackup table.
- `No stackup table`: Provide the fab stackup table.
