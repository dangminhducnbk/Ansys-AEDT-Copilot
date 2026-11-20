# Data Model: Architecture + core/

## TemplateRow (from `core.config.template_rows(path)`)

| Field | Type | From column | Missing column / empty cell |
|---|---|---|---|
| key | str | `Key` | row skipped if empty |
| name | str | `Parameter` | "" |
| unit | str | `Unit` | "" |
| type | `num`\|`bool`\|`text`\|`list` | `Type` | "text" |
| scope | `channel`\|`job` | `Scope` | "channel" |
| mandatory | bool | `Mandatory` (`yes` → True) | False |
| default | str \| None | `Default` | None |
| desc | str | `Description` | "" |

Order = file order. Returned as deep copy (callers may mutate). Cache key = (abs path, mtime).

## MachineConfig (from `core.config.machine()`)

dict from `config.yaml` (missing file → {}), then: `aedt_version` default "2026.1"; `python` resolved to an
existing absolute path, else `sys.executable`. Other keys (`aedt_root`, `aedt_grpc_port`, ...) passed through.

## EdbSession

| State | Meaning |
|---|---|
| closed | before `__enter__` / after `__exit__` |
| open | `Edb` object yielded; readonly per argument |

Transition open → closed always runs `edb.close()` (also on exception).

## RegistryEntry

Python module in a registry package: `NAME: str` (unique, non-empty), `ORDER: int`, `run: callable`
(+ extra attributes per registry). Sorted by `(ORDER, NAME)`.

## RoadmapItem (`specs/ROADMAP.md`)

number, name, type (restructure | new rule | test | postponed), scope, depends on, regression gate.
