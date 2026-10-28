# Stickman library (`SM`, appended to `template/tools/kit.js`)

Everything is SVG built at setup and updated from ONE `driver((t) => {...})` as pure functions of `t` (seek-safe, no GSAP on SVG).
The only GSAP in a stickman clip: `camPath` (camera), `applyLayouts()`, `SM.logoByLayout()`, and plain `tl.set`/`tl.to` on HTML if needed.
```js
const { mk, ramp, ss, spr, lin, popAt, BL, brick, brickLabel, drop, dust, makeChar, pose, AP, mixA, walkArm,
        makeCloud, cloudWords, HEART, faceCam, captions, shade, INK } = SM;
```

## Time + motion helpers
| Helper | Use |
|---|---|
| `mk(tag, parent, attrs)` | create an SVG element |
| `ramp(t, a, d)` / `ss(x)` | 0..1 ramp from a over d s / smoothstep |
| `spr(k)` | soft spring 0 -> 1 (~12% overshoot, settled ~0.7 s); k = t - start; 0 before |
| `lin([[t, v], ...])` | piecewise linear - walking positions (constant speed, so feet do not slide) |
| `popAt(el, x, y, s, rot)` | scale/rotate an SVG group about (x, y): pops `popAt(g, ox, oy, spr(t - t0))`, exits `* (1 - ss(ramp(t, tOff, 0.22)))` |
| `BL(t, seed)` | blink (1 open, 0 closed), one 0.14 s blink every 3.4 s; different seed per person |
| `drop(t, t0, H, fall = 0.4)` | y offset of something falling H px (gravity) then a small bounce; use for bricks, props, slams |
| `dust(parent)` | `.add(x, y, tLand, dir)` at setup, `.update(t)` in the driver: 4 ink puffs at a landing |

## Lego bricks
`brick(g, x, y, w, h, colour, side)` draws a front face (x, y, w, h), an oblique top (18 px right, 26 px up) with two rows of studs every
90 px, and an optional right side face. Put each brick in its own `mk("g", ...)` and move that group (`translate(0 ${drop(...)})`).
Stacking: the brick on top has its front-face bottom on the lower faces' top (`y_top + h = y_low`); it covers their studs.
Clip 1 numbers: yellow `#f2c14e` (160, 640, 360x170), coral `#e8604c` (528, 640, 360x170, side), blue `#2563eb` (160, 470, 728x170, side).
`brickLabel(g, cx, baselineY, size, colour, text)` returns a group; stamp it: `popAt(l, cx, cy, k > 0 ? 1.5 - 0.5 * spr(k) : 1.5)` +
opacity `ramp(k, 0, 0.06)`. Later "done" states: a paper tag in a top overlay SVG (rect + text + blue check path), stamped the same way.

