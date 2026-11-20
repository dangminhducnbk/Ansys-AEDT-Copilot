<!-- Open trace end or T-branch on a signal net -->
# Trace stub

| Field | Value |
|---|---|
| id | trace_stubs |
| findings | Trace stub = Trace stub |
| section | trace_stub |
| not ok when | an open trace end or a T-branch |
| thresholds | none |
| limit key | none |
| code | yes |

## What
A trace end not connected to a same-net pad / via / trace end / polygon (open end), or ending on the
middle of another same-net trace on the same layer (T-branch).

## Why
- `T-branch`: a branch splits the signal and leaves a stub (reflection).
- `open trace end`: an unconnected trace end is a resonant stub / antenna.

## Fix
- `T-branch`: remove the branch, or check that it is intended (e.g. test point).
- `open trace end`: remove the dangling segment.

## Discuss
Test points and intended branches exist: ask before calling it a defect.

## Report
- Open end: trace ends without a connection.
- T-branch: a trace branches off another trace.

## Issue
{net} ({layer}) has {what}.

## Recommendation
Remove the dangling segment / branch.
