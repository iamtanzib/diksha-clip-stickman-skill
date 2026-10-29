# Stickman style - The Quest with Diksha (studio episodes)

Studio episodes: Diksha and the guest meet in person, no screen share. This style is separate from the online style (`diksha-clip`,
online episodes): never bring the online UI-card look into a studio clip, and never bring this look into an online clip.
Written 2026-10-28 from the editor's notes on Munnawar Clip 1 v1. Clip 1 v2 in this style was approved with no notes ("better than what
I wanted"). Its building blocks are now the `SM` library in the template kit (references/stickman-api.md): bricks, the stick-figure rig,
clouds, zoom-through worlds, captions, logo. The Clip 1 composition (`D:\Diksha\Podcast 2\Clips\Clip 1\videos\clip1\tools\index.src.html`)
is the full worked example (inline copies of the same helpers).

## Layouts (1080x1920, 24 fps)
| Layout | On screen | Use for |
|---|---|---|
| **half** | animation 1080x960 on top, speaker camera (cell crop) 1080x960 below, 6 px white seam | every explained idea (default) |
| **stack** | Diksha + guest halves | the opening line, pure back-and-forth with no idea to draw |
| **full** | one person full frame | rarely, one punchy line |

- No inset-card (`split`) layout in studio clips.
- **Diksha 3-4 times per clip**: it is her channel. Cut the bottom half to her camera for reactions (smiles, nods) and her own lines,
  1-2 s each, while the animation keeps running. Reaction cuts may land mid-sentence of the guest; speaker cuts land in pauses.
- Graphics live in y 40-920 of the top half. Keep the animation running to the last frame.

## Captions (burned in, the editor's Premiere caption style)
- DM Sans Bold (700), 92 px at 1080 wide, letter-spacing -0.02em (-0.08em read as cramped), white, no stroke, no background,
  soft black shadow: `text-shadow: 3px 4px 10px rgba(0,0,0,.55), 0 0 26px rgba(0,0,0,.45), 2px 6px 40px rgba(0,0,0,.35)`.
- One line, centred on the half/stack seam (box top 916, height 92): never over a face, readable on both halves.
- Chunks from `python -I tools/captions.py` (<= 3 words, <= 16 chars, break at punctuation / pauses > 0.35 s, lowercase, no punctuation;
  add the clip's proper nouns to `KEEP_CASE`). Static per chunk, no animation. Set the text from the driver.
- **Back to back, never a gap**: each caption ends exactly where the next starts; the last holds to the end (empty frames between
  blocks looked unprofessional). captions.py asserts it.
- `hyperframes check` flags the captions for contrast (it ignores text-shadow): known and accepted, it is the editor's exact style.
  qa.py stops at that gate, so run the draft render / motion_check / sheet steps directly afterwards.

## Logo (top right)
- Over the animation (`half`): black wordmark only, no ring - `assets/logo/quest_wordmark_black.png`, left 853, top 84, width 173.
- Over camera-only layouts (`stack`, `full`): the normal logo (gradient ring + white wordmark) - `assets/logo/quest_logo.png`, left 800, top 24, 250x250,
  `mix-blend-mode: overlay` so it sits in the footage.
- Switch with the layout rows: `tl.set` opacity on each row time (both images always in the DOM).

## Look: hand-drawn illustration, not UI
- **No UI**: no cards, pills, chips, chat rectangles, dashboards, avatar discs, stat tiles. The editor rejected that look for studio talk.
- **Real logos only on their beat**: a product's real logo appears where the product itself is the subject (e.g. the word-of-mouth beat),
  not on the frame where its name is merely said.
- **Line art**: ink outlines `#1a1a1a`, 5-6 px at 1080 wide, round caps/joins; flat fills; soft drop shadows only; warm paper background.
- **Characters**: stick-figure people in the reference style - big round white head with a simple face (dot eyes, curved brows, small smile),
  thin limb lines, black t-shirt, denim shorts, white sneakers. Vary hair/clothes per person (the guest's avatar can carry his look:
  long hair tied back, black tee). Never generic avatar icons.
- **Speech**: cloud-shaped bubbles with an offset ink shadow and a tail, rising out of the speaker's head (scale up from the head, then text).
- **Scenes**: illustrated places drawn in the same line style - room, street, café (reference: line-art people in a warm café with pendant
  lamps, a menu board, plants, wooden tables, olive and beige tones).
- **Palette**: paper `#f7f3ea`, ink `#1a1a1a`, olive `#6b7a4b`, beige `#e8dcc8`, wood `#c9a77c`, denim `#4f7cac`, warm yellow `#f2c14e`,
  coral `#e8604c`, brand blue `#2563eb` for highlights only.
- **Type**: DM Sans, few words, 700-800, may sit on drawn objects (brick faces, signs, menu boards) instead of floating headlines.

## Motion: real animation
- Characters act: walk cycles, sitting down, typing, head turns, blinks, gestures, reactions synced to the words.
- **One continuous world.** The camera travels between places (pan, follow a walking character, push in); scene changes are camera moves
  or zoom-throughs (push into a brick face until its colour becomes the next room's wall). Never a card that grows, a slab that clips open,
  a crossfade cut or a box that "increases its size from nowhere".
- Every arrival animates (drop + settle, draw-on, spring pop out of a source). Nothing appears without motion.
- Ambient life on holds: breathing, blinks, steam, swaying plants, slow camera drift.
- Shared kit rules still hold: camera keys 1.8-2.4 s `CAMV` (or `camSpring`); `landS` arrivals; no squash; followers computed in one
  `driver()`; no still > 0.8 s; near-still <= 15% (motion_check); no motion blur.
- Any shape that changes into another (bubble -> sign, brick -> card, a UI element) follows diksha-clip `references/motion.md`: one shape
  on springs (`boxTrack`), content swapped mid-flight with a short blur, shared elements travelling, never a cross-fade.
- The editor may ask for the online UI style on a studio clip (Munnawar Clip 2): then build it exactly like motion.md + the online style,
  keeping this skill's half layout, captions and logo.

## Metaphors
- Liked in v1: the infectious-smile wave across a crowd (idea liked, execution broken); a fan thinking about what they love, the list building in.
- Requested: Lego bricks for "layers / foundation" - two bricks at the bottom as the foundation, one brick on top resting on both; drawn
  properly with studs, moving (drops, snaps, settles), never static.

## First-output checklist
1. Layout = half (animation top, camera bottom); Diksha shown 3-4 times; sync check done.
2. No UI elements anywhere; people are illustrated characters; bubbles are clouds rising from heads.
3. Every scene change is a camera move or zoom-through inside one world; no growing boxes, no slideshow cuts.
4. Every element enters with motion; characters move on the words; nothing overlaps a label (check drift/peak positions).
5. Real logo only on its beat.
6. Captions on the seam in the editor's style; channel logo black over animation, normal over camera-only frames.
7. Render passes motion_check / qa_cuts; one sheet looked at; lip sync measured on the render (bottom half vs conformed cell).

## Rejected in Munnawar Clip 1 v1 (do not repeat)
Online UI-card look; split inset layout; iceberg metaphor; avatar discs as people; rectangular chat bubble; bubble trail line; slab -> card
clip-path morphs (read as a slideshow / a box growing from nowhere); room content appearing with no animation; label pill overlapping drifting
nodes; Clay logo shown on the word "Clay" instead of its beat; Diksha only once; audio out of sync (25 fps cameras re-stamped as 24 fps; fixed in conform).
