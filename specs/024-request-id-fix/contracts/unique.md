# Contract: aedt_copilot/core/unique.py

## claim_dir(path) -> str
- In: `path` non-empty str (absolute or relative). Parent folders are created if missing (exist_ok).
- Does: `os.mkdir(path)`; on `FileExistsError` tries `path_2`, `path_3`, … (for `X.aedb` → `X_2.aedb`: suffix
  before the extension), up to 10000.
- Out: absolute path of the folder THIS call created (empty). Two callers never get the same path.
- Errors: `CopilotInputError("path", ...)` on empty / non-str; `OSError` other than exists is raised.

## claim_file(path) -> str
- Same as claim_dir for a file: `os.open(O_CREAT|O_EXCL|O_WRONLY)`, closed at once, empty file left.
- Out: absolute path of the created (empty) file; caller writes it.

## move_aside(src, dst) -> str
- In: `src` existing path (file or folder), `dst` wanted target (non-empty str).
- Does: `os.rename(src, candidate)` with candidate = dst, dst_2, … ; skips existing candidates; never overwrites.
- Out: absolute final path.
- Errors: `CopilotInputError` on empty args; `FileNotFoundError` when src is missing.

## file_lock(path, timeout=30, stale=60) -> context manager
- In: lock file path. Creates it with O_EXCL (pid + time inside), deletes it on exit.
- Waits (sleep 0.05 s) while held; a lock older than `stale` s is removed (crashed owner) and retaken.
- Windows: `PermissionError` on create (lock file of another holder still pending delete) = busy, retried;
  denied continuously for > 2 s → that `PermissionError` is raised (fix 2026-11-10).
- Errors: `TimeoutError` after `timeout` s.
