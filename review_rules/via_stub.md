<!-- Via barrel beyond the outermost signal layers -->
# Via stub / backdrill

| Field | Value |
|---|---|
| id | via_stub |
| findings | Via stub = Via stub |
| section | via |
| not ok when | the stub > 0 |
| thresholds | none |
| limit key | none |
| code | yes |

## What
Per signal via stack: layer range, used layers (trace / polygon / pin connections), backdrill, stub.
Stub = barrel beyond the outermost used layers; with backdrill → the remaining stub declared in EDB. The via table of
the review (reference data) belongs to this rule.

## Why
the unused part of the via barrel is an open stub: resonance and an insertion-loss dip at high frequency.

## Fix
backdrill the via, or use a blind / buried via, or route on layers that use the whole barrel.

## Discuss
Judge the stub against the interface data rate, never by length alone. Rule of thumb: a stub matters when its
quarter-wave resonance f = c / (4 · stub · √Dk_eff) comes near the band of interest (≥ ~3× the Nyquist frequency =
data rate / 2 for NRZ). Example: 0.26 mm stub, Dk ≈ 3.8 → ~150 GHz → harmless for PCIe Gen4 (8 GHz Nyquist), worth
noting for 56G PAM4. The rule stays NOT OK for any stub > 0: give the numbers (rate, stub mm, estimated resonance), never re-rank it. Ask the
engineer for the data rate if the interface does not say it.

## Report
- Via stub: unused part of the via barrel.

## Issue
Signal via of {net} has an unused stub.

## Recommendation
Backdrill the via or use a blind / buried via.
