"""Public repository guard (feature 046): refuse customer data in commits / pushes.

  python tools/public_guard.py scan [--all | <paths>...]   check files (--all = everything git would commit)
  python tools/public_guard.py pre-commit                  check the staged files + author / committer e-mail
  python tools/public_guard.py pre-push <remote> <url>     check every outgoing commit (refs on stdin)
  python tools/public_guard.py scrub [--apply] [<paths>]   replace protected terms in tracked text files (dry run)
  python tools/public_guard.py install                     git hooks (.githooks) + repo e-mail
  python tools/public_guard.py list-check                  validate the protected list, print counts

The protected list `.public_guard.local.json` (repo root) is LOCAL ONLY (ignored by git): it names the terms.
Contract: specs/046-public-release/contracts/public-guard.md. Stdlib only (runs before .venv exists).
Exit: 0 OK, 1 findings / refused, 2 bad input.
"""
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_NAME = ".public_guard.local.json"
ZERO = "0" * 40
BIN_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".npz", ".npy", ".zip", ".7z", ".gz", ".tar",
           ".xlsx", ".xls", ".docx", ".pptx", ".dll", ".exe", ".pyd", ".so", ".whl", ".aedt", ".def", ".siw",
           ".wkb", ".pkl", ".bin", ".woff", ".woff2", ".ttf"}
FIX = {
    "term": "replace the name (tools/public_guard.py scrub --apply <file>) or move the detail to CLAUDE.local.md",
    "path": "this path is local only: git rm --cached <path> (file stays on disk)",
    "binary": "look at the file; if it holds no customer data add its sha256 to approved_binaries",
    "email": "git config user.email <list e-mail> then git commit --amend --reset-author",
    "size": "large file (often board data): keep it local or approve it explicitly",
}


# ---------------------------------------------------------------- pure
def load_list(path):
    """Read + validate the protected list (data-model.md). ValueError names the bad key."""
    if not isinstance(path, str) or not os.path.isfile(path):
        raise ValueError(f"protected list not found: {path} (create {LIST_NAME} at the repo root, see CLAUDE.md)")
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except ValueError as ex:
        raise ValueError(f"protected list {path}: not valid JSON ({ex})")
    if not isinstance(d, dict) or d.get("version") != 1:
        raise ValueError("protected list: 'version' must be 1")
    em = d.get("email")
    if not isinstance(em, str) or "@" not in em:
        raise ValueError("protected list: 'email' must be an e-mail address")
    mb = d.get("max_bytes", 5000000)
    if not isinstance(mb, int) or mb <= 0:
        raise ValueError("protected list: 'max_bytes' must be a positive integer")
    terms = []
    for i, t in enumerate(d.get("terms") or []):
        if not isinstance(t, dict) or not isinstance(t.get("pattern"), str) or not t["pattern"]:
            raise ValueError(f"protected list: terms[{i}].pattern must be a non-empty string")
        try:
            rx = re.compile(t["pattern"], 0 if t.get("case") else re.I)
        except re.error as ex:
            raise ValueError(f"protected list: terms[{i}].pattern does not compile ({ex})")
        terms.append({"rx": rx, "pattern": t["pattern"], "note": str(t.get("note") or "")})
    if not terms:
        raise ValueError("protected list: 'terms' must not be empty")
    reps = []
    for i, r in enumerate(d.get("replace") or []):
        if not isinstance(r, dict) or not isinstance(r.get("from"), str) or not r["from"] \
                or not isinstance(r.get("to"), str):
            raise ValueError(f"protected list: replace[{i}] needs string 'from' (non-empty) and 'to'")
        if r.get("regex"):
            try:
                rx = re.compile(r["from"])
            except re.error as ex:
                raise ValueError(f"protected list: replace[{i}].from does not compile ({ex})")
            reps.append((rx, r["to"]))
        else:
            reps.append((r["from"], r["to"]))
    paths = d.get("paths") or []
    if not isinstance(paths, list) or any(not isinstance(p, str) or not p for p in paths):
        raise ValueError("protected list: 'paths' must be a list of non-empty strings")
    appr = d.get("approved_binaries") or {}
    if not isinstance(appr, dict) or any(not re.fullmatch(r"[0-9a-f]{64}", str(v)) for v in appr.values()):
        raise ValueError("protected list: 'approved_binaries' values must be 64 hex chars (sha256)")
    return {"email": em.lower(), "max_bytes": mb, "terms": terms, "replace": reps, "paths": paths,
            "approved": {k.replace("\\", "/"): v for k, v in appr.items()}}


def finding(rule, path, line=None, text="", commit=None):
    return {"rule": rule, "path": path, "line": line, "text": text[:120], "commit": commit, "fix": FIX[rule]}


