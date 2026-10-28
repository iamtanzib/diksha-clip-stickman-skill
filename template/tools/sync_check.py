"""Lip-sync check on a render: does the bottom-half camera show the conformed camera frame at each time? Offset in ms, 0 = in sync.
    python -I tools/sync_check.py renders/qa.mp4 guest 5,15,40      (times where that camera is in the bottom half)
Exit 1 if any offset is more than one frame. (Clip 1 v1 drifted to -1.8 s because 25 fps cameras were re-stamped as 24 fps.)"""
import subprocess, sys
import numpy as np

src, cam, times = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")]


def frames(path, vf, w=64, h=48):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"{vf},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


R = frames(src, "crop=iw:ih*0.4:0:ih*0.6")              # lower part of the bottom half (below the captions)
C = frames(f"assets/{cam}_cell.mp4", "crop=iw:ih*0.8:0:ih*0.2")
bad = False
for t in times:
    i = round(t * 24)
    lo, hi = max(0, i - 24), min(len(C), i + 25)
    j = lo + int(np.argmin([((R[i] - C[k]) ** 2).mean() for k in range(lo, hi)]))
    ms = (j - i) * 1000 / 24
    bad |= abs(ms) > 42
    print(f"t={t}s: {cam} camera frame offset {ms:+.0f} ms")
print("FAIL: out of sync" if bad else "PASS: in sync")
sys.exit(1 if bad else 0)
