"""Cut every camera to the editor's final audio and crop per layout, straight from 4K.

Reads project.json and assets/keep_final.json (from align_audio.py). Writes:
  <cam>_inset.mp4 1460x946, <cam>_cell.mp4 1080x960, <cam>_full.mp4 1080x1920,
  screen.mp4 (1080 wide) if a screen recording is set, voice.wav (the final audio),
  words.json (final transcript words + the frame-snapped keep list).

Run from the project root:  python -I tools/conform.py [output-name ...]
"""
import json
import shutil
import subprocess
import sys

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).parent))
from common import ASSETS, FPS, PROJECT, input_path

final = json.loads((ASSETS / "keep_final.json").read_text(encoding="utf-8"))
KEEP = [tuple(r) for r in final["keep"]]
if KEEP[0][0] < 0:                       # first piece may start a few ms before 0
    KEEP[0] = (0.0, KEEP[0][1] - KEEP[0][0])
# snap cuts to the frame grid so picture and sound cut at the same instants
KEEP = [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in KEEP]

SIZES = {"inset": (1460, 946), "cell": (1080, 960), "full": (1080, 1920)}


def run(args):
    print(" ".join(str(a) for a in args[:6]), "...")
    subprocess.run(args, check=True)


def select_chain(extra):
    keep = "+".join(f"gte(t,{a - 0.5 / FPS:.5f})*lt(t,{b - 0.5 / FPS:.5f})" for a, b in KEEP)
    return f"[0:v]fps={FPS},select='{keep}',setpts=N/({FPS}*TB){extra}[out]"  # fps first: a 25 fps camera must not be re-stamped as 24 fps (slow-motion drift)


def encode(src, extra, dst):
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
         "-filter_complex", select_chain(extra), "-map", "[out]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-g", str(FPS), "-an", "-movflags", "+faststart", str(dst)])


ONLY = sys.argv[1:]
jobs = []
for cam, c in PROJECT["cameras"].items():
    for kind, (ow, oh) in SIZES.items():
        if c.get(kind):
            x, y, w, h = c[kind]
            jobs.append((f"{cam}_{kind}", input_path(c["file"]), f",crop={w}:{h}:{x}:{y},scale={ow}:{oh}:flags=lanczos"))
scr = PROJECT.get("screen") or {}
if scr.get("file"):
    crop = scr.get("crop")
    pre = f",crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}" if crop else ""
    jobs.append(("screen", input_path(scr["file"]), pre + ",scale=1080:-2:flags=lanczos"))

for name, src, extra in jobs:
    if not ONLY or name in ONLY:
        encode(src, extra, ASSETS / f"{name}.mp4")

for cam in PROJECT["cameras"]:   # half-layout cells need their own file: two <video>s on one source can freeze one of them
    if (ASSETS / f"{cam}_cell.mp4").exists() and (not ONLY or f"{cam}_cell" in ONLY):
        shutil.copyfile(ASSETS / f"{cam}_cell.mp4", ASSETS / f"{cam}_half.mp4")
total = sum(b - a for a, b in KEEP)
for name, _, _ in jobs:
    if not ONLY or name in ONLY:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ASSETS / f"{name}.mp4")],
                                 capture_output=True, text=True).stdout)
        assert abs(d - total) <= 1.5 / FPS, f"{name}.mp4 is {d:.3f}s but the cut is {total:.3f}s: the picture would drift out of lip sync"
if not ONLY:
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(input_path(PROJECT["inputs"]["audio"])),
         "-af", f"apad,atrim=0:{total:.4f}", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(ASSETS / "voice.wav")])

tx = json.loads(input_path(PROJECT["inputs"]["transcript"]).read_text(encoding="utf-8"))
words = [{"w": w["word"], "s": w["start"], "e": w["end"]} for seg in tx["segments"] for w in seg["words"]]
(ASSETS / "words.json").write_text(json.dumps({"duration": round(total, 6), "keep": KEEP, "words": words}, indent=0))
joins, acc = [], 0.0
for a, b in KEEP[:-1]:
    acc += b - a
    joins.append(round(acc, 3))
print("duration", round(total, 3), "joins", joins, "words", len(words))
