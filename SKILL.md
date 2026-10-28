---
name: diksha-clip-stickman
description: 'Build a finished vertical clip from a STUDIO episode of "The Quest with Diksha" (Diksha and the guest in person, no screen share) in the stickman style - hand-drawn illustrated animation on the top half (stick-figure characters, cloud speech bubbles, Lego-brick metaphors, one continuous world the camera zooms through), speaker camera on the bottom half, Diksha reaction cuts, burned-in captions and the channel logo. Use whenever the editor (Tahjib) brings a Diksha studio-episode clip, says "studio clip", "stickman clip" or "diksha clip stickman". Online episodes (remote guest, screen share) use diksha-clip instead; never mix the two styles.'
---

# Diksha clip - stickman (studio episodes)

Separate from `diksha-clip` (online episodes, UI-card look). Same pipeline and QA tools, a different look, layout and animation language.
Proven on Munnawar Clip 1: v2 approved with no notes ("better than what I wanted"), then only caption/logo polish.
One clip per session. Target: v1 approved after at most one round of notes.

Read, in this order and only when the step needs it (each once):
- `references/style.md` - the look, layout, captions, logo, motion rules, rejected list and the **first-output checklist**. Always before storyboarding.
- `log/used.md` - the newest ~4 clip blocks. Before storyboarding; append after delivery.
- `references/stickman-api.md` - the `SM` library (bricks, stick-figure rig, clouds, zoom-through worlds, captions, logo) and recipes.
  Before writing scene code. Shared kit helpers (W, T, camPath, K, driver, landS, ...): `~/.claude/skills/diksha-clip/references/kit-api.md`.
  Do not read `tools/kit.js` itself.
- Reference implementation (open ONLY the section you need, `grep -n` then `sed -n a,b p` <= 80 lines):
  `D:\Diksha\Podcast 2\Clips\Clip 1\videos\clip1\tools\index.src.html` - anchors: `world 1 people`, `word of mouth`, `world 2`, `the finale`,
  `camera: one world`, `----- world 1: room`, `----- cafe`. Its helpers are inline; new clips use `SM` instead.
- Do NOT read the online `style.md`/`concepts.md`, and do not load the generic HyperFrames skills unless a lint/check error is unclear.

## Inputs (ask once if anything is missing)
In the clip folder's `Inputs/`: one camera file per person (host = Diksha, guest), the **final edited audio** and its word-level transcript
JSON (`segments[].words[]` with start/end). Camera audio is only for alignment; the picture always plays against the final audio.
Studio cameras are **25 fps**: conform resamples to 24 fps by timestamp and asserts every output matches the audio length.
Ask only: who says which lines if unclear, and must-have visuals. The channel logo source is `E:\Diksha Podcast\Episode 3 Tushar\Raw\2.png`
(already processed into `template/assets/logo/`).

## Workflow
1. **Scaffold** (one Bash call, from the clip folder):
   ```bash
   npx hyperframes init "videos/clipN" --non-interactive --example=blank --skill=general-video && cp -r ~/.claude/skills/diksha-clip-stickman/template/* "videos/clipN/"
   ```
   Fill `project.json`: `inputs.audio`, `inputs.transcript`, `cameras.host.file`, `cameras.guest.file` (paths inside `../../Inputs`).
2. **Align + conform** (chain with `&&`, read summary lines only):
   `python -I tools/align_audio.py && python -I tools/framing.py grid` - every chunk ncc >= 0.9; view the ONE grid image (host tile left).
   `python -I tools/framing.py suggest --cam host --hair <f> --chin <f> --face <f>` (FRACTIONS of the 4K frame: hair top y, chin y, face
   centre x), same for guest, merge the printed JSON into project.json, then `python -I tools/conform.py` (background; it also writes the
   `*_half.mp4` copies the 50/50 cells need). For a new guest/setup: `python -I tools/framing.py check` and send that image.
3. **Reactions**: `python -I tools/sheet.py assets/host_cell.mp4 <10-12 times> --w 220` once; pick 3-4 Diksha moments (smiles, nods, her lines).
4. **Storyboard (text only, get approval)**: ONE table `# · time · line · bottom half · animation (word -> action)`. Name the world (places,
   how the camera travels: pans, follows a walking character, zooms through a face), every character and every morph chain. List open
   questions (who says what, logos). Check it against the style.md checklist. Get approval; the build follows it without re-deliberating.
