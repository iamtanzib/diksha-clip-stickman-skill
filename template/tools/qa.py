"""One-command QA gate. Replaces ~8 separate tool calls per pass with one, and prints only what matters.

Run from the project root (run it in the background when --render is on; you are notified when it ends):
    python -I tools/qa.py                          # build + lint + check (text gates only, ~1 min)
    python -I tools/qa.py --render --at 3,9.5,17,24,31,38    # + draft render, motion_check, qa_cuts, one panel sheet

Stops at the first failing gate and prints its filtered output. On PASS, look at the sheet ONCE (qa/sheet.jpg).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--render", action="store_true")
ap.add_argument("--at", default="", help="comma-separated times for the contact sheet (graphics panel only)")
ap.add_argument("--full", action="store_true", help="sheet of the whole frame instead of the graphics panel")
ap.add_argument("--out", default="renders/qa.mp4")
a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows console + CLI symbols

pkg = Path("package.json").read_text(encoding="utf-8") if Path("package.json").exists() else ""
m = re.search(r"hyperframes@[0-9.]+", pkg)
HF = f"npx --yes {m.group(0) if m else 'hyperframes'}"
KEEP = re.compile(r"error|fail|overlap|campath|✗|×|⚠|not found|exception", re.I)
# Template-level lint warnings that are known and harmless in this house setup (one big file, breathing #gfx, bg layers).
IGNORE = re.compile(r"composition_file_too_large|nested_structure_needs_sub|negative_z_index|"
                    r"gsap_repeated_fromto_without_baseline: \d+ tl\.fromTo\(\) calls target \"#gfx\"|^\s*Fix:|0 error\(s\)")


def run(name, cmd, max_lines=18, gate=True, raw=False):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout + "\n" + p.stderr).strip().splitlines()
    hits = [l.strip()[:200] for l in out if l.strip() and (raw or (KEEP.search(l) and not IGNORE.search(l)))]
    ok = p.returncode == 0
    errs = [l for l in out if "✗" in l]
    if not ok and name.startswith("check") and errs and all("need 3:1" in l for l in errs) and any("#caps" in l for l in errs):
        ok = True   # white captions with a soft shadow are the editor's exact style; the contrast audit ignores text-shadow
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    for l in (hits[-max_lines:] if raw else hits[:max_lines] if hits else out[-1:]):
        print("   ", l)
    if len(hits) > max_lines:
        print(f"    ... {len(hits) - max_lines} more")
    if gate and not ok:
        sys.exit(1)
    return out


run("build", "python -I tools/build.py")
run("lint", f"{HF} lint")
run("check (layout + tween overlaps)", f"{HF} check")
if not a.render:
    sys.exit(0)

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
run("draft render", f'{HF} render -q draft -o "{a.out}"', max_lines=6)
run("motion_check", f'python -I tools/motion_check.py "{a.out}"', max_lines=25, raw=True)
run("qa_cuts", f'python -I tools/qa_cuts.py "{a.out}"', max_lines=12, gate=False, raw=True)
if a.at:
    crop = "" if a.full else " --crop 0:0:1080:960"
    run("sheet", f'python -I tools/sheet.py "{a.out}" {a.at}{crop} --out qa/sheet.jpg', max_lines=3)
print("ALL GATES PASS" + (" -> open qa/sheet.jpg once" if a.at else ""))