## Stick-figure rig
`const c = makeChar(parent, { tee, bcol, pants, hair, hcol, beard, mug })` - hair `"tuft"` (reference look), `"short"`, `"pony"`, `"bun"`;
`pants: 1` = long trousers (no stick line), else shorts. Local origin = ground point between the feet; standing ~312 px tall at s = 1
(head centre 272 px above the feet, sitting: hip 64 px above the ground).
`pose(c, p)` every frame. p:
| Field | Meaning |
|---|---|
| `x, y, s` | ground position, scale (multiply by `spr(t - t0)` to pop a person in) |
| `face` | +1 faces right, -1 left; a turn = `-Math.cos(Math.PI * ss(ramp(t, t0, 0.22)))` (goes through 0 = edge-on) |
| `sit` | 0 standing .. 1 seated (thigh forward, shin down); blend over ~0.3 s to stand up / sit down |
| `amp, ph` | walk amount 0..1 and phase = distance * 0.0314 (one stride ~200 px); ramp amp in/out 0.2 s at start/stop |
| `arm(j)` | `[shoulder, elbow]` degrees for arm j (0 back, 1 front): `AP.rest/lap/counter/type/talk/up/wave/think/cup`, `walkArm(amp, ph, j)`, blend with `mixA(p1, p2, u)` |
| `lean, tilt` | upper body / head rotation in degrees (lean -12 = leaning back) |
| `look` | face offset `[fx, fy]` inside the head: [8, 0] toward where they face, [0, -4] at camera, [4, 5] looking down |
| `eye, brow, blink` | 1.45 + brow -6 = surprised; `BL(t, seed)` |
| `mood` | `"smile"`, `"big"` (laugh/excited), `"o"` (surprise), `"flat"` |
Heights to know: seated at a 64 px seat -> head top ~ ground - 256; standing head top ~ ground - 314 (at s = 1).
Draw order = z order: chairs/sofa before people, table tops / counters in a front layer after them (a counter hides a barista's legs).
Typing at a desk: desk top at seat-hip - 96 (shoulder height) and `AP.type`; hands land on the keyboard ~110 px in front of the hip.

## Clouds
`const cl = makeCloud(parent, cx, cy, rx, ry, tip, n)` - puffy cloud (n bumps), 7/8 px ink offset shadow, tail to `tip` = a point just above
the speaker's head (head top ~ ground - 256 seated). `tip = null` = thought cloud: add 3 growing circles from the head yourself.
Pop from the tip: `popAt(cl.g, cl.ox, cl.oy, spr(t - t0) * (1 - ss(ramp(t, tOff, 0.25))))`; bob idle clouds with `oy + 6 * sin(t * 3 + i)`.
`const say = cloudWords(cl, x, y0, [[["Hey,", W("hey")], ["have", W("have")]], [["Clay?", W("clay")]]], { size: 46, color: { "Clay?": "#2563eb" } })`
-> `say(t)` in the driver: each word fades in on its spoken time (layout is fixed, so lines never jump).
Lists inside a cloud: one row per item (HEART path scaled 1.35 + text 25 px 800), heart `spr` pop + text fill-opacity on its word.
Real logos inside clouds: `mk("image", cl.g, { href, x, y, width, height })` AND a static hidden `<img>` of the same file in the markup.

## Zoom-through worlds (the transition the editor loved)
A whole place (room, street, cafe) is drawn on a brick face at 1/Z scale; the camera zooms into the face until its colour becomes the
next scene's wall, travels inside, and pulls back out so the scene ends as a mural on the brick.
- Face w x h with centre (fcx, fcy), zoom Z (Clip 1: 360x170, Z = 9 -> inner face X -1620..1620, Y -285..1245, ground y 800).
- Markup: `<div class="world" id="W1" style="transform:translate(${fcx}px,${fcy - 480 / Z}px) scale(${1 / Z});opacity:0">` containing
  `<svg class="abs" style="left:-1620px;top:-285px;width:3240px;height:1530px" viewBox="-1620 -285 3240 1530">` (face size x Z).
  The inner SVG clips itself to the face. First rect = the face colour (yellow room wall for the yellow brick). Last element: an ink
  border `stroke-width="60"` so the face keeps its outline from outside.
- Camera: `const I1 = faceCam(fcx, fcy, Z);` then camPath keys `I1(X, Y = 480, k = 1)` - inner px = panel px at k = 1.
  Zoom in: `[t, I1(-1000)]` 2.2 s from an outer pose; travel: more I1 keys (1.9-2.2 s); pull back: an outer pose key (2.25 s).
- Fade the world in while the camera is diving (`W1.style.opacity = ramp(t, tZoom + 0.5, 0.5)`) and fade the face's own label out; then
  spring the scene's props in (`popAt(prop, baseX, baseY, spr(t - t_i))`, staggered ~0.08 s) so nothing appears without motion.
- Keep every inner view inside the face: |X| + 540/k <= w*Z/2, and Y range within the face. Lay places out left -> right in walking order.
- World 2 on the next brick works the same (Clip 1: coral face -> painted street wall with a poster).

## Captions + logo (template markup, keep)
- `#caps` div (CSS in the template) + `const cap = captions(CAPS, q("#caps"))`, `cap(t)` in the driver. `CAPS` = `assets/captions.json`
  from `tools/captions.py`. `captions()` logs a console error (fails check) if blocks are not back to back.
- `#logoN` (colour, overlay blend) + `#logoB` (black wordmark) imgs in the template; `SM.logoByLayout()` (after `applyLayouts()`) shows the
  black one on `half` rows and the colour one on `stack`/`full` rows.

## Recipes from Clip 1 (time anchors on words)
- Word of mouth: small clouds with the real logo pop head to head (0.35 s apart, each person turns `face` toward the previous one first),
  sparkles on the payoff word; on the negative line pop them in reverse (0.1 s apart), moods -> "flat", looks down, lamps dim, chalk
  strike on a menu board (`pathLength="1"` + dashoffset 1 -> 0).
- Infectious crowd: 6 people walking at 110 px/s; on the word each one's mood flips to "big" in a 0.17 s wave + a heart (`HEART`, scale
  2.1 * spr, rising 46 px, fading); one of them stops, arms -> `AP.think`, thought cloud with the list.
- Neon sign: group with an feGaussianBlur glow filter, opacity flicker `sin(k * 70) > 0` for 0.4 s on the word, then 1.
- Door: polygon points lerped closed -> open. Hanging sign: `popAt` with rotation `14 * exp(-3k) * sin(9k)` (swing).
- Finale slam: lift the top brick 64 px (0.22 s, ss) then `drop(t, t0, 64, 0.16)`; dust; people pop on top (`s: 0.42 * spr`), waving;
  guest avatar (bun + beard + black tee + jeans + mug) seated on the edge (`sit 1, lean -12, AP.cup`); a hand-lettered line + underline.
