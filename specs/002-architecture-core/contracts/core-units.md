# Contracts: `aedt_copilot.core.units`

Pure, no side effects. Constants `MM = 1e-3` (m per mm, same as `cutter.MM`), `MM2 = 1e-6` (m² per mm²).
Tests: `tests/unit/test_core_units.py`.

| Function | Input (validated) | Output |
|---|---|---|
| `mm_to_m(v) -> float` | finite number (not bool) | `v * MM` |
| `m_to_mm(v) -> float` | finite number | `v / MM` |
| `mm2_to_m2(v) -> float` | finite number | `v * MM2` |
| `m2_to_mm2(v) -> float` | finite number | `v / MM2` |
| `edb_length(m, digits=4) -> str` | `m` finite number; `digits` int 0..9 | `f"{round(m / MM, digits):g}mm"` (0.0002 → `"0.2mm"`, identical to cutter.py solder-ball strings) |

Errors: CopilotInputError naming `v` / `m` / `digits`.
Not used in inner loops (geometry keeps raw floats), so per-call validation is fine.
