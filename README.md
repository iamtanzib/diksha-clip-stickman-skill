# diksha-clip-stickman — Claude Code skill (backup)

The Claude Code skill that builds vertical clips from **studio** episodes of *The Quest with Diksha*. Studio means Diksha and the guest are in the same room, with no screen share.

**The look:** hand-drawn stickman animation on the top half: stick figures, cloud speech bubbles and Lego-brick metaphors in one continuous world the camera zooms through. The speaker camera is on the bottom half, with Diksha reaction cuts, burned-in captions and the channel logo.

> Online episodes (remote guest, screen share) use the sister skill
> [diksha-clip](https://github.com/iamtanzib/diksha-clip-skill) instead. Never mix the two styles.

This repo **is** the skill folder, so cloning it puts the exact skill back in place.

---

## Reinstall (new PC, or the skill got lost)

Run in PowerShell. **Install both skills**, because this one reads the shared kit notes in `diksha-clip/references/kit-api.md`:

```powershell
gh repo clone iamtanzib/diksha-clip-stickman-skill "$HOME\.claude\skills\diksha-clip-stickman"
gh repo clone iamtanzib/diksha-clip-skill "$HOME\.claude\skills\diksha-clip"
```

Restart Claude Code. The skill shows up as `diksha-clip-stickman`.

If a clone fails because the folder already exists, rename the old folder first, then run the command again:
`Rename-Item "$HOME\.claude\skills\diksha-clip-stickman" diksha-clip-stickman.old`

### First time on a fresh PC

| Need | Install |
|---|---|
| Git + GitHub CLI, signed in | `winget install Git.Git GitHub.cli`, then `gh auth login --web` |
| Claude Code | https://claude.com/claude-code |
| Node.js 20+ (for `npx hyperframes`) | `winget install OpenJS.NodeJS.LTS` |
| Python 3.12 + numpy + scipy | `winget install Python.Python.3.12`, then `pip install numpy scipy` |
| FFmpeg on PATH | `winget install Gyan.FFmpeg` |

---

## Back up after you change the skill

Right-click `backup.ps1` → **Run with PowerShell**, or run:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\diksha-clip-stickman\backup.ps1"
```

It saves every change, including new `log/used.md` entries, with a dated message and pushes it to GitHub. If nothing changed, it does nothing.

**Pull the latest from GitHub** (for example, after editing on another PC):

```powershell
git -C "$HOME\.claude\skills\diksha-clip-stickman" pull
```

**Roll back:** every backup is a commit. See the history with `git -C "$HOME\.claude\skills\diksha-clip-stickman" log --oneline`.

---

## What's inside

```
SKILL.md                entry point Claude reads: workflow, inputs, gotchas, cost rules
references/
  style.md              look, layout, captions, logo, motion rules, rejected list,
                        first-output checklist
  stickman-api.md       the SM library: bricks, stick-figure rig, clouds,
                        zoom-through worlds, captions, logo + recipes
log/used.md             concepts used per clip, newest first (anti-repeat memory)
tools/usage.py          token/cost report for a finished session
template/               copied into every new clip project
  project.json          inputs, cameras, crops
  tools/                align_audio, framing, conform, build, captions, qa, qa_cuts,
                        sync_check, motion_check, sheet, sfx, patch, kit.js,
                        index.src.html
  assets/fonts/         DM Sans + Roboto (SIL Open Font License)
  assets/logo/          The Quest logo + black wordmark
  assets/sfx_cues.json
  CLAUDE.md, AGENTS.md  per-project instructions
```

**How it's used:** start a fresh Claude Code session in the clip folder and say "stickman clip" or "studio clip". The skill sets up a HyperFrames project from `template/`. It then aligns the audio, conforms the 25 fps studio cameras to 24 fps, picks reactions, storyboards, builds, adds captions and SFX, runs QA and renders in 4K. `SKILL.md` has the full workflow.

---

## Notes

- **Private repo.** It holds the client's logo and the editor's working notes. Keep it private.
- Line endings are stored as-is (`.gitattributes`), so a clone is byte-for-byte the same as the original.
- `SKILL.md` points to a reference clip and the logo source by absolute paths on the editing PC (`D:\…`, `E:\…`). Those are optional. The processed logo is already in `template/assets/logo/`.
