"""Motion QA gate (Clip 2 lesson). Measures how the graphics panel actually moves in a rendered MP4.

Run from the project root after a draft render:
    python -I tools/motion_check.py renders/qa.mp4

Reports, per graphics (split) window of tools/layout.json:
  near-still %  frames where the panel barely changes. The editor's reference videos sit at 0-17 %;
                above ~15 % the clip reads as a slideshow ("starts, freezes, resumes").
  hard stops    motion that dies within one frame that is NOT a layout cut. Look at each one: fine if the thing
                is fading out or an intended impact, wrong if a move just halts (missing ease-out tail).
Exit code 1 if near-still is above target, so fix before showing the editor.
"""
import json
import subprocess
import sys

import numpy as np

FPS = 24
STILL = 0.2          # mean abs gray diff per frame (96x112 thumbnail) below this = near-still
TARGET_STILL = 15.0  # percent

src = sys.argv[1] if len(sys.argv) > 1 else "renders/qa.mp4"
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "crop=1080:960:0:0,scale=96:85,format=gray",
                      "-f", "rawvideo", "-"], capture_output=True).stdout
if not raw:  # 4K renders: crop scales with the frame
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "crop=iw:ih*0.5:0:0,scale=96:85,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.uint8).reshape(-1, 85, 96).astype(np.float32)
d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))

rows = json.load(open("tools/layout.json"))["layout"]
rows = rows + [[len(a) / FPS, "end", None]]
cuts = [r[0] for r in rows]
near_cut = lambda t: min(abs(t - c) for c in cuts) < 2.5 / FPS

allseg, bad = [], False
for (t, kind, _), (t2, *_rest) in zip(rows, rows[1:]):
    if kind not in ("split", "half"):
        continue
    s, e = int(t * FPS) + 2, int(t2 * FPS) - 1
    seg = d[s:e]
    if len(seg) == 0:
        continue
    allseg += list(seg)
    still = float(np.mean(seg < STILL) * 100)
    stops = [round((s + k) / FPS, 2) for k in range(len(seg) - 1)
             if seg[k] > 1.0 and seg[k + 1] < 0.25 * seg[k] and not near_cut((s + k) / FPS)]
    flag = "  <-- too still" if still > TARGET_STILL * 2 else ""
    print(f"[{t:6.2f}-{t2:6.2f}] near-still {still:4.0f}%  hard stops {stops}{flag}")
total = float(np.mean(np.array(allseg) < STILL) * 100) if allseg else 0.0
print(f"ALL graphics: near-still {total:.0f}% (target <= {TARGET_STILL:.0f}%)")
if total > TARGET_STILL or bad:
    print("FAIL: add continuous motion / ease-out tails before review (see references/style.md, Motion).")
    sys.exit(1)
print("PASS")
