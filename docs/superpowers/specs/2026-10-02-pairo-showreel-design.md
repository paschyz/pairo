# Pairo showreel — 20 s motion-graphics film with an original piano score

## Context

**Asked for:** a dynamic 16:9, 20-second motion-graphics showreel presenting Pairo; S-tier sound design (no generic synth pads); an original piano score with every cut synced to it; exported as 1080p MP4. Creative direction is delegated ("show your real creative limits").

**Found (read-only exploration):**
- Brand as shipped in `dashboard/src/views/HomeView.vue`: near-black `#08090d`, orange `#ff7a32` (gradient `#e05500→#ffcc66`), Space Grotesk, robot mascot `dashboard/src/assets/pairo.png`. CLAUDE.md's violet `#7c6ef0` is stale; the film follows the landing page.
- Story, in the product's own words (`README.md`, `index.html`, `webhook.py`, `github/client.py`): "AI code reviews that actually help" · "Dismiss a finding once — it never comes back." · `@pairo ignore we don't use Redis in this project` → "👍 Ignored on this PR. Rule proposed in `.pairo.md`" · axes 🔧 crafts / 🌱 eco / ♿ a11y · "It learns. It's transparent. It's fast. It's yours."
- Machine: Intel i7 (6 cores), macOS 15, Node 24, uv + Python 3.12. No ffmpeg (Remotion bundles one). **Only 11 GB free disk** — this plan needs about 1.5 GB.
- Skill search: official `remotion-dev/skills@remotion-best-practices` (561K installs, v4.0.532). Not installed yet.

**Outcome:** `video/out/pairo-showreel-1080p.mp4` (1920×1080, 60 fps, 20.000 s, H.264 + AAC) plus its reproducible source in `video/`. `dashboard/` and `backend/` are not touched.

## Concept — "The note that learns"

One idea drives music, picture and edit:

1. A reviewer that repeats itself is **one piano note, repeated**.
2. Pairo learns, so that note **becomes a melody**.
3. The melody **spells the name**: P‑A‑I‑R‑O → **B‑A‑B‑D‑A** (musical cryptogram: alphabet wrapped onto the notes A–G).
4. Five letters → **5/4 time**, a 5-note motif, 5 sections of 2 bars. At ♩=150 a bar is exactly 2.000 s = 120 frames, a beat 24 frames, an eighth 12: every note lands on a whole frame.

Three things change when Pairo arrives, so the story reads even on mute or with eyes shut: **colour** (grey world → first orange pixel is `@pairo`), **motion** (stepped 12 fps "robot" movement → fluid 60 fps), **sound space** (mono, dry, boxed-in → wide stereo, hall).

## Score and edit map

Bass accents follow a 3+3+2+2 pattern inside each bar (frames +0, +36, +72, +96): long, long, short, short. That pattern is the cutting rhythm.

| Section | Bars · time | Music | Picture | Cut frames |
|---|---|---|---|---|
| **I. Noise** | 1–2 · 0–4 s | One B, repeated, mechanical, no pedal. Bar 2 doubles speed and adds a clashing C, crescendo, then a hard stop into silence. | A grey, faceless reviewer posts the same "cache it in Redis" comment on PR after PR; duplicates pile into a wall. "Most AI reviewers repeat themselves." Freeze on the silence. | 24 48 72 96 · 120→204 every 12 · 216 |
| **II. Tell it once** | 3–4 · 4–8 s | Pedal down, soft Em9. The motif appears for the first time, high and tentative: B A B D → A. Typing is piano key-release clicks. A7sus4 and a reversed-piano swell lead into the drop. | `@pairo ignore we don't use Redis in this project` is typed in time with the clicks. Pairo answers. The reply's letters rearrange into the rule "This project does not use Redis." and snap into `.pairo.md`. | 240 · 360 · 432 |
| **III. It never comes back** | 5–6 · 8–12 s | D major groove: left hand in octaves on the accents (D → G), right hand plays the motif in eighths. | Next PR: the Redis comment starts to form and is erased on the accent. Only real findings land: 🔧 crafts, 🌱 eco, ♿ a11y. The mascot's eyes read the diff; its antenna pulses on each note. | 480 · 552 · 600 · 672 |
| **IV. Blitz** | 7–8 · 12–16 s | Loudest: Bm7 → A, octaves, a sixteenth-note run upward. | Eight hard cuts, full-bleed kinetic type: "It learns." / "It's transparent." (dashboard counters) / "It's fast." (cache hit, 0 tokens) / "It's yours." (open-source) · crafts / eco / a11y / implode to a point. | 720 756 792 816 · 840 876 912 936 |
| **V. Pairo** | 9–10 · 16–20 s | The motif as five broad chords (G – D/F♯ – Em7 – C add9 – A7sus4) resolving to D with a low D; one high "ping"; ring-out. | Giant P · A · I · R · O, one letter per chord, each captioned with its note. Final chord: mascot + wordmark + "AI code reviews that actually help" + `github.com/paschyz/pairo`. The mascot blinks on the ping. | 960 984 1008 1032 1056 · 1080 |

