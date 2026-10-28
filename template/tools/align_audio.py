"""Find where each piece of the editor's final audio comes from in the camera recording.

Splits the final audio into speech chunks (from its word-level transcript), locates
each chunk in the camera audio by normalised cross-correlation, merges neighbouring
chunks that share an offset, and writes assets/keep_final.json: [[src_start, src_end], ...]
covering the final audio's whole length. conform.py cuts every camera with it.

Run from the project root:  python -I tools/align_audio.py
"""
import json
import subprocess

import numpy as np
from scipy.signal import fftconvolve

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).parent))
from common import ASSETS, PROJECT, input_path

SR = 8000
cfg = PROJECT["inputs"]
FINAL_AUDIO = input_path(cfg["audio"])
FINAL_TX = input_path(cfg["transcript"])
SOURCE = input_path(PROJECT["cameras"][cfg.get("align_with", "guest")]["file"])


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                          "-af", "highpass=f=120,lowpass=f=3500", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def locate(chunk, src):
    c = (chunk - chunk.mean()) / (chunk.std() + 1e-9)
    num = fftconvolve(src, c[::-1], mode="valid")
    win = np.ones(len(c))
    s1 = fftconvolve(src, win, mode="valid")
    s2 = fftconvolve(src ** 2, win, mode="valid")
    std = np.sqrt(np.maximum(s2 / len(c) - (s1 / len(c)) ** 2, 1e-12))
    ncc = num / (len(c) * std)
    i = int(np.argmax(ncc))
    return i, float(ncc[i])


final, src = load(FINAL_AUDIO), load(SOURCE)
dur = len(final) / SR
words = [w for seg in json.loads(FINAL_TX.read_text(encoding="utf-8"))["segments"] for w in seg["words"]]

chunks, cur = [], [words[0]]
for w in words[1:]:
    if w["start"] - cur[-1]["end"] > 0.25:
        chunks.append(cur)
        cur = [w]
    else:
        cur.append(w)
chunks.append(cur)

found = []
for ch in chunks:
    a, b = max(0, ch[0]["start"] - 0.05), min(dur, ch[-1]["end"] + 0.05)
    i, score = locate(final[int(a * SR):int(b * SR)], src)
    off = i / SR - a
    text = " ".join(w["word"] for w in ch)
    found.append({"a": a, "b": b, "off": off, "score": score, "text": text})
    flag = "" if score >= 0.9 else "   <-- check (patched word or different take?)"
    print(f"{a:6.2f}-{b:6.2f}  src {a + off:6.2f}  ncc {score:.2f}  {text[:48]}{flag}")

pieces = []
for f in found:
    if pieces and abs(pieces[-1]["off"] - f["off"]) < 0.03:
        pieces[-1]["b"] = f["b"]
    else:
        pieces.append(dict(f))

keep = []
for k, p in enumerate(pieces):
    start = 0.0 if k == 0 else (pieces[k - 1]["b"] + p["a"]) / 2
    end = dur if k == len(pieces) - 1 else (p["b"] + pieces[k + 1]["a"]) / 2
    keep.append([round(start + p["off"], 4), round(end + p["off"], 4)])
print(f"pieces: {len(keep)}  final audio {dur:.2f}s")
for (s, e), p in zip(keep, pieces):
    print(f"  src {s:7.3f}-{e:7.3f}  {p['text'][:50]}")
(ASSETS / "keep_final.json").write_text(json.dumps({"duration": round(dur, 4), "keep": keep}, indent=1))
