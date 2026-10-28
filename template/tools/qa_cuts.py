"""QA a render for unplanned jumps and flashes.

Measures mean frame-to-frame change (signalstats YDIF) in the graphics area, the speaker
inset and the whole frame. Spikes not within one frame of a planned picture change
(layout rows in tools/layout.json + audio joins) are printed. Smooth camera moves show as
smooth ramps; a single-frame spike is a flash or a jump.

Usage:  python -I tools/qa_cuts.py renders/qa.mp4
"""
import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, FPS  # noqa: E402

layout = json.loads(Path("tools/layout.json").read_text(encoding="utf-8"))["layout"]
keep = json.loads((ASSETS / "words.json").read_text(encoding="utf-8"))["keep"]
planned, acc = [row[0] for row in layout], 0.0
for a, b in keep[:-1]:
    acc += b - a
    planned.append(acc)
planned_frames = {round(t * FPS) for t in planned}

REGIONS = {
    "frame": "scale=270:480",
    "gfx": "crop=1080:960:0:0,scale=270:240",
    "inset": "crop=1080:960:0:960,scale=270:240",   # studio: camera half
}


def ydif(path, vf):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
                          vf + ",signalstats,metadata=print:key=lavfi.signalstats.YDIF", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return [float(v) for v in re.findall(r"lavfi\.signalstats\.YDIF=([0-9.]+)", out)]


for name, vf in REGIONS.items():
    v = ydif(sys.argv[1], vf)
    med = st.median(v)
    thr = max(6.0, med * 6)
    # isolated spikes only: a frame far above both neighbours (camera moves are ramps)
    spikes = [i for i in range(1, len(v) - 1) if v[i] > thr and v[i] > 2.2 * max(v[i - 1], v[i + 1], med)]
    bad = [i for i in spikes if not any(abs(i - p) <= 1 for p in planned_frames)]
    print(f"[{name}] isolated spikes={len(spikes)} unplanned={len(bad)}")
    for i in bad[:15]:
        print(f"   frame {i:4d}  t={i / FPS:6.3f}s  ydif={v[i]:5.1f}")
