# Research: Full settings form

## R1 — Who renders the form

- Decision: the client (Claude desktop `show_widget`, HTML + JS; `sendPrompt(text)` returns the submit as a chat
  message). The MCP server returns data only.
- Why: the MCP server (mcp<2, FastMCP) has no UI; elicitation forms are flat (no tabs / buttons) — usable only as a
  fallback for one tab without "Set default". Other clients → chat table (FR-011).

## R2 — Choices

- Decision: parse the template Description `^\w+( \| \w+)+` → options (`radiation | pml`, `mixed | first | second`,
  `interpolation | discrete`, `conformal | convex_hull | bounding_box`, `cylinder | spheroid`). The airbox extent rows
  get `conforming | bounding_box | convex_hull` (values accepted by PyEDB `hfss_extent_info`).
- bool → checkbox; num → number input; list → text (comma separated); text without choices → text.

## R3 — Defaults for "Set default"

- Decision: descriptor `default` = `coerce(template default)`; mandatory sweep rows have no default → null. The
  widget keeps a per-tab "last typed" value for those rows so "Set default" does not clear what the engineer typed.

## R4 — Per-interface validation in one call

- Decision: loop over `settings.validate_for` (unchanged rules, same messages as the Excel flow). No new rules.
