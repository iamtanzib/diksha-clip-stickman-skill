"""Keep this skill identical on every device (Windows PC + Mac) through its GitHub repo.

    python sync.py        (Windows)      python3 sync.py      (macOS)

1. Commits any local change (new log entries, skill edits) with the device name.
2. Pulls the other device's changes (rebase; log/used.md merges by union, so both sides' entries survive).
3. Pushes. Prints SKILL UPDATED + what changed when the other device had pushed something new.
Never fails the clip: offline, no git or a conflict just prints SYNC WARNING and the local copy is used.
"""
import datetime
import socket
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parent


def git(*a):
    try:
        return subprocess.run(["git", "-C", str(D), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return subprocess.CompletedProcess(a, 127, "", "git is not installed")


def main():
    if git("rev-parse", "--git-dir").returncode:
        return print(f"SYNC WARNING: {D.name} is not a git clone, so it cannot sync. Reinstall it with git clone.")
    if git("status", "--porcelain").stdout.strip():
        git("add", "-A")
        git("commit", "-q", "-m", f"Sync from {socket.gethostname()} {datetime.datetime.now():%Y-%m-%d %H:%M}")
    old = git("rev-parse", "HEAD").stdout.strip()
    p = git("pull", "-q", "--rebase")
    if p.returncode:
        git("rebase", "--abort")
        return print(f"SYNC WARNING: could not pull ({p.stderr.strip()[:200]}). Using the local copy; local edits stay committed.")
    # upstream commits the old local HEAD did not have = what the other device pushed
    incoming = git("log", "--format=- %s (%ar)", f"{old}..@{{u}}").stdout.strip()
    files = git("diff", "--stat", f"{old}...@{{u}}").stdout.strip() if incoming else ""
    if git("rev-list", "--count", "@{u}..HEAD").stdout.strip() not in ("", "0"):
        r = git("push", "-q")
        if r.returncode:
            print(f"SYNC WARNING: push failed ({r.stderr.strip()[:200]}). Run: gh auth login, then gh auth setup-git")
    if incoming:
        print(f"SKILL UPDATED ({D.name}) from the other device:\n{incoming}\n{files}")
    else:
        print(f"SKILL UP TO DATE ({D.name})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
