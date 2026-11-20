<!-- Length per net / layer, widths, skew, layer match (data only) -->
# Routing data (length, width, skew, layers)

| Field | Value |
|---|---|
| id | routing |
| findings | none |
| section | routing |
| not ok when | data only (no finding); never judge skew (4.1.0) |
| thresholds | none |
| limit key | none |
| code | yes |

## What
Groups by net suffix (`_P/_N`, `_DP/_DN`, `+/-`, `P/N`; CPHY `_A/_B/_C`), confirmed at GATE A. Length =
trace (all layers) + via barrel between used layers; chains through series parts are summed. Intra-group skew, inter-
group skew, length per layer, widths per layer, same layers inside a pair / trio. Lengths of each pair member: `pair_skew` (data only, 4.1.0).

## Why
(data only)

## Fix
(data only)

## Discuss
Quote the numbers only when the engineer asks or when a pair / trio uses different layers.
