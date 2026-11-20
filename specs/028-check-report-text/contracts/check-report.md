# Contract: report interface of a review check module (feature 028)

A module in `aedt_copilot/review_checks/` (public name = registered) has NAME, ORDER, TITLE, SEVERITY_RULE,
`run(cc) -> {items, data}` (feature 011) and, for every finding name its `run` can produce, either

```python
REPORT = {
    "<finding check name>": {
        "section": "reference" | "trace_stub" | "via" | "routing" | "<new section title>",
        "title": "Plain title shown in bold",
        "limit_key": "review.<template key>" | None,          # hover only
        "describe": describe,   # (f, P, channel) -> (rows [(label, text)], why, fix)
        "layers": layers,       # (f, ref_layers, metal) -> (signal layers, plane layers)
    },
}
```

or `DATA_ONLY = True` (no finding). `f` = finding dict of `cut_board/review.py` (m); `P` = template `review.*`;
`channel` = report channel (vias, chains...); `ref_layers(layer)` -> reference planes; `metal` = stack order.

`review_report.report_specs()` merges all `REPORT`s; a finding name in two modules → `RegistryError`.
No spec for a finding → generic block (At / Layer / Measured) and picture = issue layer + note.
