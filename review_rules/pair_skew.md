<!-- Length of each member of a diff pair / CPHY trio (data only) -->
# Pair / trio lengths

| Field | Value |
|---|---|
| id | pair_skew |
| findings | none |
| section | routing |
| not ok when | data only (no finding): the allowed skew depends on the interface spec, which the engineer knows |
| thresholds | none |
| limit key | none |
| code | yes |

## What
Per pair / trio (same grouping as `routing`): total length (trace + via barrel, through series parts) of each member
and its length per layer. No threshold, no OK / NOT OK, no recommendation (user rule 2026-11-15, 4.1.0). The report
shows a P / N length table in each pair box of "Signal routing per pair".

## Why
(data only)

## Fix
(data only)

## Discuss
Never judge or ask about skew; quote the lengths only when the engineer asks.
