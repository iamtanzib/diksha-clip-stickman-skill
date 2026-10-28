"""Cost report for a Claude Code session (what a clip actually cost, and where).

    python -I ~/.claude/skills/diksha-clip/tools/usage.py                 # latest session of the Clip 1 project folder
    python -I ~/.claude/skills/diksha-clip/tools/usage.py <session.jsonl>

Weights (input-token equivalents): cache read 0.1, input 1, cache write 2 (1 h cache), output 5.
"Baseline" is the context of the first call: system prompt + tools + connectors + skills list, paid on EVERY call.
"""
import collections
import json
import sys
from pathlib import Path

PROJ = Path.home() / ".claude/projects/E--Diksha-Nastia-Podcast-Project-File-Clips-Claude-Clip-1"
p = Path(sys.argv[1]) if len(sys.argv) > 1 else max(PROJ.glob("*.jsonl"), key=lambda f: f.stat().st_mtime)
seen, ctx, u = set(), [], collections.Counter()
tools, imgs, users = collections.Counter(), 0, 0
for line in p.open(encoding="utf-8"):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "user" and not d.get("isMeta"):
        c = d["message"].get("content")
        if isinstance(c, str):
            users += 1
        else:
            for x in c:
                if x.get("type") == "text":
                    users += 1
                if x.get("type") == "tool_result" and isinstance(x.get("content"), list):
                    imgs += sum(y.get("type") == "image" for y in x["content"])
    if d.get("type") != "assistant":
        continue
    m = d["message"]
    for c in m.get("content", []):
        if c.get("type") == "tool_use":
            tools[c["name"]] += 1
    if m.get("id") in seen:
        continue
    seen.add(m.get("id"))
    us = m.get("usage", {})
    for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
        u[k] += us.get(k, 0) or 0
    u["thinking"] += (us.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0
    ctx.append(us.get("input_tokens", 0) + us.get("cache_read_input_tokens", 0) + us.get("cache_creation_input_tokens", 0))

w = {"read": u["cache_read_input_tokens"] * 0.1, "input": u["input_tokens"], "write": u["cache_creation_input_tokens"] * 2,
     "output": u["output_tokens"] * 5}
tot = sum(w.values()) or 1
k = lambda v: f"{v / 1000:,.0f}K"
print(f"{p.name[:8]}  calls {len(seen)}  user msgs ~{users}  images {imgs}")
print(f"context: baseline {k(ctx[0]) if ctx else '-'}  avg {k(sum(ctx) / max(1, len(ctx)))}  peak {k(max(ctx or [0]))}")
print(f"output {k(u['output_tokens'])} (thinking {k(u['thinking'])})  cache read {k(u['cache_read_input_tokens'])}  cache write {k(u['cache_creation_input_tokens'])}")
print("weighted cost share: " + "  ".join(f"{n} {100 * v / tot:.0f}%" for n, v in w.items()) + f"   total {k(tot)} units")
print("tool calls: " + ", ".join(f"{n.split('__')[-1]} {c}" for n, c in tools.most_common(8)))
