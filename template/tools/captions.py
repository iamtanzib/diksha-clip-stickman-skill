"""Caption chunks from assets/words.json -> assets/captions.json ([start, end, text]); paste into the composition's CAPS.
Rules (editor's Premiere captioner look): <= 3 words, <= 16 chars, break at , . ? ! or a pause > 0.35 s, lowercase, no punctuation.
Back to back: each caption ends exactly where the next starts (gaps between blocks look unprofessional); the last one holds to the end."""
import json, re
J = json.load(open("assets/words.json", encoding="utf-8")); W, DUR = J["words"], J["duration"]
KEEP_CASE = {"I"}   # add this clip's proper nouns (product, people), e.g. {"I", "Clay"}
clean = lambda w: (lambda c: c if c in KEEP_CASE else c.lower())(re.sub(r"[^\w$']", "", w))
chunks, cur = [], []
for w in W:
    t = clean(w["w"])
    if cur and (len(cur) == 3 or len(" ".join([c["t"] for c in cur] + [t])) > 16 or re.search(r"[,.?!]$", cur[-1]["w"]) or w["s"] - cur[-1]["e"] > 0.35):
        chunks.append(cur); cur = []
    cur.append({**w, "t": t})
chunks.append(cur)
caps = []
for k, c in enumerate(chunks):
    end = chunks[k + 1][0]["s"] - 0.03 if k + 1 < len(chunks) else DUR
    caps.append([round(c[0]["s"] - 0.03, 3), round(end, 3), " ".join(x["t"] for x in c)])
assert all(a < b for a, b, _ in caps) and all(caps[i][1] == caps[i + 1][0] for i in range(len(caps) - 1)), "caption gap or zero length"
json.dump(caps, open("assets/captions.json", "w", encoding="utf-8"))
print(len(caps), "captions:", " | ".join(t for _, _, t in caps))
