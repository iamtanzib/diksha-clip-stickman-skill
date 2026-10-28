// Diksha clip animation kit. Inlined into index.html by tools/build.py.
// Needs: gsap, a paused timeline `tl`, and DATA = {words, joins, layout, fps}.
// Every helper adds tweens to `tl`; times are seconds on the FINAL audio's clock.

const FPS = DATA.fps || 24;
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

// ---------- time ----------
// T(t): snap a final-timeline time to the frame grid.
const T = (t) => Math.round(t * FPS) / FPS;
// W("word", n): start time of the n-th (0-based) occurrence of a word in the final transcript.
// Matching ignores case and punctuation. Throws if missing, so typos fail at build time.
function W(word, n = 0, after = 0) {
  const norm = (s) => s.toLowerCase().replace(/[^\p{L}\p{N}%]/gu, "");
  const hits = DATA.words.filter((w) => w.s >= after && norm(w.w) === norm(word));
  if (!hits[n]) throw new Error(`word not found: "${word}" #${n} after ${after}s`);
  return T(hits[n].s);
}

// ---------- eases (LOCKED after Clips 2-5; approved first time in Clip 5 v2) ----------
// Fast start, soft tail, never a dead stop. Camera travel is slow and calm (CAMV over 1.8-2.4 s), arrivals use a soft
// spring (SSP, ~8% overshoot), morphs use ONE spring for clip + scale + position (MSP, ~3% overshoot). No squash.
// Never inOut on anything that starts on a spoken beat. Never motion blur.
const SOFT = "expo.out", GLIDE = "power3.inOut", DRIFT = "sine.inOut";
// springD(damping, omega, duration): time-based spring ease; ALWAYS tween it with that same duration.
function springD(z, w, Dur) {
  const wd = w * Math.sqrt(1 - z * z);
  return (p) => { if (p >= 1) return 1; const t = p * Dur; return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t)); };
}
// CAMV: 12% gentle ease-in, then cubic ease-out. Camera moves (1.8-2.4 s) and any long travel. Fixes "rushed / like a cut".
const CAMV = (p) => { const k = 0.12, d = 1 / ((1 - k) ** 2 * (1 + k / 2)), c = (3 * d * (1 - k) ** 2) / (2 * k); return p < k ? c * p * p : 1 - d * (1 - p) ** 3; };
const SMOOTH = (p) => p * p * (3 - 2 * p);
const SSD = 1.2, SSP = springD(0.62, 9.0, SSD);   // arrivals: cards, pills, rows, icons (~8% overshoot, settles ~1 s)
const MSD = 1.3, MSP = springD(0.74, 7.0, MSD);   // morphs + shared-element travel: ONE ease for shape, scale, position
const HEAVY = springD(0.42, 7.5, 1.4);            // heavy wobble (balance beam, weights), duration 1.4
// Old names kept so copied snippets still run; they now point at the approved values.
const SD = SSD, SPRING = SSP, BIG = MSP, CAM = CAMV, MORPH = CAMV;
const DUR = parseFloat(document.querySelector("#root").dataset.duration);
const lerp = (a, b, p) => a + (b - a) * p, clamp = (v, a, b) => Math.max(a, Math.min(b, v)), bump = (x) => Math.exp(-x * x);

// ---------- layouts ----------
// Rows from tools/layout.json: [time, "split"|"stack"|"full"|"screen", camera]
function applyLayouts(rows = DATA.layout) {
  rows.forEach(([t0, type, cam]) => {
    const t = T(t0);
    const on = (sel, v) => { if ($(sel)) tl.set(sel, { opacity: v ? 1 : 0 }, t); };
    on("#gfx", type === "split" || type === "half");
    on("#screen", type === "screen");
    on("#inset", type === "split" || type === "screen");
    on("#inset-host", cam === "host");
    on("#inset-guest", cam !== "host");
    on("#st-host", type === "stack"); on("#st-guest", type === "stack"); on("#seam", type === "stack" || type === "half");
    on("#hf-host", type === "half" && cam === "host"); on("#hf-guest", type === "half" && cam !== "host");
    on("#full-host", type === "full" && cam === "host");
    on("#full-guest", type === "full" && cam !== "host");
  });
}

