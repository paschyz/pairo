# Pairo showreel

A 20-second, 1080p60 motion-graphics film for Pairo with an original piano score.
Built with [Remotion](https://www.remotion.dev) (picture) and one Python script (music and sound).

```sh
npm i
npm run score     # compose, perform and master the music -> public/score.wav + src/timeline.json
npm run dev       # preview in Remotion Studio
npm run render    # -> out/pairo-showreel-1080p.mp4
npm run verify    # check the rendered film against the score
```

`npm run score` and `npm run verify` need [uv](https://docs.astral.sh/uv/); it fetches Python and the
few packages the script declares. The first `score` run downloads about 230 MB of piano samples into
`score/samples/`. `public/score.wav` and `src/timeline.json` are its output, so the film renders
without Python once they exist.

## How it is put together

**The score is the master clock.** `score/score.py` writes the audio and, next to it,
`src/timeline.json`: every cut, accent, keystroke and note, as frame numbers. The scenes read their
timings from that file (`src/kit.tsx`) and never hard-code a frame, so picture cannot drift from sound.
To move a cut, change the score and run `npm run score`.

**The name is the tune.** Wrap the alphabet onto the notes A–G and P‑A‑I‑R‑O spells B‑A‑B‑D‑A.
Five letters, so the piece is in 5/4; at 150 bpm an eighth note is exactly 12 frames at 60 fps.
The left hand plays a 3+3+2+2 pattern, and the film cuts on it.

| Section | Bars | What happens |
| --- | --- | --- |
| I. Noise | 1–2 | One note, repeated: a reviewer that says the same thing on every PR. Grey, 12 fps, mono. |
| II. Tell it once | 3–4 | `@pairo ignore …` is typed on the score's sixteenths; the words become a `.pairo.md` rule. |
| III. It never comes back | 5–6 | The old comment tries to return and is wiped. Three real findings land. |
| IV. Blitz | 7–8 | Eight cuts on the bass: the README's four claims, then the three review axes. |
| V. Pairo | 9–10 | One letter per chord (the top voice is the motif), then the lockup. |

**Every sound is a recording.** `INSTRUMENT` in `score.py` picks who plays the notes: `"mallets"`
(marimba with a glockenspiel edge on the right hand; the current film) or `"piano"` (a sampled grand).
Swells are the instrument reversed, impacts are its lowest notes an octave down, typing is piano
key-release noise. There are no oscillators in `score.py`.

**`npm run verify`** decodes the finished MP4 and checks that the picture jumps on each of the 34 cut
frames, that a note lands within a frame and a half of each one, and that the audio track lines up with
the score it was rendered from.

`score/mascot.py` cuts the mascot out of `dashboard/src/assets/pairo.png` (-> `public/mascot.png`).
`src/Mascot.tsx` rigs it: the body is the original artwork, only the eyes are redrawn so they can move.

## Credits and licences

- Marimba and glockenspiel: [VSCO-2 Community Edition](https://github.com/sgossner/VSCO-2-CE) by
  Versilian Studios, CC0.
- Piano, including the key and pedal noises used in every version:
  [Salamander Grand Piano V3](https://github.com/sfzinstruments/SalamanderGrandPiano) by
  Alexander Holm, CC BY 3.0. **Credit him wherever the film is published.**
- Remotion is free for individuals and teams of up to three; larger companies need a
  [company licence](https://www.remotion.pro/license).
- Type: Space Grotesk and Space Mono (SIL Open Font License), loaded from Google Fonts at render time.
