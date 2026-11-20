# Contracts: `aedt_copilot.core.edb`

PyEDB is imported only inside `open_edb` (through `aedt_env.open_edb`, after `aedt_env.ensure`). The module is
importable without AEDT. Tests: `tests/unit/test_core_edb.py` (`aedb_path`; session with a fake opener). Real EDB
path covered by `tests/regression.py` from feature 003 on (first real caller); 002 migrates no caller.

## `aedb_path(board) -> str`

| Input | Type | Valid |
|---|---|---|
| board | str \| PathLike | `<x>.aedb` folder, `<x>.aedt` file or `<x>.aedb/edb.def`; quotes / spaces stripped |

Output: absolute path of the existing `.aedb` folder. Side effects: none.
Errors: empty → CopilotInputError(`board`, `non-empty path`); folder missing →
CopilotInputError(`board`, `existing .aedb folder`, resolved path).

## `open_edb(board, cell=None, readonly=True, version=None) -> pyedb.Edb`

| Input | Type | Valid | Default |
|---|---|---|---|
| board | as `aedb_path` | — | — |
| cell | str \| None | non-empty if given | None (first cell) |
| readonly | bool | — | True |
| version | str \| None | `"2026.1"`, `"2025.2"`, `"auto"` or an installed version | None = config.yaml |

Preconditions: AEDT installed (resolved by `aedt_env`). Validation at entry (before PyEDB import): `aedb_path`,
`cell`, `readonly` type.

Output: open `Edb` (.NET backend, explicit version, as `aedt_env.open_edb`). Caller closes it (prefer `edb_session`).
Side effects: none on disk while readonly.
Errors: CopilotInputError (inputs); RuntimeError from `aedt_env` (AEDT / version not found, message unchanged);
PyEDB errors propagate unchanged.

## `edb_session(board, cell=None, readonly=True, version=None, opener=None)` — context manager

Inputs as `open_edb`; `opener` (callable with the same signature, test hook) default `open_edb`.

Output: yields the `Edb`; on exit ALWAYS calls `edb.close()`. Body raised → that exception propagates, a close
error is suppressed (printed to stderr). Body succeeded and `close()` fails → close error propagates.
EDB saved: only if the body saves.

## Unchanged: `aedt_copilot.aedt_env.open_edb(path, cell=None, readonly=True, version=None)`

Signature and behaviour kept; only `aedt_env._machine()` now reads `core.config.machine()`.