// ---------- entrances / exits ----------
function blurIn(el, t, d = 0.7, y = 24) {
  tl.fromTo(el, { opacity: 0, y, filter: "blur(14px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: SOFT }, t);
}
function blurOut(el, t, d = 0.4, y = -16) {
  tl.to(el, { opacity: 0, y, filter: "blur(12px)", duration: d, ease: "power2.in" }, t);
}
function popIn(el, t, from = 0.82, d = 0.6) {
  tl.fromTo(el, { opacity: 0, scale: from, filter: "blur(8px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: d, ease: "back.out(1.6)" }, t);
}
// Words of an element (each wrapped in <span class="tw">) slide up at given times.
function wordsUp(sel, times, d = 0.4) {
  $$(sel + " .tw").forEach((w, i) => {
    w.style.display = "inline-block";
    tl.fromTo(w, { opacity: 0, y: 22, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: SOFT }, times[i] - 0.04);
  });
}
// Wrap text into <span class="tw"> words (call at setup, before wordsUp).
function splitWords(el) {
  el = typeof el === "string" ? $(el) : el;
  el.innerHTML = el.textContent.trim().split(/\s+/).map((w) => `<span class="tw">${w}</span>`).join(" ");
}

// ---------- highlights ----------
// .mark element (absolute, behind single-line text): marker sweeps open.
function sweep(el, t, d = 0.55) {
  tl.fromTo(el, { scaleX: 0 }, { scaleX: 1, duration: d, ease: "power2.inOut" }, t);
}
// .lines span (multi-line text): per-line background sweeps open.
function lineSweep(el, t, d = 0.6) {
  tl.fromTo(el, { backgroundSize: "0% 100%" }, { backgroundSize: "100% 100%", duration: d, ease: "power2.inOut" }, t);
}

// ---------- numbers ----------
function count(el, from, to, t, d, ease = "power2.out", fmt = (v) => Math.round(v).toLocaleString("en-US")) {
  el = typeof el === "string" ? $(el) : el;
  const o = { v: from };
  el.textContent = fmt(from);
  tl.to(o, { v: to, duration: d, ease, onUpdate: () => (el.textContent = fmt(o.v)) }, t);
}

// ---------- SVG ----------
function drawPath(el, t, d = 0.9, ease = "power2.inOut") {
  el = typeof el === "string" ? $(el) : el;
  const len = el.getTotalLength();
  el.style.strokeDasharray = len;
  tl.fromTo(el, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: d, ease }, t);
}
// Same, but hidden until the draw starts (round caps otherwise show a dot before the line draws).
function drawP(el, t, d = 0.9, ease = CAMV) {
  el = typeof el === "string" ? $(el) : el;
  el.style.opacity = 0;
  tl.set(el, { opacity: 1 }, t);
  drawPath(el, t, d, ease);
}

// ---------- virtual camera ----------
// A .cam element (transform-origin 0 0) holds a "world"; pose [cx, cy, s] shows world point
// (cx, cy) at the centre of the graphics area at zoom s. Focal point travels in a straight line.
const VCX = 540, VCY = 480;   // studio: the graphics panel is the top half (1080x960)
const camPose = ([cx, cy, s]) => ({ x: VCX - s * cx, y: VCY - s * cy, scale: s });
// keys: [time, pose, duration = 2.0, ease = CAMV]; the first key is the starting pose. Keys must not overlap.
// House pace: few, long, calm moves (1.8-2.4 s); zoom <= 1.08 on full-width UI; never while a strip/list travels.
function camPath(el, keys) {
  tl.set(el, camPose(keys[0][1]), keys[0][0]);
  for (let i = 1; i < keys.length; i++) {
    const [t, pose, d = 2.0, ease = CAMV] = keys[i];
    if (i + 1 < keys.length && t + d > keys[i + 1][0] + 0.01) console.error(`CAMPATH key ${i} (${t.toFixed(2)}+${d}) runs into key ${i + 1} (${keys[i + 1][0].toFixed(2)})`);
    tl.fromTo(el, camPose(keys[i - 1][1]), { ...camPose(pose), duration: d, ease }, t);
  }
}

// ---------- cursor ----------
// pts: [time, x, y, duration] in the cursor's parent coordinates.
function cursorPath(cur, pts) {
  const [t0, x0, y0] = pts[0];
  tl.fromTo(cur, { x: x0, y: y0, opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power1.out", immediateRender: false }, t0);
  for (let i = 1; i < pts.length; i++) {
    const [t, x, y, d] = pts[i];
    tl.fromTo(cur, { x: pts[i - 1][1], y: pts[i - 1][2] }, { x, y, duration: d, ease: GLIDE, immediateRender: false }, t);
  }
}
function click(cur, rip, t, x, y) {
  tl.to(cur, { scale: 0.82, duration: 0.09, ease: "power2.out" }, t);
  tl.to(cur, { scale: 1, duration: 0.18, ease: "power2.out" }, t + 0.09);
  tl.fromTo(rip, { left: x, top: y, scale: 0.3, opacity: 0.9 }, { scale: 1.4, opacity: 0, duration: 0.55, ease: "power2.out", immediateRender: false }, t);
}

// ---------- ambience ----------
function drift(el, t, d, to = 1.025) {
  tl.fromTo(el, { scale: 1 }, { scale: to, duration: d, ease: "none" }, t);
}
// seeded random for deterministic scatter
function rng(seed = 7) {
  return () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
}

// ---------- motion system ----------
// Squash before a morph was REJECTED twice (Clip 4, Clip 5). Kept only so old code fails loudly.
function squash() { throw new Error("squash() is rejected by the editor: use morph() (one element, one spring)"); }

// clip-path inset string that the browser never collapses (all-equal insets get shortened and GSAP mis-pairs them).
function ins(t, r, b, l, R = 0) {
  const v = [t, r + 0.01, b + 0.02, l + 0.03].map((x) => x.toFixed(2) + "px");
  return `inset(${v.join(" ")} round ${Math.max(0, R).toFixed(2)}px)`;
}
// THE house morph (editor loved it in Clip 4/5): ONE element whose clip-path, scale and position run on the SAME
// spring (MSP, 1.3 s). Give the element 30-40 px spare room so the overshoot shows. from/to must both state every
// animated prop (explicit start = no snap on cold seeks). Content inside crossfades in ~0.3 s later (softIn).
function morph(el, t, from, to) {
  if (("clipPath" in to) !== ("clipPath" in from)) throw new Error("morph(): give clipPath in BOTH from and to");
  tl.fromTo(el, from, { ...to, duration: MSD, ease: MSP, immediateRender: false }, t);
}
// Shared element (title, photo, avatar, thumbnail) travelling with a morph: same spring, same start.
function flip(el, t, to, from = { x: 0, y: 0, scale: 1 }) {
  tl.fromTo(el, from, { ...to, duration: MSD, ease: MSP, immediateRender: false }, t);
}
// Arrival with the soft spring. from: any props; they settle to opacity 1 / scale 1 / 0 / blur(0).
function landS(el, t, from = { opacity: 0, scale: 0.7, y: 24 }) {
  const to = { opacity: 1, scale: 1, y: 0, duration: SSD, ease: SSP };
  Object.keys(from).forEach((k) => { if (!(k in to)) to[k] = k === "filter" ? "blur(0px)" : 0; });
  tl.fromTo(el, from, to, t);
}
const land = landS;
function softIn(el, t, d = 0.6, y = 14) { tl.fromTo(el, { opacity: 0, y }, { opacity: 1, y: 0, duration: d, ease: SOFT }, t); }
function fadeOut(el, t, d = 0.45) { tl.to(el, { opacity: 0, filter: "blur(10px)", duration: d, ease: "power2.in" }, t); }

// ---------- per-frame geometry (seek-safe, for anything that follows something else) ----------
// K([[t0, v0], [t, v, dur = 0.6, ease = CAMV], ...]) -> pure function of time. A key starts from the value at its start,
// so keys may interrupt each other without jumps. Use with driver() for cursors, pins, shapes computed every frame.
function K(keys) {
  const sv = [keys[0][1]];
  const f = (t, upto) => {
    let v = keys[0][1];
    for (let i = 1; i < upto; i++) {
      const [ti, vi, d = 0.6, e = CAMV] = keys[i];
      if (t <= ti) break;
      v = sv[i] + (vi - sv[i]) * e(Math.min(1, (t - ti) / d));
    }
    return v;
  };
  for (let i = 1; i < keys.length; i++) sv[i] = f(keys[i][0], i);
  return (t) => f(t, keys.length);
}
const place = (el, x, y, r = 0) => { el.style.transform = `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) rotate(${r.toFixed(3)}deg)`; };
const placeC = (el, x, y, s = 1) => { el.style.transform = `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) scale(${s.toFixed(4)})`; };
// Call fn(t) every frame for the whole clip (one driver per clip; put all per-frame code in fn).
function driver(fn) {
  const o = { v: 0 };
  tl.fromTo(o, { v: 0 }, { v: 1, duration: DUR, ease: "none", onUpdate() { fn(this.time()); } }, 0);
  fn(0);
}
// Hesitating cursor wobble (Diksha's photo cursor "choosing"): add to the cursor position between a and b.
function hesitate(t, a, b, amp = 7) {
  const env = clamp((t - a) / 0.4, 0, 1) * clamp((b - t) / 0.3, 0, 1);
  return [env * amp * Math.sin(t * 2 * Math.PI * 1.4), env * amp * 0.7 * Math.sin(t * 2 * Math.PI * 1.1 + 1.3)];
}
// Breathing camera: three out-of-phase sine sways so the frame is never dead between beats.
// Amplitude is small on purpose (everything must stay in frame): +-9 px x, +-8 px y, 3% scale.
function breathe(el, a, b) {
  const n = (per) => Math.ceil((b - a) / per);
  tl.fromTo(el, { x: -9 }, { x: 9, duration: 2.9, ease: "sine.inOut", yoyo: true, repeat: n(2.9), transformOrigin: "540px 640px" }, a);
  tl.fromTo(el, { y: 8 }, { y: -8, duration: 2.3, ease: "sine.inOut", yoyo: true, repeat: n(2.3) }, a);
  tl.fromTo(el, { scale: 1 }, { scale: 1.03, duration: 3.7, ease: "sine.inOut", yoyo: true, repeat: n(3.7) }, a);
}
// Overlap audit: two tweens animating the same property of the same element at the same time fight each other
// (the later one wins, then the earlier one snaps back = "broken mid-animation"). Call once after building the
// timeline; problems print as console errors and are listed in window.__overlaps.
function auditOverlaps() {
  const meta = new Set(["ease", "duration", "delay", "repeat", "yoyo", "stagger", "onUpdate", "onComplete", "onStart", "immediateRender", "transformOrigin", "keyframes", "overwrite", "callbackScope",
    "parent", "startAt", "data", "id", "lazy", "paused", "runBackwards", "inherit", "yoyoEase", "repeatDelay", "repeatRefresh", "onUpdateParams", "onCompleteParams", "onReverseComplete", "onRepeat"]);
  const rows = [];
  tl.getChildren(true, true, false).forEach((tw) => {
    const s = tw.startTime(), e = s + tw.totalDuration();
    let props = Object.keys(tw.vars).filter((k) => !meta.has(k));
    if (tw.vars.keyframes) props = Object.keys(tw.vars.keyframes[0] || {}).filter((k) => !meta.has(k));
    if (props.includes("scale")) props.push("scaleX", "scaleY");
    tw.targets().forEach((tg) => props.forEach((p) => rows.push({ id: tg.id || tg.className || "obj", tg, p, s, e })));
  });
  const out = [];
  rows.sort((a, b) => a.s - b.s);
  for (let i = 0; i < rows.length; i++) for (let j = i + 1; j < rows.length; j++) {
    const A = rows[i], B = rows[j];
    if (B.s >= A.e - 0.02) break;
    if (A.tg === B.tg && A.p === B.p && A.e - A.s > 0.001 && B.e - B.s > 0.001)
      out.push(`#${A.id} "${A.p}" ${A.s.toFixed(2)}-${A.e.toFixed(2)} overlaps ${B.s.toFixed(2)}-${B.e.toFixed(2)}`);
  }
  window.__overlaps = out;
  out.forEach((m) => console.error("OVERLAP " + m));
  return out;
}

// =====================================================================================================
// STICKMAN LIBRARY (diksha-clip-stickman) - the illustrated building blocks of the approved Munnawar Clip 1 v2.
// One namespace so nothing clashes with clip code. In the composition block:
//   const { mk, ramp, ss, spr, lin, popAt, BL, brick, brickLabel, drop, dust, makeChar, pose, AP, mixA, walkArm,
//           makeCloud, cloudWords, HEART, faceCam, captions, logoByLayout } = SM;
// Everything is SVG, set from ONE driver() as pure functions of t (seek-safe). API: references/stickman-api.md
// =====================================================================================================
const SM = (() => {
  const NS = "http://www.w3.org/2000/svg", INK = "#1a1a1a", D2R = Math.PI / 180;
  const mk = (tag, parent, a = {}) => { const e = document.createElementNS(NS, tag); for (const k in a) e.setAttribute(k, a[k]); parent.appendChild(e); return e; };
  const ramp = (t, a, d) => clamp((t - a) / d, 0, 1);
  const ss = (x) => x * x * (3 - 2 * x);
  const spr = (k) => (k <= 0 ? 0 : 1 - Math.exp(-6 * k) * Math.cos(9 * k));       // soft spring 0 -> 1, ~12% overshoot, settled ~0.7 s
  const lin = (keys) => (t) => {                                                    // piecewise linear [[t, v], ...] (constant walking speed)
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) if (t < keys[i][0]) return lerp(keys[i - 1][1], keys[i][1], (t - keys[i - 1][0]) / (keys[i][0] - keys[i - 1][0]));
    return keys[keys.length - 1][1];
  };
  const popAt = (e, x, y, s, r = 0) => e.setAttribute("transform", `translate(${x} ${y}) rotate(${r.toFixed(2)}) scale(${Math.max(0.0001, s).toFixed(4)}) translate(${-x} ${-y})`);
  const BL = (t, sd) => { const u = (t + sd) % 3.4; return u < 0.14 ? Math.abs(u - 0.07) / 0.07 : 1; };   // blink, seed per person

  // ---------- Lego bricks: front face (x, y, w, h), oblique top with two rows of studs, optional right side ----------
  const shade = (hex, f) => {
    const n = parseInt(hex.slice(1), 16), m = (c) => Math.round(f > 0 ? c + (255 - c) * f : c * (1 + f));
    return `rgb(${m(n >> 16)},${m((n >> 8) & 255)},${m(n & 255)})`;
  };
  function brick(g, x, y, w, h, col, side) {
    const D = 18, T0 = 26, n = Math.round(w / 90), st = { stroke: INK, "stroke-width": 5, "stroke-linejoin": "round" };
    mk("path", g, { d: `M${x} ${y}L${x + D} ${y - T0}L${x + w + D} ${y - T0}L${x + w} ${y}Z`, fill: shade(col, 0.28), ...st });
    if (side) mk("path", g, { d: `M${x + w} ${y}L${x + w + D} ${y - T0}L${x + w + D} ${y + h - T0}L${x + w} ${y + h}Z`, fill: shade(col, -0.22), ...st });
    [[19, 13], [7, 5]].forEach(([d, off]) => {
      for (let i = 0; i < n; i++) {
        const cx = x + (w / n) * (i + 0.5) + off, sy = y - d;
        mk("path", g, { d: `M${cx - 22} ${sy - 13}V${sy}A22 7 0 0 0 ${cx + 22} ${sy}V${sy - 13}`, fill: shade(col, 0.1), stroke: INK, "stroke-width": 4 });
        mk("ellipse", g, { cx, cy: sy - 13, rx: 22, ry: 7, fill: shade(col, 0.42), stroke: INK, "stroke-width": 4 });
      }
    });
    mk("rect", g, { x, y, width: w, height: h, rx: 6, fill: col, ...st });
    mk("path", g, { d: `M${x + 14} ${y + 14}H${x + w * 0.45}`, stroke: "#fff", "stroke-width": 6, "stroke-linecap": "round", opacity: 0.35 });
  }
  const brickLabel = (g, x, y, size, col, txt) => {
    const w = mk("g", g);
    mk("text", w, { x, y, "text-anchor": "middle", "font-family": "DM Sans Brand", "font-size": size, "font-weight": 800, fill: col }).textContent = txt;
    return w;   // stamp it in the driver: popAt(w, cx, cy, k > 0 ? 1.5 - 0.5 * spr(k) : 1.5) + opacity ramp
  };
  // y offset of a dropped object: falls H px in `fall` s (gravity), then a small bounce
  const drop = (t, t0, H, fall = 0.4) => {
    if (t < t0) return -H;
    const u = (t - t0) / fall;
    if (u < 1) return -H * (1 - u * u);
    const k = t - t0 - fall;
    return -16 * Math.exp(-k * 7) * Math.abs(Math.sin(k * 11));
  };
  function dust(parent) {   // puffs where something lands: add(x, y, tLand, dir) at setup, update(t) in the driver
    const g = mk("g", parent), puffs = [];
    return {
      add(x, y, t0, dir) { for (let i = 0; i < 4; i++) puffs.push({ c: mk("circle", g, { r: 0, fill: "#f7f3ea", stroke: INK, "stroke-width": 3 }), x, y, t0, dx: dir * (14 + i * 16), dy: -6 - (i % 2) * 12 }); },
      update(t) {
        puffs.forEach((p) => {
          const k = t - p.t0, on = k > 0 && k < 0.8, u = ss(clamp(k / 0.8, 0, 1));
          p.c.setAttribute("r", on ? (5 + 12 * u).toFixed(1) : 0);
          p.c.setAttribute("cx", (p.x + p.dx * u).toFixed(1)); p.c.setAttribute("cy", (p.y + p.dy * u).toFixed(1));
          p.c.setAttribute("opacity", on ? (1 - k / 0.8).toFixed(3) : 0);
        });
      },
    };
  }

  // ---------- stick-figure rig (editor's reference: big round white head, thin limbs, tee, shorts/pants, white sneakers) ----------
  // Local coords: origin = between the feet on the ground, y up is negative; standing height ~312 px at s = 1.
  const TH = 62, SHN = 60, UA = 50, FA = 46;
  const SHOE = "M-10 -12Q0 -17 10 -11L27 -5Q32 4 22 5L-11 5Q-15 -4 -10 -12Z";
  const TEE = "M-15 -96Q0 -88 15 -96L37 -88L33 8L-33 8L-37 -88Z";
  const TUFT = "M-6 -43Q-10 -60 -20 -66M1 -44Q1 -63 -4 -72M8 -43Q15 -58 25 -61";
  const CAP = "M-45 -2Q-50 -50 0 -48Q48 -50 45 -2Q37 -30 4 -31Q-30 -30 -45 -2Z";
  const PONY = "M-36 -24Q-76 -14 -66 36Q-56 10 -40 4Z";
  const BEARD = "M-35 6Q-30 44 2 48Q32 44 37 6Q27 26 2 28Q-24 26 -35 6Z";
  const BROW = "M-22 -17Q-15 -22 -7 -18M8 -18Q16 -22 23 -17";
  const MOUTH = { smile: ["M-10 14Q3 24 15 13", "none"], big: ["M-13 10Q3 36 19 10Z", INK], o: ["M-3 17a6 7 0 1 0 12 0a6 7 0 1 0 -12 0Z", INK], flat: ["M-8 16L13 15", "none"] };
  // o: { tee, bcol (shorts/pants colour), pants: true for long trousers, hair: "tuft" | "short" | "pony" | "bun", hcol, beard, mug }
  function makeChar(parent, o) {
    const r = mk("g", parent), c = { o, r }, W0 = o.pants ? 24 : 30, rc = { "stroke-linecap": "round", "stroke-linejoin": "round", fill: "none" };
    c.legs = [0, 1].map(() => ({
      u: mk("path", r, { ...rc, stroke: INK, "stroke-width": W0 + 9 }),
      v: mk("path", r, { ...rc, stroke: o.bcol, "stroke-width": W0 }),
      l: mk("path", r, { ...rc, stroke: INK, "stroke-width": o.pants ? 0 : 5 }),
      s: mk("path", r, { d: SHOE, fill: "#fff", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }),
    }));
    c.b = mk("g", r);
    mk("path", c.b, { d: "M-31 -8H31V12H-31Z", fill: o.bcol, stroke: INK, "stroke-width": 5, "stroke-linejoin": "round" });
    mk("path", c.b, { d: "M0 -96V-110", stroke: INK, "stroke-width": 5 });
    mk("path", c.b, { d: TEE, fill: o.tee, stroke: INK, "stroke-width": 5, "stroke-linejoin": "round" });
    c.arms = [0, 1].map(() => ({
      u: mk("path", c.b, { ...rc, stroke: INK, "stroke-width": 31 }),
      v: mk("path", c.b, { ...rc, stroke: o.tee, "stroke-width": 22 }),
      l: mk("path", c.b, { ...rc, stroke: INK, "stroke-width": 5 }),
      h: mk("circle", c.b, { r: 6.5, fill: "#fff", stroke: INK, "stroke-width": 4 }),
    }));
    if (o.mug) c.mug = mk("path", c.b, { d: "M-10 -16h20v17a5 5 0 0 1 -5 5h-10a5 5 0 0 1 -5 -5zM10 -11a5 5 0 0 1 0 10", fill: "#fff", stroke: INK, "stroke-width": 3.5 });
    c.h = mk("g", c.b);
    if (o.hair === "pony") mk("path", c.h, { d: PONY, fill: o.hcol, stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" });
    if (o.hair === "bun") mk("circle", c.h, { cx: -18, cy: -50, r: 15, fill: o.hcol, stroke: INK, "stroke-width": 4 });
    mk("circle", c.h, { r: 44, fill: "#fff", stroke: INK, "stroke-width": 5 });
    if (o.hair === "tuft") mk("path", c.h, { d: TUFT, ...rc, stroke: INK, "stroke-width": 4 });
    else mk("path", c.h, { d: CAP, fill: o.hcol, stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" });
    c.f = mk("g", c.h);
    c.eyes = [-13, 15].map((x) => mk("ellipse", c.f, { cx: x, cy: -2, rx: 4.6, ry: 6.5, fill: INK }));
    c.brow = mk("path", c.f, { d: BROW, ...rc, stroke: INK, "stroke-width": 4 });
    if (o.beard) mk("path", c.f, { d: BEARD, fill: o.hcol, stroke: INK, "stroke-width": 3 });
    c.m = mk("path", c.f, { stroke: INK, "stroke-width": 4.5, "stroke-linecap": "round", "stroke-linejoin": "round" });
    return c;
  }
  // arm poses (t, j) -> [shoulder, elbow] degrees from straight down, + = forward; j = 0 back arm, 1 front arm
  const AP = {
    rest: () => [6, 10], lap: () => [42, 44], counter: () => [52, 28],
    type: (t, j) => [70, 60 + 7 * Math.sin(t * 22 + j * 2.1)],
    talk: (t, j) => (j ? [74 + 14 * Math.sin(t * 4.2), 66] : [14, 22]),
    up: (t, j) => [158 + 7 * Math.sin(t * 8 + j * 1.7), 14],
    wave: (t, j) => (j ? [152, 22 + 32 * Math.sin(t * 9)] : [6, 10]),
    think: (t, j) => (j ? [128, 128] : [24, 64]),
    cup: (t, j) => (j ? [40, 105] : [-46, 30]),
  };
  const mixA = (p1, p2, u) => [lerp(p1[0], p2[0], u), lerp(p1[1], p2[1], u)];
  const walkArm = (amp, ph, j) => [-amp * 22 * Math.sin(ph + j * Math.PI), 12 + 8 * amp];   // arms swing against the legs
  // p: { x, y (ground), s, face (+1 right / -1 left; animate through 0 with -cos(PI*u) for a turn), sit 0..1, amp (walk 0..1),
  //      ph (walk phase = distance * 0.0314), arm: (j) => [a, b], lean, tilt, look [fx, fy], eye (1, 1.45 = wide), blink, brow (y), mood }
  function pose(c, p) {
    const amp = p.amp || 0, sit = p.sit || 0, ph = p.ph || 0, s = Math.max(p.s ?? 1, 0.0001);
    const hy = lerp(-122, -64, sit) - amp * 5 * Math.abs(Math.cos(ph));
    c.r.setAttribute("transform", `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) scale(${(p.face * s).toFixed(4)} ${s.toFixed(4)})`);
    c.legs.forEach((L, j) => {
      const q = ph + j * Math.PI, ox = j ? 11 : -11;
      const a = lerp(amp * 24 * Math.sin(q), 88, sit), b = lerp(-amp * 34 * Math.max(0, Math.cos(q)), -88, sit);
      const kx = ox + TH * Math.sin(a * D2R), ky = hy + TH * Math.cos(a * D2R);
      const fx = kx + SHN * Math.sin((a + b) * D2R), fy = ky + SHN * Math.cos((a + b) * D2R);
      const leg = `M${ox} ${hy.toFixed(1)}L${kx.toFixed(1)} ${ky.toFixed(1)}L${fx.toFixed(1)} ${fy.toFixed(1)}`;
      const cl = c.o.pants ? leg : `M${ox} ${hy.toFixed(1)}L${(ox + (kx - ox) * 0.55).toFixed(1)} ${(hy + (ky - hy) * 0.55).toFixed(1)}`;
      L.u.setAttribute("d", cl); L.v.setAttribute("d", cl); L.l.setAttribute("d", leg);
      L.s.setAttribute("transform", `translate(${fx.toFixed(1)} ${(fy - 4).toFixed(1)}) rotate(${(-(a + b) * 0.25).toFixed(1)})`);
    });
    c.b.setAttribute("transform", `translate(0 ${hy.toFixed(1)}) rotate(${(p.lean || 0).toFixed(1)})`);
    c.arms.forEach((A, j) => {
      const [sa, sb] = p.arm ? p.arm(j) : AP.rest(), sx = j ? 29 : -29, sy = -84;
      const ex = sx + UA * Math.sin(sa * D2R), ey = sy + UA * Math.cos(sa * D2R);
      const hx = ex + FA * Math.sin((sa + sb) * D2R), hy2 = ey + FA * Math.cos((sa + sb) * D2R);
      A.l.setAttribute("d", `M${sx} ${sy}L${ex.toFixed(1)} ${ey.toFixed(1)}L${hx.toFixed(1)} ${hy2.toFixed(1)}`);
      const sl = `M${sx} ${sy}L${(sx + (ex - sx) * 0.4).toFixed(1)} ${(sy + (ey - sy) * 0.4).toFixed(1)}`;
      A.u.setAttribute("d", sl); A.v.setAttribute("d", sl);
      A.h.setAttribute("cx", hx.toFixed(1)); A.h.setAttribute("cy", hy2.toFixed(1));
      if (j && c.mug) c.mug.setAttribute("transform", `translate(${hx.toFixed(1)} ${(hy2 - 2).toFixed(1)})`);
    });
    c.h.setAttribute("transform", `translate(0 -150) rotate(${(p.tilt || 0).toFixed(1)})`);
    const lk = p.look || [6, 0], ey = p.eye || 1;
    c.f.setAttribute("transform", `translate(${lk[0].toFixed(1)} ${lk[1].toFixed(1)})`);
    c.eyes.forEach((e) => { e.setAttribute("ry", (6.5 * ey * (p.blink ?? 1)).toFixed(2)); e.setAttribute("rx", (4.6 * ey).toFixed(2)); });
    c.brow.setAttribute("transform", `translate(0 ${(p.brow || 0).toFixed(1)})`);
    const [md, mf] = MOUTH[p.mood || "smile"];
    c.m.setAttribute("d", md); c.m.setAttribute("fill", mf);
  }

  // ---------- cloud bubbles (editor's reference: puffy cloud, offset ink shadow, tail to the speaker's head) ----------
  const cloudD = (cx, cy, rx, ry, n) => {
    let d = "";
    const r = ((2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2)) / n) * 0.62;
    for (let i = 0; i <= n; i++) {
      const a = (i / n) * 2 * Math.PI + 0.3, x = (cx + rx * Math.cos(a)).toFixed(1), y = (cy + ry * Math.sin(a)).toFixed(1);
      d += i ? `A${r.toFixed(1)} ${r.toFixed(1)} 0 0 1 ${x} ${y}` : `M${x} ${y}`;
    }
    return d + "Z";
  };
  // tip = [x, y] just above the speaker's head (null = thought cloud: add your own little circles). Pop: popAt(c.g, c.ox, c.oy, spr(t - t0)).
  function makeCloud(parent, cx, cy, rx, ry, tip, n = 9) {
    const g = mk("g", parent, { transform: "scale(0.0001)" }), d = cloudD(cx, cy, rx, ry, n);
    let tail = "";
    if (tip) {
      const bx = cx + (tip[0] - cx) * 0.35, by = cy + ry * 0.78;
      tail = `M${bx - 22} ${by}Q${(bx + tip[0]) / 2 - 6} ${(by + tip[1]) / 2} ${tip[0]} ${tip[1]}Q${(bx + tip[0]) / 2 + 14} ${(by + tip[1]) / 2} ${bx + 24} ${by}`;
    }
    mk("path", g, { d: d + tail, fill: INK, transform: "translate(7 8)" });
    mk("path", g, { d, fill: "#fff", stroke: INK, "stroke-width": 5, "stroke-linejoin": "round" });
    if (tip) { mk("path", g, { d: tail + "Z", fill: "#fff" }); mk("path", g, { d: tail, fill: "none", stroke: INK, "stroke-width": 5, "stroke-linejoin": "round", "stroke-linecap": "round" }); }
    return { g, ox: tip ? tip[0] : cx, oy: tip ? tip[1] : cy + ry };
  }
  // words that type on as they are spoken: lines = [[["Hey,", W("hey")], ["have", W("have")]], [...]]; returns update(t) for the driver
  function cloudWords(cloud, x, y0, lines, o = {}) {
    const size = o.size || 46, lh = o.lh || Math.round(size * 1.22), col = o.color || {}, words = [];
    lines.forEach((ws, li) => {
      const tx = mk("text", cloud.g, { x, y: y0 + li * lh, "text-anchor": "middle", "font-family": "DM Sans Brand", "font-size": size, "font-weight": 800, fill: INK });
      ws.forEach(([w, tw], wi) => { const s = mk("tspan", tx, { "fill-opacity": 0, fill: col[w] || INK }); s.textContent = (wi ? " " : "") + w; words.push([s, tw]); });
    });
    return (t) => words.forEach(([s, tw]) => s.setAttribute("fill-opacity", ramp(t, tw - 0.04, 0.15).toFixed(3)));
  }
  const HEART = "M0 8C-14 -2 -12 -12 -5 -12C-2 -12 0 -10 0 -8C0 -10 2 -12 5 -12C12 -12 14 -2 0 8Z";

  // ---------- zoom-through worlds: a scene drawn at 1/Z scale on a face (centre fcx, fcy); camera keys into it ----------
  // world div: style="transform:translate(${fcx}px,${fcy - 480 / Z}px) scale(${1 / Z})"; its SVG viewBox covers the face:
  // x -w*Z/2..w*Z/2, y 480-h*Z/2..480+h*Z/2 (face w x h). Inside, inner px = panel px at k = 1.
  const faceCam = (fcx, fcy, Z) => (X, Y = 480, k = 1) => [fcx + X / Z, fcy + (Y - 480) / Z, Z * k];

  // ---------- captions + channel logo ----------
  function captions(CAPS, el) {   // CAPS = assets/captions.json ([start, end, text], back to back); returns update(t)
    for (let i = 0; i + 1 < CAPS.length; i++) if (CAPS[i][1] !== CAPS[i + 1][0]) console.error(`CAPTIONS gap after "${CAPS[i][2]}"`);
    return (t) => { const c = CAPS.find(([a, b]) => t >= a && t < b), s = c ? c[2] : ""; if (el.textContent !== s) el.textContent = s; };
  }
  function logoByLayout(normal = "#logoN", black = "#logoB") {   // black wordmark over the animation (half), colour logo over camera-only frames
    DATA.layout.forEach(([t0, type]) => { tl.set(normal, { opacity: type === "half" ? 0 : 1 }, T(t0)); tl.set(black, { opacity: type === "half" ? 1 : 0 }, T(t0)); });
  }

  return { NS, INK, mk, ramp, ss, spr, lin, popAt, BL, shade, brick, brickLabel, drop, dust, makeChar, pose, AP, mixA, walkArm, makeCloud, cloudWords, HEART, faceCam, captions, logoByLayout };
})();