def path_blocked(lst, path):
    p = path.replace("\\", "/")
    for pat in lst["paths"]:
        if fnmatch.fnmatchcase(p, pat) or (pat.endswith("/*") and p.startswith(pat[:-1])):
            return pat
    return None


def is_binary(path, data):
    return os.path.splitext(path)[1].lower() in BIN_EXT or b"\0" in data[:8000]


def check_blob(lst, path, data, commit=None):
    """Findings for one file content (bytes) at repo path `path`. Never raises on content."""
    path = path.replace("\\", "/")
    out = []
    pat = path_blocked(lst, path)
    if pat:
        out.append(finding("path", path, text=f"matches local-only pattern '{pat}'", commit=commit))
        return out
    if len(data) > lst["max_bytes"]:
        out.append(finding("size", path, text=f"{len(data)} bytes > {lst['max_bytes']}", commit=commit))
    if is_binary(path, data):
        h = hashlib.sha256(data).hexdigest()
        if lst["approved"].get(path) != h:
            out.append(finding("binary", path, text=f"sha256 {h}", commit=commit))
        return out
    text = data.decode("utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        for t in lst["terms"]:
            m = t["rx"].search(line)
            if m:
                a = max(0, m.start() - 40)
                ctx = line[a:m.end() + 40].strip()
                out.append(finding("term", path, i, f"'{m.group(0)}' ({t['note'] or t['pattern']}): {ctx}",
                                   commit))
    return out


def check_email(lst, email, where, commit=None):
    if (email or "").strip().lower() != lst["email"]:
        return [finding("email", where, text=f"'{email}' != '{lst['email']}'", commit=commit)]
    return []


def scrub_text(lst, text):
    """Apply replacements in order. Returns (new_text, count). Line endings untouched."""
    n = 0
    for frm, to in lst["replace"]:
        if hasattr(frm, "subn"):
            text, k = frm.subn(to, text)
        else:
            k = text.count(frm)
            text = text.replace(frm, to)
        n += k
    return text, n


def outgoing(lines, rev_list):
    """Commit ids to check from pre-push stdin lines. rev_list(args) -> list of ids (newest first, like git)."""
    seen, out = set(), []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        f = raw.split()
        if len(f) != 4:
            raise ValueError(f"pre-push input: expected '<local ref> <local sha> <remote ref> <remote sha>', got '{raw}'")
        _, lsha, _, rsha = f
        if lsha == ZERO:                                     # deleted ref
            continue
        ids = rev_list([lsha, "--not", "--remotes"]) if rsha == ZERO else rev_list([f"{rsha}..{lsha}"])
        for c in reversed(ids):
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


def report(findings, n_files):
    if not findings:
        return f"public_guard: OK ({n_files} files)"
    by = {}
    for f in findings:
        by.setdefault(f["rule"], []).append(f)
    lines = [f"public_guard: REFUSED - {len(findings)} finding(s) in {n_files} file(s) checked"]
    for rule in ("email", "path", "binary", "size", "term"):
        fs = by.get(rule)
        if not fs:
            continue
        lines.append(f"\n[{rule}] fix: {FIX[rule]}")
        for f in fs[:200]:
            loc = f["path"] + (f":{f['line']}" if f["line"] else "")
            lines.append(f"  {(f['commit'] or '')[:8] + ' ' if f['commit'] else ''}{loc}  {f['text']}")
        if len(fs) > 200:
            lines.append(f"  ... {len(fs) - 200} more")
    return "\n".join(lines)


# ---------------------------------------------------------------- git adapters
def git(*args, data=None, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd or ROOT, input=data, capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def _z(b):
    return [x for x in b.decode("utf-8", "replace").split("\0") if x]


def staged(cwd=None):
    return [(p, git("show", f":{p}", cwd=cwd)) for p in
            _z(git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR", cwd=cwd))]


def commit_files(c, cwd=None):
    out = []
    parts = _z(git("diff-tree", "--no-commit-id", "-r", "--root", "-M", "--name-status", "-z", c, cwd=cwd))
    i = 0
    while i < len(parts):
        st = parts[i]
        if st[0] in "RC":
            path, i = parts[i + 2], i + 3
        else:
            path, i = parts[i + 1], i + 2
        if st[0] != "D":
            out.append((path, git("cat-file", "blob", f"{c}:{path}", cwd=cwd)))
    return out


def ident_email(var, cwd=None):
    s = git("var", var, cwd=cwd).decode("utf-8", "replace")
    m = re.search(r"<([^>]*)>", s)
    return m.group(1) if m else ""


def all_files(cwd=None):
    """Every file the next commit would hold if everything were added (tracked + untracked not ignored)."""
    names = set(_z(git("ls-files", "-z", cwd=cwd))) | set(_z(git("ls-files", "-z", "--others", "--exclude-standard",
                                                                     cwd=cwd)))
    base = cwd or ROOT
    out = []
    for p in sorted(names):
        fp = os.path.join(base, *p.split("/"))
        if os.path.isfile(fp):
            with open(fp, "rb") as f:
                out.append((p, f.read()))
    return out


# ---------------------------------------------------------------- commands
def _list(cwd=None):
    return load_list(os.path.join(cwd or ROOT, LIST_NAME))


def cmd_scan(args, cwd=None):
    lst = _list(cwd)
    if args and args[0] == "--all":
        files = all_files(cwd)
    elif args:
        files = []
        for p in args:
            with open(os.path.join(cwd or ROOT, p), "rb") as f:
                files.append((p.replace("\\", "/"), f.read()))
    else:
        files = [(p, open(os.path.join(cwd or ROOT, *p.split("/")), "rb").read())
                 for p in _z(git("ls-files", "-z", cwd=cwd)) if os.path.isfile(os.path.join(cwd or ROOT, p))]
    fs = [x for p, d in files for x in check_blob(lst, p, d)]
    print(report(fs, len(files)))
    return 1 if fs else 0


def cmd_pre_commit(cwd=None):
    lst = _list(cwd)
    files = staged(cwd)
    fs = check_email(lst, ident_email("GIT_AUTHOR_IDENT", cwd), "author e-mail")
    fs += check_email(lst, ident_email("GIT_COMMITTER_IDENT", cwd), "committer e-mail")
    fs += [x for p, d in files for x in check_blob(lst, p, d)]
    print(report(fs, len(files)), file=sys.stderr)
    return 1 if fs else 0


def cmd_pre_push(stdin_lines, cwd=None):
    lst = _list(cwd)
    commits = outgoing(stdin_lines, lambda a: git("rev-list", *a, cwd=cwd).decode().split())
    fs, n = [], 0
    for c in commits:
        ae, ce = git("log", "-1", "--format=%ae%n%ce", c, cwd=cwd).decode("utf-8", "replace").splitlines()[:2]
        fs += check_email(lst, ae, "author e-mail", c) + check_email(lst, ce, "committer e-mail", c)
        files = commit_files(c, cwd)
        n += len(files)
        fs += [x for p, d in files for x in check_blob(lst, p, d, c)]
    print(f"public_guard: {len(commits)} outgoing commit(s)", file=sys.stderr)
    print(report(fs, n), file=sys.stderr)
    return 1 if fs else 0


def cmd_scrub(args, cwd=None):
    lst = _list(cwd)
    apply = "--apply" in args
    paths = [a.replace("\\", "/") for a in args if a != "--apply"] or _z(git("ls-files", "-z", cwd=cwd))
    total, changed = 0, []
    for p in paths:
        fp = os.path.join(cwd or ROOT, *p.split("/"))
        if not os.path.isfile(fp) or path_blocked(lst, p):
            continue
        with open(fp, "rb") as f:
            data = f.read()
        if is_binary(p, data):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            print(f"  skip (not UTF-8): {p}")
            continue
        new, n = scrub_text(lst, text)
        if n:
            total += n
            changed.append((p, n))
            if apply:
                with open(fp, "wb") as f:
                    f.write(new.encode("utf-8"))
    for p, n in changed:
        print(f"  {p}: {n}")
    print(f"public_guard scrub: {total} replacement(s) in {len(changed)} file(s)"
          + ("" if apply else " (dry run, --apply to write)"))
    return 0


def cmd_install(cwd=None):
    lst = _list(cwd)
    git("config", "core.hooksPath", ".githooks", cwd=cwd)
    git("config", "user.email", lst["email"], cwd=cwd)
    print(f"public_guard: hooks = .githooks, user.email = {lst['email']}")
    return 0


def cmd_list_check(cwd=None):
    lst = _list(cwd)
    print(f"public_guard list OK: {len(lst['terms'])} terms, {len(lst['replace'])} replacements, "
          f"{len(lst['paths'])} local-only paths, {len(lst['approved'])} approved binaries, e-mail {lst['email']}")
    return 0


def main(argv, stdin=None, cwd=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    try:
        if cmd == "scan":
            return cmd_scan(args, cwd)
        if cmd == "pre-commit":
            return cmd_pre_commit(cwd)
        if cmd == "pre-push":
            return cmd_pre_push((stdin or sys.stdin).read().splitlines(), cwd)
        if cmd == "scrub":
            return cmd_scrub(args, cwd)
        if cmd == "install":
            return cmd_install(cwd)
        if cmd == "list-check":
            return cmd_list_check(cwd)
    except ValueError as ex:
        print(f"public_guard: {ex}", file=sys.stderr)
        return 2 if cmd in ("scan", "scrub", "install", "list-check") else 1
    print(f"public_guard: unknown command '{cmd}' (scan, pre-commit, pre-push, scrub, install, list-check)",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
