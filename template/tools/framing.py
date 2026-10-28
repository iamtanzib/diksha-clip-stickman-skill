"""Framing helper for the speaker crops.

  python -I tools/framing.py grid
      One gridded still per camera (10% lines) -> qa/framing_grid.jpg. Read the head
      position of each person as fractions of the frame: hair top, chin, face centre x.

  python -I tools/framing.py suggest --cam guest --hair 0.17 --chin 0.50 --face 0.49
      Prints inset/cell/full crops by the house rules; paste them into project.json.
      Check a leaning-forward moment too: the hair must never touch the inset's top.

  python -I tools/framing.py check
      After conform: inset + cell stills of every camera at 3 times -> qa/framing_check.jpg.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, PROJECT, input_path  # noqa: E402

QA = Path("qa")
QA.mkdir(exist_ok=True)

# aspect (w/h), head share of crop height, headroom above hair (share of crop height)
RULES = {"inset": (1460 / 946, 0.44, 0.08), "cell": (1080 / 960, 0.36, 0.10), "full": (1080 / 1920, 0.30, 0.10)}


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])


def even(v):
    return int(round(v / 2) * 2)


def suggest(cam, hair, chin, face):
    fw, fh, _ = probe(input_path(PROJECT["cameras"][cam]["file"]))
    hair_px, head, face_px = hair * fh, (chin - hair) * fh, face * fw
    out = {}
    for kind, (aspect, share, room) in RULES.items():
        H = min(head / share, fh)
        W = H * aspect
        if W > fw:
            W, H = fw, fw / aspect
        y0 = min(max(hair_px - room * H, 0), fh - H)
        x0 = min(max(face_px - W / 2, 0), fw - W)
        out[kind] = [even(x0), even(y0), even(W), even(H)]
        if kind == "full" and W < 1080:
            print(f"  note: full crop is only {even(W)} px wide (will be upscaled)")
    print(json.dumps(out))


def grid():
    tiles = []
    srcs = [(cam, input_path(c["file"])) for cam, c in PROJECT["cameras"].items()]
    if (PROJECT.get("screen") or {}).get("file"):
        srcs.append(("screen", input_path(PROJECT["screen"]["file"])))
    for i, (cam, path) in enumerate(srcs):
        _, _, dur = probe(path)
        t = QA / f"_g{i}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur / 2:.2f}", "-i", str(path), "-frames:v", "1",
                        "-vf", "scale=640:-2,drawgrid=w=iw/10:h=ih/10:t=1:c=red@0.5", str(t)], check=True)
        tiles.append(t)
        print(f"tile {i}: {cam}")
    ins = sum([["-i", str(t)] for t in tiles], [])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                    "".join(f"[{i}]" for i in range(len(tiles))) + f"hstack={len(tiles)}" if len(tiles) > 1 else "null",
                    str(QA / "framing_grid.jpg")], check=True)
    for t in tiles:
        t.unlink()
    print(QA / "framing_grid.jpg")


def check():
    cams = [c for c in PROJECT["cameras"] if (ASSETS / f"{c}_inset.mp4").exists()]
    _, _, dur = probe(ASSETS / f"{cams[0]}_inset.mp4")
    rows = []
    for k, cam in enumerate(cams):
        for kind in ("inset", "cell"):
            out = QA / f"_c{k}{kind}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ASSETS / f"{cam}_{kind}.mp4"), "-vf",
                            f"select='eq(n\\,{int(dur * 24 * 0.2)})+eq(n\\,{int(dur * 24 * 0.5)})+eq(n\\,{int(dur * 24 * 0.8)})',scale=-2:240,tile=3x1",
                            "-frames:v", "1", str(out)], check=True)
            rows.append(out)
    ins = sum([["-i", str(r)] for r in rows], [])
    pads = "".join(f"[{i}]pad=2200:240[p{i}];" for i in range(len(rows)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                    pads + "".join(f"[p{i}]" for i in range(len(rows))) + f"vstack={len(rows)}", str(QA / "framing_check.jpg")], check=True)
    for r in rows:
        r.unlink()
    print(QA / "framing_check.jpg")


ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["grid", "suggest", "check"])
ap.add_argument("--cam")
ap.add_argument("--hair", type=float)
ap.add_argument("--chin", type=float)
ap.add_argument("--face", type=float)
a = ap.parse_args()
if a.cmd == "grid":
    grid()
elif a.cmd == "suggest":
    suggest(a.cam, a.hair, a.chin, a.face)
else:
    check()
