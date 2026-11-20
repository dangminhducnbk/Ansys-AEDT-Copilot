# Contract — 042 merge into a board copy

## `cut_board.stackup_check`

```
read(edb) -> {"layers": [{"name", "type", "material", "fill", "thickness_um"}],   # stackup order (top first)
              "materials": {name: {"permittivity", "loss_tangent", "conductivity"}}}
compare(ref, got) -> [str]                                # [] = identical
```
Tolerances: thickness ± 0.01 µm; property relative 1e-6 (absolute 1e-12 when ref = 0). Lines (English):
`layer order: ... -> ...`, `missing layer <n>`, `extra layer <n>`, `<layer> thickness 31.0 -> 30.0 um`,
`<layer> material A -> B`, `<layer> fill A -> B`, `<material> permittivity 4.1 -> 4.3`.

## `cut_board.merge`

```
copy_board(board, workspace, target_aedt, log) -> {"aedt", "aedb", "bytes", "board_designs": [..]}
merge_designs(orig, sources, out_dir, port=None, log=print, create_if_missing=False, backup=True, board_stackup=None)
  -> {... as before, "channels": {name: {..., "checks": {"pins": [str], "stackup": [str]}}},
      "board_designs_before": [..], "board_designs_after": [..]}
```
Any `checks` line → channel `state = "error"`, `error` = joined lines.

## stage1 / self-check / request

- `stage1.board_stackup` = `read()` of the source board (5.4.0+).
- self-check result `stackup`: `{"ok": true | false | null, "diffs": [str], "note": str?}`; diffs also in `mismatches`
  as `{"item": "stackup = board", "expected": "board stackup", "got": line}`.
- request keys: `merge_layout = "board_copy"`, `merged_board_designs`, `merged_copy_bytes`.

## `isim_go` result / M3

Rows add `stackup` ("OK" | "NOT OK" | "-") and `checks`; result adds `board_copy` {designs, mb}. M3 lines after the
table: `Board copy / Bản copy board: <designs> (<mb> MB)`; `Stackup = board: OK` or per channel the difference lines.
