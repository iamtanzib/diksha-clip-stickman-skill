"""Apply a batch of exact find/replace edits in one call (the "one patch per revision round" rule).

    python -I tools/patch.py qa/round2.patch

Patch file format (any number of blocks; the file line is optional, default tools/index.src.html):
    @@@ tools/layout.json
    <exact old text, must occur exactly once>
    ===
    <new text>
    @@@
    <next old text>
    ===
    <next new text>

All anchors are checked first; nothing is written unless every block matches exactly once.
"""
import sys
from pathlib import Path

DEFAULT = "tools/index.src.html"
blocks = Path(sys.argv[1]).read_text(encoding="utf-8").split("@@@")[1:]
files, edits = {}, []
for i, b in enumerate(blocks, 1):
    head, _, body = b.partition("\n")
    path = head.strip() or DEFAULT
    old, sep, new = body.partition("\n===\n")
    if not sep:
        sys.exit(f"block {i}: missing === separator")
    new = new[:-1] if new.endswith("\n") else new
    text = files.setdefault(path, Path(path).read_text(encoding="utf-8"))
    n = text.count(old)
    if n != 1:
        sys.exit(f"block {i} ({path}): anchor found {n} times: {old[:80]!r}")
    edits.append((path, old, new))
for path, old, new in edits:
    files[path] = files[path].replace(old, new, 1)
for path, text in files.items():
    Path(path).write_text(text, encoding="utf-8")
print(f"applied {len(edits)} edits to {', '.join(files)}")