34 cuts, each on a note onset **by construction**: the score emits `timeline.json`; scenes read cut frames from it and never hard-code a frame number.

## Sound design — everything you hear is a piano

- **Instrument:** Salamander Grand Piano V3 (Yamaha C5, 48 kHz/24-bit, 16 velocity layers, CC BY 3.0). Only the pitches and layers the score uses are downloaded (about 150 MB).
- **Own sampler** (Python): onset-aligned samples, velocity layers, ±1-semitone repitch, damper release, sustain pedal, key-release and pedal noises, humanised timing and velocity (notes on cut points stay sample-tight), rolled chords.
- **No oscillators, no pads.** Effects are transformed piano: reversed tails (swells, whooshes), low strings an octave down (sub impacts), key-release clicks (typing, a sixteenth-note "shaker"), pedal thump (the breath before section II), a pitch-glided reversed high note (the "erase"), string-resonance samples (shimmer).
- **Master:** convolution reverb, glue compression, true-peak limiter; −14 LUFS integrated, peaks ≤ −1 dBTP.

## Visual system

- Tokens lifted from `.landing` in `HomeView.vue`; the end card reuses the landing's 64 px grid and orange radial glow.
- Type: Space Grotesk 700 for display, Space Mono for code (its monospace parent), via `@remotion/google-fonts`.
- **Mascot redrawn as a rigged SVG** from `pairo.png` so it can act: pupils track, blink, antenna spring, squash and stretch. Checked by overlaying it on the PNG.
- UI cards in the landing's float-card style, using the real comment format from `render_review_comment` and the real reply strings from `webhook.py`.
- Motion: springs and béziers, frame-driven only. Camera rig (push, whip, shake on sub impacts), motion blur on whips, film grain and vignette against banding. A hairline 88-key strip along the bottom lights each played note, so the sync is visible.
- No large-area flashing above 3 Hz (WCAG 2.3.1): Pairo reviews a11y, so its film should pass.

## Build

**Stack:** Remotion 4.0.532 for picture (bundles its own Chrome Headless Shell and ffmpeg). One Python script run with `uv` for audio and QA (inline deps: numpy, scipy, soundfile, pyloudnorm, imageio-ffmpeg). No brew installs.

**New files, all under `video/`:**

```
score/score.py       compose · sampler · sound design · master · emits timeline · `verify` subcommand
score/samples/       Salamander subset (gitignored)
public/score.wav     generated
src/timeline.json    generated: bpm, fps, cuts, accents, notes, typing, sfx
src/index.ts · Root.tsx · Showreel.tsx      root, compositions, <Audio> + <Series> built from timeline.cuts
src/kit.tsx          tokens, bar/beat→frame helpers, note-pulse hook, KineticText, Camera, Grain, KeyStrip
src/Mascot.tsx       rigged SVG mascot
src/scenes/          Noise · TellItOnce · NeverBack · Blitz · Lockup
README.md            three commands + credits
out/pairo-showreel-1080p.mp4
```

