"""Small contact sheet from a rendered MP4 (cheap QA image: ~1.4K tokens instead of ~3K for a snapshot sheet).

Run from the project root:
    python -I tools/sheet.py renders/qa.mp4 12.5,20,31.2,40 [--w 270] [--out qa/sheet.jpg]
    python -I tools/sheet.py renders/qa.mp4 31.2 --crop 0:0:1080:1260 --w 720     # one detail frame (graphics panel)

Tiles are in the order given, left to right, 4 per row. Times are seconds on the final timeline.
Only open the sheet after `qa.py` text gates pass; one sheet per pass, a crop only for a flagged spot.
"""
import argparse
import math
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("times")
ap.add_argument("--w", type=int, default=270, help="tile width in px (270 = 4 tiles across 1080)")
ap.add_argument("--crop", default="", help="w:h:x:y style crop as x:y:w:h applied before scaling")
ap.add_argument("--out", default="qa/sheet.jpg")
ap.add_argument("--fps", type=float, default=24)
a = ap.parse_args()

ts = [float(t) for t in a.times.split(",") if t.strip()]
frames = [round(t * a.fps) for t in ts]
cols = min(4, len(frames))
rows = math.ceil(len(frames) / cols)
sel = "+".join(f"eq(n\\,{n})" for n in frames)
vf = [f"select='{sel}'"]
if a.crop:
    x, y, w, h = a.crop.split(":")
    vf.append(f"crop={w}:{h}:{x}:{y}")
vf += [f"scale={a.w}:-2", f"tile={cols}x{rows}:padding=4:color=white"]
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", ",".join(vf), "-frames:v", "1", "-q:v", "4", a.out], check=True)
print(a.out, "|", " ".join(f"[{i + 1}]{t:g}s" for i, t in enumerate(ts)))
