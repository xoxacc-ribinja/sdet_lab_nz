#!/usr/bin/env python3
"""Save a finished NZ report from macOS clipboard and push it with local Git.

No report templates or AI services. Run from the cloned sdet_lab_nz repository:
    python3 tools/save_report.py daily
    python3 tools/save_report.py weekly --date 2026-10-18
    python3 tools/save_report.py monthly --date 2026-10-31
"""

from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPO_NAME = "xoxacc-ribinja/sdet_lab_nz"
REPO_ROOT = Path(__file__).resolve().parent.parent


class ReportError(Exception):
    """An expected error that should be displayed without a traceback."""


def command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise ReportError(f"Command failed: {' '.join(args)}\n{detail}")
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return command("git", "-C", str(REPO_ROOT), *args, check=check)


def report_path(kind: str, day: date) -> Path:
    if kind == "daily":
        name = day.isoformat()
    elif kind == "weekly":
        year, week, _ = day.isocalendar()
        name = f"{year}-W{week:02d}"
    elif kind == "monthly":
        name = day.strftime("%Y-%m")
    else:
        raise ReportError(f"Unknown report type: {kind}")
    return Path("reports") / kind / f"{name}.md"


def validate_repo() -> None:
    top = Path(git("rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != REPO_ROOT:
        raise ReportError("The script is not in the expected Git repository root.")
    branch = git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise ReportError(f"Expected main branch, currently: {branch or '(detached HEAD)'}")
    origin = git("remote", "get-url", "origin").stdout.strip()
    valid = (
        rf"https://github\.com/{REPO_NAME}(?:\.git)?/?",
        rf"git@github\.com:{REPO_NAME}(?:\.git)?/?",
        rf"ssh://git@github\.com/{REPO_NAME}(?:\.git)?/?",
    )
    if not any(re.fullmatch(item, origin) for item in valid):
        raise ReportError(f"Unexpected origin: {origin}\nExpected GitHub repository: {REPO_NAME}")


def read_clipboard() -> str:
    if sys.platform != "darwin":
        raise ReportError("Clipboard mode requires macOS (pbpaste).")
    try:
        text = command("pbpaste").stdout
    except FileNotFoundError as exc:
        raise ReportError("pbpaste not available: macOS required.") from exc
    if not text.strip():
        raise ReportError("Clipboard is empty; copy the final report first.")
    return text


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as temp:
            temp_name = temp.name
            temp.write(content)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    if path.read_text(encoding="utf-8") != content:
        raise ReportError(f"Local content verification failed: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a finished NZ report from the macOS clipboard.")
    parser.add_argument("kind", choices=("daily", "weekly", "monthly"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(),
                        help="Report period date, YYYY-MM-DD (defaults to today's local date)")
    parser.add_argument("--replace", action="store_true", help="Explicitly replace an existing report")
    parser.add_argument("--no-push", action="store_true", help="Commit locally, but do not push to GitHub")
    args = parser.parse_args()

    try:
        validate_repo()
        content = read_clipboard()
        relative = report_path(args.kind, args.date)
        target = REPO_ROOT / relative
        if target.exists() and not args.replace:
            raise ReportError(f"Report already exists: {relative}\nUse --replace to save a revised version.")
        if target.exists() and target.is_symlink():
            raise ReportError(f"Refusing to overwrite a symlink: {relative}")
        if target.exists() and target.read_text(encoding="utf-8") == content:
            print(f"Unchanged: {relative} (no new commit)")
        else:
            atomic_write(target, content)
            print(f"SAVED LOCALLY: {relative} ({len(content)} characters)")
            # Stage new files; --only commits this path, not unrelated staged files.
            git("add", "--", str(relative))
            git("commit", "--only", "-m", f"reports: save NZ {args.kind} {relative.stem}", "--", str(relative))
            sha = git("rev-parse", "HEAD").stdout.strip()
            print(f"LOCAL COMMIT: {sha}")

        if args.no_push:
            print("PUSH SKIPPED (--no-push); report is only local.")
            return 0

        push = git("push", "origin", "main", check=False)
        if push.returncode != 0:
            detail = push.stderr.strip() or push.stdout.strip()
            print(f"PUSH FAILED: {detail}\nReport and any new commit remain local.", file=sys.stderr)
            return 1

        local_sha = git("rev-parse", "HEAD").stdout.strip()
        remote = git("ls-remote", "origin", "refs/heads/main", check=False)
        if remote.returncode != 0:
            print("PUSH RAN, BUT REMOTE VERIFICATION FAILED; check GitHub manually.", file=sys.stderr)
            return 1
        remote_sha = remote.stdout.split()[0] if remote.stdout.strip() else None
        if remote_sha != local_sha:
            print("REMOTE SHA DOES NOT MATCH LOCAL HEAD; check GitHub manually.", file=sys.stderr)
            return 1
        print(f"VERIFIED ON GITHUB: {REPO_NAME} main @ {remote_sha}")
        return 0
    except (ReportError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
