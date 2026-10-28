"""Build index.html from tools/index.src.html.

- inlines tools/kit.js (animation kit) and DATA (keep list, final words, layout list)
- resolves {{T:t}} (frame-snapped final time), {{SPAN:a:b}} and {{D}} placeholders
- drops <video> tags whose asset file does not exist (e.g. no screen share in this clip)

Run from the project root:  python -I tools/build.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, FPS  # noqa: E402

data = json.loads((ASSETS / "words.json").read_text(encoding="utf-8"))
layout = json.loads(Path("tools/layout.json").read_text(encoding="utf-8"))
T = lambda x: round(x * FPS) / FPS          # final-timeline seconds, snapped to frames
acc, joins = 0.0, []
for a, b in data["keep"][:-1]:
    acc += b - a
    joins.append(round(acc * FPS) / FPS)
src = Path("tools/index.src.html").read_text(encoding="utf-8")

src = re.sub(r"\{\{T:([0-9.]+)\}\}", lambda m: f"{T(float(m.group(1))):.6f}", src)
src = re.sub(r"\{\{SPAN:([0-9.]+):([0-9.]+)\}\}", lambda m: f"{T(float(m.group(2))) - T(float(m.group(1))):.6f}", src)
src = src.replace("{{D}}", f"{data['duration']:.6f}")


def keep_video(m):
    path = re.search(r'src="(assets/[^"]+)"', m.group(0))
    return m.group(0) if not path or Path(path.group(1)).exists() else ""


src = re.sub(r"[ \t]*<video[^>]*></video>\n?", keep_video, src)
payload = {"joins": joins, "words": data["words"], "layout": layout["layout"], "fps": FPS}
src = src.replace("/*__KIT__*/", Path("tools/kit.js").read_text(encoding="utf-8"))
src = src.replace("__DATA__", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
src = src.replace("    <!-- Source file. Edit tools/index.src.html, then run: python -I tools/build.py -->\n",
                  "    <!-- Generated from tools/index.src.html by tools/build.py. Do not edit by hand. -->\n")
Path("index.html").write_text(src, encoding="utf-8")
print("index.html written:", round(data["duration"], 3), "s,", len(data["words"]), "words,", len(layout["layout"]), "layout changes")
