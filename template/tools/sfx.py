"""Synthesize the SFX track in code (no sample files) from assets/sfx_cues.json.

Cue list: [{"t": 1.61, "type": "whoosh", "args": {...}}, ...]   t = final-timeline seconds
types: whoosh(d, lo, hi, gain) pop(f0, f1, d, gain) click(gain) tick(f, gain) chime(gain) shimmer(d, gain)
House levels: whoosh 0.13-0.22, pop 0.08-0.14, tick 0.04-0.06, chime 0.15, shimmer 0.04-0.05.
Writes assets/sfx.wav (48 kHz stereo, peak -9 dBFS) plus stems sfx_whoosh.wav and sfx_ui.wav at the same gain.

Run from the project root:  python -I tools/sfx.py
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS  # noqa: E402

SR = 48000
DUR = json.loads((ASSETS / "words.json").read_text(encoding="utf-8"))["duration"]
CUES = json.loads((ASSETS / "sfx_cues.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(7)


def env(n, attack, release):
    e = np.ones(n)
    a, r = max(1, int(attack * SR)), max(1, int(release * SR))
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * np.broadcast_to(cutoff, x.shape) / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def whoosh(d=0.6, lo=300, hi=3000, gain=0.18):
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    x = lowpass(rng.standard_normal(n), lo + (hi - lo) * np.sin(np.pi * t) ** 1.5)
    x -= lowpass(x, 120)
    return x / (np.abs(x).max() + 1e-9) * env(n, d * 0.45, d * 0.5) * gain


def pop(f0=560, f1=280, d=0.09, gain=0.12):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR)
    return x * np.exp(-t * 38) * env(n, 0.002, 0.02) * gain


def click(gain=0.18):
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return (0.6 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 260) + 0.4 * rng.standard_normal(n) * np.exp(-t * 900)) * gain


def tick(f=1900, gain=0.05):
    n = int(0.025 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 220) * gain


def chime(gain=0.15):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, a, k in [(880, 1, 5), (1320, 0.55, 6), (1760, 0.25, 8)])
    return x / 1.8 * env(n, 0.004, 0.2) * gain


def shimmer(d=0.4, gain=0.045):
    n = int(d * SR)
    x = rng.standard_normal(n)
    x -= lowpass(x, 5000)
    return x * env(n, d * 0.3, d * 0.6) * gain


SOUNDS = {"whoosh": whoosh, "pop": pop, "click": click, "tick": tick, "chime": chime, "shimmer": shimmer}
def mix(cues):
    tr = np.zeros(int(DUR * SR) + 2 * SR)
    for c in cues:
        s = SOUNDS[c["type"]](**c.get("args", {}))
        i = max(0, int(c["t"] * SR))
        tr[i:i + len(s)] += s[: len(tr) - i]
    return tr[: int(DUR * SR)]


def write(tr, name):
    stereo = np.repeat((np.clip(tr, -1, 1) * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(str(ASSETS / name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# Full mix peaks at -9 dBFS; the two stems (whooshes / everything else) share that gain, so they sum back to the mix.
full = mix(CUES)
k = 10 ** (-9 / 20) / (np.abs(full).max() + 1e-9)
write(full * k, "sfx.wav")
write(mix([c for c in CUES if c["type"] == "whoosh"]) * k, "sfx_whoosh.wav")
write(mix([c for c in CUES if c["type"] != "whoosh"]) * k, "sfx_ui.wav")
print("assets/sfx.wav + sfx_whoosh.wav + sfx_ui.wav", round(DUR, 3), "s,", len(CUES), "cues")