**Steps:**
0. Save this design to `docs/superpowers/specs/2026-10-02-pairo-showreel-design.md` (repo convention, uncommitted). Install the skill: `npx skills add remotion-dev/skills@remotion-best-practices -g -y`, then follow it.
1. Scaffold: `npx create-video@latest --yes --blank --no-tailwind video`, `npm i`, `npx remotion add @remotion/media @remotion/google-fonts @remotion/motion-blur`. Start `npx remotion studio` so you can watch it come together, with sound.
2. **Music first** (it is the master clock): write `score/score.py`; `uv run score/score.py` produces `public/score.wav` and `src/timeline.json`; inspect spectrogram and waveform images.
3. Kit and mascot (overlay check against the PNG).
4. Scenes I → V, each checked with stills at its cut frames (`npx remotion render … --frames=… --image-format=png`).
5. Render: `npx remotion render PairoShowreel out/pairo-showreel-1080p.mp4 --codec=h264 --crf=16 --pixel-format=yuv420p --color-space=bt709 --audio-bitrate=320k --jpeg-quality=95`.
6. Verify (below), write the README, report results.

## Verification

1. `uv run score/score.py` asserts: exactly 20.000 s; every cue on a whole frame; −14 ± 0.5 LUFS; true peak ≤ −1 dBTP; no clipping or DC; section I is mono and the hard stop is silent.
2. Stills at every cut frame ±1, reviewed for layout, legibility, safe area and the flash limit.
3. `npx remotion ffprobe` on the MP4: 1920×1080, 60 fps, 1200 frames, h264/yuv420p, AAC 48 kHz stereo.
4. `uv run score/score.py verify out/pairo-showreel-1080p.mp4` on the **final file**: at each of the 34 cut frames the picture must jump on exactly that frame, with an audio event within ±1 frame (16.7 ms); A/V offset against the source WAV under 10 ms. Prints a pass/fail table.
5. Contact sheet of all cuts for a last look. Then you watch and listen.

## Decisions I made (tell me to change any)

- Lives in `video/` at the repo root with its own `package.json`. **Nothing is committed** unless you ask.
- English copy, lifted from the landing and README. Two lines are mine: "Most AI reviewers repeat themselves." (README paraphrase) and "Tell it once."
- 60 fps. One constant switches it to 30; the timing grid still lands on whole frames.
- Mascot redrawn as SVG so it can move. Fallback: the PNG as a rounded tile, as on the landing.
- Orange landing palette, not CLAUDE.md's violet.
- Remotion skill installed globally (`-g`), like your other skills.

## Limits and risks

- **I cannot hear audio or watch playback.** Sound is validated by measurement and spectrograms, picture by stills. Expect one taste pass after your first watch (mix, feel, copy).
- **Disk:** 11 GB free; this uses about 1.5 GB (node_modules + Chrome 0.7, samples 0.15, Python wheels 0.3, render temp 0.4).
- **Render** on this Intel Mac: roughly 5–15 min. Motion blur is a polish layer; if it is slow or unstable here it falls back to CSS/SVG blur, with sync and story unaffected.
- **Licences:** Remotion is free for individuals and teams of up to 3 (company licence beyond that). Salamander is CC BY 3.0, so "Alexander Holm" is credited in the README and should be credited wherever the video is posted.

## As built (2026-10-02)

Where the result differs from the design above:

- **Mascot:** not redrawn. The body is the original logo artwork, cut out to a transparent PNG by `video/score/mascot.py`; only the eyes are redrawn on top (so they can look and blink), and the antenna is the same image clipped at the stem.
- **Motion blur:** `@remotion/motion-blur` is not used and was removed. The zoom into `.pairo.md` uses a CSS blur and the thrown comment a directional SVG blur.
- **Encode:** CRF 18, not 16. With film grain, CRF 16 came out at 83 MB; the delivered file is 28 MB.
- **Samples:** 259 MB downloaded, not about 150 MB.
- **30 fps:** cuts would still land on whole frames, but the in-shot animation lengths are written in frames, so a 30 fps version needs retiming, not just the one constant.
- **Section III caption:** the title is "It never comes back." only; no summary line under the findings.

Measured on the delivered file: 1920×1080, 60 fps, 1200 frames, H.264 High + AAC 48 kHz stereo; −14.0 LUFS, −1.6 dBTP; all 34 cuts land on the score with a note onset 0–12 ms after each; audio/video offset 0.0 ms; at most 1.5 luminance flashes per second.
