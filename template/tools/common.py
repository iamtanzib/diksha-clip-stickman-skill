"""Shared helpers for the Diksha clip tools: project config and the time map."""
import json
from pathlib import Path

ROOT = Path(".")
PROJECT = json.loads((ROOT / "project.json").read_text(encoding="utf-8"))
FPS = PROJECT.get("fps", 24)
INP = (ROOT / PROJECT["inputs"]["dir"]).resolve()
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def input_path(rel):
    return INP / rel


def load_keep():
    """Kept source ranges (frame-snapped), written by conform.py into words.json."""
    return json.loads((ASSETS / "words.json").read_text(encoding="utf-8"))["keep"]


def make_T(keep):
    """Source time -> edited time, snapped to frames (same rule as tools/kit.js)."""
    def T(x):
        acc = 0.0
        for a, b in keep:
            if a - 0.002 <= x <= b + 0.002:
                return round((acc + min(max(x, a), b) - a) * FPS) / FPS
            acc += b - a
        raise ValueError(f"time in a trimmed gap: {x}")
    return T