5. **Build**: `tools/index.src.html` (replace the DEMO block; keep everything marked keep) + `tools/layout.json` (rows: stack opener, `half`
   with guest, Diksha cuts) + `assets/sfx_cues.json`, one Write each. Use `SM` (stickman-api.md): one `camPath` with 1.8-2.4 s keys and
   zoom-throughs, everything else set from ONE `driver()`. Anchor every beat with `W()`.
   Captions: `python -I tools/captions.py` (put the clip's proper nouns in `KEEP_CASE` first), paste `assets/captions.json` into `CAPS`.
   SFX: `python -I tools/sfx.py`.
6. **QA**: `python -I tools/qa.py` until no FAIL (caption contrast is auto-accepted), then in the background
   `python -I tools/qa.py --render --at <8-12 times> --full` and look at `qa/sheet.jpg` once (whole frames: captions + logo visible), then
   `python -I tools/sync_check.py renders/qa.mp4 guest <3 times where the guest is in the bottom half>` - must PASS.
   Detail only for a flagged spot: `python -I tools/sheet.py renders/qa.mp4 <t> --crop x:y:w:h --w 540`.
7. **Preview**: send the draft MP4 (SendUserFile) with a short list of what changed per note. Ask for all notes in one message.
8. **Revise** with one batched patch per round (python replace script with asserted anchors, or `tools/patch.py`); re-render, re-sheet only
   the changed moments.
9. **Final** (background, ~4 min; never motion blur, never `-shortest`):
   ```bash
   PIN=$(grep -o 'hyperframes@[0-9.]*' package.json | head -1); npx --yes $PIN render -q delivery --resolution portrait-4k --fps 24 -o renders/ClipN_4K.mp4 && ffmpeg -v error -y -i renders/ClipN_4K.mp4 -i assets/voice.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k renders/ClipN_4K_noSFX.mp4 && cp assets/sfx.wav renders/ClipN_SFX_track.wav
   ```
   Deliverables: `ClipN_4K.mp4` (voice + SFX), `ClipN_4K_noSFX.mp4`, `ClipN_SFX_track.wav`. Verify 2160x3840, 24 fps, frame count, and run
   sync_check on the 4K file.
10. **Log**: append the clip's concepts to `log/used.md` (newest first) and `python -I tools/usage.py` (in this skill) as its last line.
    Fold any new editor rule into `references/style.md`, any new reusable helper into `SM` + stickman-api.md.

## Gotchas (each one cost a round or a re-render)
- **25 fps cameras**: before the conform fix, frames were re-stamped as 24 fps -> the picture ran 4% slow, 1.8 s out of lip sync by the end.
  Conform now asserts lengths; `sync_check.py` measures the render. Run it every clip.
- **Two `<video>`s on one file** can freeze one of them (`duplicate_media_discovery_risk`): stack cells use `*_cell.mp4`, half cells `*_half.mp4`.
- **Assets referenced only from script are not shipped by the renderer** (an SVG `<image>` built in JS rendered empty): keep a static
  `<img>` (opacity 0, 1 px) of every such file in the markup. Logos and fonts are already static.
- `hyperframes check` flags the white captions for contrast (it ignores text-shadow). That is the editor's style; qa.py accepts it when it is
  the only error. A blurred text copy behind them does NOT fix it (it adds an overlap error).
- qa.py stops at the first failing gate: if a render is still needed, run its steps directly (render, motion_check, qa_cuts, sheet).
- No PIL on this machine: image work = ffmpeg + numpy over raw pipes (`-f rawvideo -pix_fmt rgba`).
- A brick-face border inside a world SVG must be thin (60 inner px) or it shows as a black bar when the camera is inside near the edge.
- Wide camera views inside a world must stay inside the face (`|X| <= w*Z/2 - 540/k`), or the edge and the outer world show.
- Clouds near the frame edge get clipped once their bumps are counted (add ~35 px to rx/ry when checking the frame).

## Cost discipline
Fewer calls (chain with `&&`, qa.py, one batched patch per round), small context (short outputs, section reads, one sheet per pass),
decide once in the storyboard. Characters, bricks and clouds come from `SM` - never re-derive the rig. Measured on Clip 1 (incl. building
this skill): ~5.6M weighted tokens; a v2-style rebuild with the library should be well under half of that.
