#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "soundfile", "pyloudnorm", "imageio-ffmpeg"]
# ///
"""The Pairo showreel score: composed, performed, designed and mastered in one pass.

    uv run score/score.py                       -> public/score.wav, src/timeline.json, score/qa/
    uv run score/score.py verify out/film.mp4   -> checks the rendered film against the score

Every sound is a recording, played or transformed; there are no oscillators in this file.
INSTRUMENT picks who plays the notes: "mallets" (marimba with a glockenspiel edge, from the
CC0 VSCO-2 Community Edition) or "piano" (Salamander Grand Piano V3, Alexander Holm, CC BY 3.0).
The typing clicks and the pedal breath are the piano's key and pedal noises either way.

The name is the tune: wrap the alphabet onto A-G and P-A-I-R-O spells B-A-B-D-A.
Five letters, so 5/4, and at 150 bpm every eighth note is exactly 12 frames.
The film reads its cuts from the timeline written here, so picture cannot drift from sound.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "score" / "samples"
QA = ROOT / "score" / "qa"
WAV = ROOT / "public" / "score.wav"
TIMELINE = ROOT / "src" / "timeline.json"
SOURCE = "https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/master/Samples/"
VSCO = "https://raw.githubusercontent.com/sgossner/VSCO-2-CE/master/Percussion/"

INSTRUMENT = "mallets"  # or "piano"
# Sounding pitch of each mallet recording, measured: the marimba files are named an octave low
# and the glockenspiel is tuned a touch sharp.
MARIMBA = {41: "F1", 48: "C2", 55: "G2", 59: "B2", 65: "F3", 72: "C4", 79: "G4", 83: "B4", 89: "F5", 96: "C6"}
GLOCK = {79.08: "G4", 84.12: "C5", 91.12: "G5", 96.15: "C6", 103.16: "G6", 108.24: "C7"}

SR = 48_000
BPM, BEATS, BARS, FPS = 150, 5, 10, 60
BEAT = 60 / BPM  # 0.4 s = 24 frames
BAR = BEAT * BEATS  # 2.0 s = 120 frames
DUR = BAR * BARS
N = round(DUR * SR)
CLAVE = (0, 3, 6, 8)  # 3+3+2+2 in eighths: where the left hand lands, and where the film cuts
MOTIF = ("B", "A", "B", "D", "A")  # P A I R O
TARGET_LUFS, CEILING_DB = -14.0, -1.6
VELTRACK = 0.35  # extra velocity->gain on top of the natural level of each velocity layer
GAIN_DB = {"piano": -3.0, "nag": 1.5, "sub": 0.0}  # bus trims; "piano" is the main instrument bus, whoever plays it
if INSTRUMENT == "mallets":  # every bar is recorded at one level, so the buses sit differently than the piano's
    GAIN_DB.update(nag=-5.0, sub=9.0)
RNG = np.random.default_rng(5)


def at(bar: int, beat: float = 1.0) -> float:
    """Seconds at a 1-based bar and beat."""
    return (bar - 1) * BAR + (beat - 1) * BEAT


def frame(t: float) -> int:
    f = t * FPS
    assert abs(f - round(f)) < 1e-6, f"cue at {t:.4f}s is off the frame grid"
    return round(f)


def midi(name: str) -> int:
    """'F#4' -> 66."""
    step = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[name[0]] + (name[1] == "#")
    return 12 * (int(name[-1]) + 1) + step


def motif(i: int, octave: int) -> int:
    name = MOTIF[i % 5]
    return midi(f"{name}{octave + (name == 'D')}")


def db(x: float) -> float:
    return 10 ** (x / 20)


# ---------------------------------------------------------------- the instrument

HIVEL = (26, 34, 36, 43, 46, 50, 56, 64, 72, 80, 88, 96, 104, 112, 120, 127)  # 16 velocity layers
_samples: dict[tuple[str, str, float], np.ndarray] = {}
_voices: dict[tuple, np.ndarray] = {}


def fetch(name: str) -> Path:
    folder = "Marimba/" if name.startswith("Marimba") else "Glock/" if name.startswith("glock") else None
    path = SAMPLES / f"{name}.{'wav' if folder else 'flac'}"
    if not path.exists() or path.stat().st_size == 0:
        SAMPLES.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve((VSCO + folder if folder else SOURCE) + urllib.parse.quote(path.name), path)
    return path


def load(name: str, align: str = "onset", pre: float = 0.0005) -> np.ndarray:
    """A sample trimmed so its hammer strike ('onset') or loudest click ('peak') sits `pre` s in."""
    key = (name, align, pre)
    if key not in _samples:
        x, sr = sf.read(fetch(name), dtype="float32", always_2d=True)
        if sr != SR:
            x = signal.resample_poly(x, SR, sr, axis=0).astype(np.float32)
        env = np.abs(x).max(axis=1)
        mark = int(np.argmax(env > 0.02 * env.max())) if align == "onset" else int(np.argmax(env))
        x = x[max(0, mark - round(pre * SR)) :].copy()
        x[:48] *= np.linspace(0, 1, 48, dtype=np.float32)[:, None]
        _samples[key] = x
    return _samples[key]


def sample_name(p: int, vel: int) -> tuple[str, int]:
    """The piano is sampled every minor third: nearest recording and semitones to shift."""
    centre = 21 + 3 * round((p - 21) / 3)
    layer = next(i + 1 for i, hi in enumerate(HIVEL) if vel <= hi)
    letter = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")[centre % 12]
    return f"{letter}{centre // 12 - 1}v{layer}", p - centre


def struck(bank: dict[float, str], name: str, p: int, vel: int) -> tuple[np.ndarray, float]:
    """A mallet instrument: one recording per few notes and one dynamic, so repitch the nearest."""
    near = min(bank, key=lambda k: abs(k - p))
    if (name, near, p) not in _voices:
        x = load(name.format(bank[near]))
        stretch = Fraction(2 ** ((near - p) / 12)).limit_denominator(300)
        if stretch != 1:
            x = signal.resample_poly(x, stretch.numerator, stretch.denominator, axis=0)
        _voices[name, near, p] = (0.5 * x / np.abs(x).max()).astype(np.float32)
    return _voices[name, near, p], (vel / 127) ** 1.7


def bell(p: int, vel: int) -> tuple[np.ndarray, float]:
    return struck(GLOCK, "glock_medium_{}", p, vel)


def voice(p: int, vel: int) -> tuple[np.ndarray, float]:
    if INSTRUMENT == "mallets":  # the marimba stops at C2; anything lower goes up an octave and the sub carries the weight
        return struck(MARIMBA, "Marimba_hit_Outrigger_{}_loud_01", p if p >= 36 else p + 12, vel)
    name, shift = sample_name(p, vel)
    if (name, shift) not in _voices:
        x = load(name)[: 14 * SR]
        if shift:  # 196/185 is a semitone to within a hundredth of a cent
            up, down = (185, 196) if shift > 0 else (196, 185)
            x = signal.resample_poly(x, up, down, axis=0).astype(np.float32)
        _voices[name, shift] = x
    return _voices[name, shift], (vel / 127) ** (2 * VELTRACK)


@dataclass
class Note:
    t: float
    p: int
    vel: int
    dur: float  # seconds the key is held
    bus: str
    hand: str
    tau: float | None  # damper time constant override


notes: list[Note] = []
pedal: list[tuple[float, float]] = []  # sustain pedal (down, up)
cues: dict[str, list] = {"cuts": [], "accents": [], "typing": [], "sfx": []}
FXD = np.zeros((N + 2 * SR, 2))  # effects that stay dry: clicks, sub
FXW = np.zeros((N + 2 * SR, 2))  # effects that go to the hall: swells, whips, echoes


def play(t, pitches, vel, dur, *, bus="piano", hand="R", roll=0.0, sigma=0.004, pin=False, tau=None):
    """Strike one note or a chord. `pin` nails the first note to the grid (cut points);
    sigma=0 is the robot: no timing or velocity humanisation at all."""
    ps = [pitches] if isinstance(pitches, (str, int)) else list(pitches)
    vs = list(vel) if isinstance(vel, (list, tuple)) else [vel] * len(ps)
    lead = 0.0 if pin or not sigma else RNG.normal(0, sigma)
    for i, (p, v) in enumerate(zip(ps, vs, strict=True)):
        dt = lead + i * roll + (RNG.normal(0, sigma / 2) if sigma and i else 0.0)
        dv = int(RNG.integers(-3, 4)) if sigma else 0
        p = midi(p) if isinstance(p, str) else p
        notes.append(Note(max(0.0, t + dt), p, int(np.clip(v + dv, 1, 127)), dur, bus, hand, tau))


def cut(t: float) -> None:
    cues["cuts"].append(frame(t))


def accent(t: float) -> None:
    cues["accents"].append(frame(t))


def sfx(name: str, t: float) -> None:
    cues["sfx"].append({"id": name, "frame": frame(t)})


def damper_tau(p: int) -> float:
    return float(np.interp(p, [28, 48, 72, 89], [0.22, 0.14, 0.09, 0.06]))


def render(bus: str) -> np.ndarray:
    out = np.zeros((N + 2 * SR, 2))
    for n in (n for n in notes if n.bus == bus):
        x, gain = voice(n.p, n.vel)
        up = n.t + n.dur
        off = next((u for d, u in pedal if d <= up < u), up)
        hold = max(1, round((off - n.t) * SR))
        tau = n.tau or damper_tau(n.p)
        mallets = INSTRUMENT == "mallets"  # bars have no dampers: they ring unless the score chokes them
        rings = (mallets or n.p >= 90) and n.tau is None  # nor does the piano's top octave and a half
        i0 = round(n.t * SR)
        length = min(len(x) if rings else min(len(x), hold + round(8 * tau * SR)), len(out) - i0)
        seg = x[:length] * gain
        if not rings and length > hold:
            seg[hold:] *= np.exp(-np.arange(length - hold) / (tau * SR))[:, None]
        out[i0 : i0 + length] += seg
        if mallets and n.hand == "R" and bus == "piano":  # a glockenspiel edge on the right hand, an octave up if it must
            ring, level = bell(n.p if n.p >= 79 else n.p + 12, n.vel)
            ring = ring[: 2 * SR] * np.exp(-np.arange(min(len(ring), 2 * SR)) / (0.45 * SR))[:, None]
            put(out, ring, n.t, -13 + 20 * math.log10(level))
        elif not mallets and n.p < 90:  # the key coming back up
            put(out, load(f"rel{n.p - 20}", "peak", 0.03), up - 0.03, -38 + 20 * math.log10(n.vel / 127))
    # ponytail: no sympathetic string resonance; layer the harm* release samples if the piano sounds too dry
    return out[:N]


# ---------------------------------------------------------------- signal helpers


def put(buf: np.ndarray, x: np.ndarray, t: float, gain_db: float = 0.0, pan: float = 0.0) -> None:
    i0 = round(t * SR)
    if i0 < 0:
        x, i0 = x[-i0:], 0
    length = min(len(x), len(buf) - i0)
    if length <= 0:
        return
    angle = (pan + 1) * math.pi / 4
    buf[i0 : i0 + length] += x[:length] * db(gain_db) * math.sqrt(2) * np.array([math.cos(angle), math.sin(angle)])


def filt(x: np.ndarray, kind: str, fc: float, order: int = 2, causal: bool = False) -> np.ndarray:
    sos = signal.butter(order, fc, kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0) if causal else signal.sosfiltfilt(sos, x, axis=0)


def auto(*points: tuple[float, float]) -> np.ndarray:
    """Automation curve over the whole piece from (seconds, value) breakpoints."""
    xs, ys = zip(*points, strict=True)
    return np.interp(np.arange(N) / SR, xs, ys)[:, None]


def width(x: np.ndarray, w: float | np.ndarray) -> np.ndarray:
    mid, side = x.mean(axis=1, keepdims=True), (x[:, :1] - x[:, 1:]) / 2
    return np.hstack([mid + w * side, mid - w * side])


def make_ir(rt60: float, predelay: float, damp: float, seed: int) -> np.ndarray:
    """A room: decaying noise whose highs die first. Reverb is the one thing here not made of piano."""
    n = round(rt60 * 1.3 * SR)
    noise = np.random.default_rng(seed).standard_normal((n, 2))
    t = np.arange(n)[:, None] / SR
    low = filt(noise, "lowpass", 500)
    high = filt(noise, "highpass", 3500)
    mid = noise - low - high
    ir = low * np.exp(-6.9 * t / (rt60 * 1.1)) + mid * np.exp(-6.9 * t / rt60) + high * np.exp(-6.9 * t / (rt60 * damp))
    ir[:240] *= np.linspace(0, 1, 240)[:, None]
    ir = np.vstack([np.zeros((round(predelay * SR), 2)), ir])
    return ir / np.sqrt((ir**2).sum(axis=0).mean())


HALL = make_ir(2.6, 0.022, 0.45, seed=1)
ROOM = make_ir(0.45, 0.004, 0.6, seed=2)


def reverb(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    return signal.fftconvolve(x, ir, axes=0)[: len(x)]


def strike(chord: list[tuple[str, int]], seconds: float) -> np.ndarray:
    """A chord left to ring, as raw material for effects (kept out of the note list)."""
    out = np.zeros((round(seconds * SR), 2))
    for name, vel in chord:
        x, gain = voice(midi(name), vel)
        length = min(len(x), len(out))
        out[:length] += x[:length] * gain
    return out


def swell(chord: list[tuple[str, int]], seconds: float, end: float, gain_db: float, hp: float = 200.0, gap: float = 0.03) -> None:
    """Reversed piano: the chord's tail first, its attack last. It stops `gap` s short of `end`,
    so the downbeat lands in a pocket of air."""
    dry = strike(chord, seconds + 0.6)
    seg = (0.5 * dry + reverb(dry, HALL))[: round(seconds * SR)][::-1]
    seg = filt(seg, "highpass", hp) * (np.linspace(0, 1, len(seg)) ** 2.2)[:, None]
    seg[-720:] *= np.linspace(1, 0, 720)[:, None]
    put(FXW, seg, end - gap - seconds, gain_db)


def sub(root: str, t: float, gain_db: float) -> None:
    """Weight under a downbeat: the lowest strings an octave down, plus the hammer thump."""
    x, _ = voice(midi(root + "1"), 112)
    low = filt(signal.resample_poly(x[: 2 * SR], 2, 1, axis=0), "lowpass", 110, 4, causal=True)
    low *= np.exp(-np.arange(len(low)) / (0.55 * SR))[:, None]
    thump = filt(x[:SR], "lowpass", 260, 2, causal=True) * np.exp(-np.arange(SR) / (0.14 * SR))[:, None]
    for part, trim in ((low, 0.0), (thump, -3.0)):
        put(FXD, part.mean(axis=1, keepdims=True).repeat(2, axis=1), t, gain_db + trim + GAIN_DB["sub"])
    sfx("sub", t)  # the picture flinches on these


def click(key: int, t: float, gain_db: float, *, pan=0.0, hp=None, lp=None, seconds=0.09) -> None:
    """A key-release noise from the sample set, its click landing on t. gain_db is its peak level."""
    x = load(f"rel{key}", "peak", 0.004)[: round(seconds * SR)].copy()
    x *= np.hanning(2 * len(x))[len(x) :, None]
    for kind, fc in (("highpass", hp), ("lowpass", lp)):
        if fc:
            x = filt(x, kind, fc)
    put(FXD, x / np.abs(x).max(), t - 0.004, gain_db, pan)


def whip(end: float, gain_db: float) -> None:
    """A reversed high note read at rising speed: something being wiped away."""
    x, gain = voice(midi("D6"), 84)
    src = x[: round(0.5 * SR)][::-1] * gain
    speed = np.linspace(0.6, 2.2, round(len(src) / 1.4))
    pos = np.cumsum(speed)
    pos = pos[pos < len(src) - 1]
    i = pos.astype(int)
    seg = src[i] * (1 - (pos - i))[:, None] + src[i + 1] * (pos - i)[:, None]
    seg = filt(seg, "highpass", 500) * (np.linspace(0, 1, len(seg)) ** 1.5)[:, None]
    seg[-240:] *= np.linspace(1, 0, 240)[:, None]
    put(FXW, seg, end - len(seg) / SR, gain_db)


# ---------------------------------------------------------------- the piece

STOP = at(2, 5)  # where the nagging is cut dead


def section_noise() -> None:
    """I. A reviewer that repeats itself: one note, no pedal, no feeling. Bars 1-2."""
    for b in range(5):
        t = at(1, 1 + b)
        play(t, "B4", 62, 0.15, bus="nag", sigma=0, tau=0.05)
        click(52, t, -15, lp=1400)
        cut(t)
    for i in range(8):  # twice as often, and now it clashes with itself
        t = at(2, 1 + i / 2)
        v = 62 + 3 * i
        chord = ["B4", "C5"] + (["B3"] if i >= 2 else []) + (["C4"] if i >= 4 else [])
        play(t, chord, [v, v - 4, v - 12, v - 14][: len(chord)], min(0.17, STOP - t), bus="nag", sigma=0, tau=0.03)
        click(52 - i, t, -16 + 0.6 * i, lp=1400 + 300 * i)
        cut(t)
    play(at(2), ["B1", "C2"], 70, STOP - at(2), bus="nag", hand="L", sigma=0, tau=0.03)
    swell([("B1", 90), ("C2", 90), ("B2", 80), ("C3", 80)], 1.55, STOP, -7, hp=120, gap=0)
    for key in (28, 33, 40, 47):  # the lid comes down: every damper at once
        click(key, STOP, -18, lp=2600, seconds=0.11)
    cut(STOP)
    sfx("stop", STOP)


def section_tell() -> None:
    """II. Tell it once: pedal down, and the note learns to move. Bars 3-4."""
    b3, b4, b44 = at(3), at(4), at(4, 4)
    breath = filt(load("pedalD1")[: 2 * SR], "highpass", 90) * np.linspace(1, 0, 2 * SR)[:, None]
    put(FXD, breath, b3 - 0.10, -6)  # the pedal going down: a breath before the first chord
    pedal.extend([(b3 - 0.08, b4 - 0.02), (b4 + 0.03, b44 - 0.02), (b44 + 0.03, at(5) - 0.03)])
    play(b3, ["E2", "B2", "G3", "D4", "F#4"], [56, 52, 56, 58, 64], 1.2, hand="L", roll=0.034, pin=True)
    cut(b3)
    for i, v in enumerate((72, 68, 74, 82)):  # B A B D ... first time the motif is heard
        play(at(3, 2 + i), motif(i, 5), v, 0.5)
    for i in range(16):  # typing: sixteenths of key-release noise
        t = at(3, 2 + i / 4)
        click(int(RNG.integers(58, 80)), t, -21 + RNG.normal(0, 1.5), pan=RNG.uniform(-0.35, 0.35), hp=500, seconds=0.07)
        cues["typing"].append(frame(t))
    play(b4, motif(4, 5), 80, 1.0, pin=True)  # ... A, resolving on the new chord
    play(b4, ["G2", "D3", "B3", "F#4"], [62, 58, 60, 62], 1.0, hand="L", roll=0.02, pin=True)
    cut(b4)
    click(40, b4, -15, lp=3000, seconds=0.12)
    sfx("send", b4)
    for k, (p, v) in enumerate((("D4", 58), ("F#4", 62), ("A4", 66), ("B4", 70))):
        play(at(4, 2 + k / 2), p, v, 0.3)
    play(b44, ["A2", "E3", "G3", "D4", "E4", "A4"], [74, 66, 64, 68, 66, 78], 0.8, roll=0.004, pin=True)
    cut(b44)
    click(64, b44, -17, hp=900, seconds=0.06)
    sfx("rule", b44)
    for k, (p, v) in enumerate((("A5", 70), ("G5", 74), ("E5", 80), ("D5", 86))):
        play(at(4, 5 + k / 4), p, v, 0.12)
    swell([("A2", 84), ("E3", 80), ("A3", 80), ("D4", 76), ("E4", 76), ("G4", 76)], 1.3, at(5), -8)


def left_hand(bar: int, root: str, octave: int, vel: int, cuts: bool) -> None:
    """Octaves on the clave, pedal re-caught on each."""
    hits = [at(bar, 1 + e / 2) for e in CLAVE] + [at(bar + 1)]
    for j in range(4):
        play(hits[j], [f"{root}{octave}", f"{root}{octave + 1}"], vel - 5 * (j % 2), hits[j + 1] - hits[j] - 0.02, hand="L", roll=0.004, pin=True)
        pedal.append((hits[j] + 0.03, hits[j + 1] - 0.02))
        accent(hits[j])
        if cuts:
            cut(hits[j])


def section_never() -> None:
    """III. It never comes back: the groove, in D. Bars 5-6."""
    for bar, root, octave, inner in ((5, "D", 2, ["A3", "F#4"]), (6, "G", 1, ["D3", "B3"])):
        left_hand(bar, root, octave, 94, cuts=False)
        for e in range(10):
            hit = e in CLAVE
            ps = [motif(e, 4)] + ([motif(e, 5)] if bar == 6 else [])
            play(at(bar, 1 + e / 2), ps, [88 if hit else 70, 76 if hit else 60][: len(ps)], 0.18, pin=hit)
        play(at(bar), inner, 60, 0.9, hand="L")
        play(at(bar, 4), inner, 56, 0.5, hand="L")
        sub(root, at(bar), -8)
        cut(at(bar))
        cut(at(bar, 4))
    whip(at(5, 4), -4)
    sfx("erase", at(5, 4))
    for e, p in zip(CLAVE, ("F#6", "A6", "D7"), strict=False):  # three findings land: a D major triad of pings
        play(at(6, 1 + e / 2), p, 78, 0.2, pin=True, tau=0.3)
        sfx("finding", at(6, 1 + e / 2))


def section_blitz() -> None:
    """IV. Blitz: eight cuts on the bass, B minor then the dominant. Bars 7-8."""
    bm7 = {0: ["B4", "D5", "F#5", "B5"], 3: ["D5", "F#5", "A5", "D6"], 6: ["A4", "D5", "F#5", "A5"], 8: ["D5", "F#5", "B5", "D6"]}
    asus = {0: ["B4", "D5", "E5", "B5"], 3: ["D5", "E5", "A5", "D6"]}
    for bar, root, chords, eighths in ((7, "B", bm7, 10), (8, "A", asus, 6)):
        left_hand(bar, root, 1, 104, cuts=True)
        for e in range(eighths):
            ps = chords.get(e, [motif(e, 4), motif(e, 5)])
            play(at(bar, 1 + e / 2), ps, 104 if e in CLAVE else 90, 0.18, roll=0.003, pin=e in CLAVE)
        sub(root, at(bar), -6)
        sub(root, at(bar, 4), -9)
    play(at(8, 4), ["A4", "C#5", "E5"], 100, 0.3, roll=0.003, pin=True)  # the suspension resolves...
    for k, p in enumerate(("A5", "B5", "C#6", "D6", "E6", "F#6", "G6", "A6")):  # ...and runs for the door
        play(at(8, 4 + k / 4), p, 92 + 4 * k, 0.1, sigma=0.002)
    swell([("B1", 96), ("F#2", 90), ("B2", 90), ("D3", 84), ("F#3", 84)], 0.9, at(7), -8)
    swell([("A1", 100), ("E2", 96), ("A2", 96), ("C#3", 90), ("E3", 90), ("A3", 90), ("C#4", 88)], 1.9, at(9), -3)


def section_pairo() -> None:
    """V. The name, one letter per chord, and home. Bars 9-10."""
    chords = (  # left hand, right hand; the top voice is the motif
        (["G1", "G2", "D3"], ["B4", "D5", "G5", "B5"]),
        (["F#1", "F#2", "D3"], ["A4", "D5", "F#5", "A5"]),
        (["E1", "E2", "B2"], ["B4", "E5", "G5", "B5"]),
        (["C1", "C2", "G2"], ["D5", "E5", "G5", "C6", "D6"]),
        (["A1", "A2", "E3"], ["G4", "A4", "D5", "E5", "A5"]),
    )
    for b, (lh, rh) in enumerate(chords):
        t = at(9, 1 + b)
        play(t, lh, 104, BEAT - 0.03, hand="L", roll=0.003, pin=True)  # held back a shade: the last chord must be the biggest
        play(t, rh[::-1], [112] + [100] * (len(rh) - 1), BEAT - 0.03, roll=0.002, pin=True)  # the letter's note first, on the cut
        pedal.append((t + 0.03, t + BEAT - 0.02))
        accent(t)
        cut(t)
    sub("G", at(9), -8)
    sub("C", at(9, 4), -10)
    home = at(10)
    play(home, ["D1", "D2", "A2", "F#3"], 120, 2.0, hand="L", roll=0.004, pin=True)
    play(home, ["D6", "A5", "F#5", "E5", "D5", "A4"], [122, 114, 112, 108, 112, 110], 2.0, roll=0.003, pin=True)
    pedal.append((home + 0.03, DUR + 1))
    accent(home)
    cut(home)
    sub("D", home, -6)
    ping = at(10, 3)
    play(ping - 0.07, "A6", 50, 0.3)
    play(ping, "D7", 66, 0.3, pin=True)
    sfx("ping", ping)
    echo = strike([("D7", 66)], 1.2)
    for k in (1, 2, 3):  # dotted-eighth echoes, each duller and further out
        put(FXW, filt(echo, "lowpass", 9000 / k), ping + 0.3 * k, -4.5 * k + 1.5, pan=0.5 * (-1) ** k)


# ---------------------------------------------------------------- mix and master


def glue(x: np.ndarray, threshold_db: float = -20.0, ratio: float = 1.6) -> np.ndarray:
    level = 10 * np.log10(uniform_filter1d((x**2).mean(axis=1), round(0.12 * SR)) + 1e-12)
    reduction = uniform_filter1d(-np.maximum(0, level - threshold_db) * (1 - 1 / ratio), round(0.08 * SR))
    return x * db(reduction)[:, None]


def limit(x: np.ndarray) -> np.ndarray:
    """Look-ahead brickwall. Smoothing a min-held gain with a window no wider than the hold cannot overshoot."""
    w = round(0.02 * SR)
    peak = maximum_filter1d(np.abs(x).max(axis=1), 2 * w + 1)
    gain = np.minimum(1.0, db(CEILING_DB) / np.maximum(peak, 1e-9))
    return x * uniform_filter1d(uniform_filter1d(gain, w // 2), w // 2)[:, None]


def true_peak_db(x: np.ndarray) -> float:
    return 20 * math.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max())


def lufs(x: np.ndarray) -> float:
    return float(pyloudnorm.Meter(SR).integrated_loudness(x))


def mixdown() -> np.ndarray:
    if INSTRUMENT == "piano":
        with ThreadPoolExecutor(8) as pool:  # fetch what the score needs, nothing else
            list(pool.map(fetch, {sample_name(n.p, n.vel)[0] for n in notes} | {f"rel{n.p - 20}" for n in notes if n.p < 90}))
    piano, nag = render("piano") * db(GAIN_DB["piano"]), render("nag") * db(GAIN_DB["nag"])

    # I is one microphone in a box; the box opens (band, then width) as the wall of noise grows
    boxed = filt(filt(nag[:, :1].repeat(2, axis=1), "highpass", 240), "lowpass", 4200)
    opening = auto((0, 0), (at(2), 0), (STOP, 1), (DUR, 1))
    nag = boxed * (1 - 0.8 * opening) + nag * 0.8 * opening

    # space is part of the story: none, then close, then wide, then the hall on the last chord
    hall = auto((0, 0), (3.9, 0), (4.0, 0.30), (7.9, 0.30), (8.0, 0.14), (12.0, 0.11), (15.9, 0.11), (16.0, 0.14), (17.9, 0.14), (18.0, 0.42), (DUR, 0.42))
    fxd, fxw = FXD[:N], FXW[:N]
    wet = reverb(piano * hall + fxw * 0.35, HALL) + reverb(piano * 0.10 + nag * 0.12 + fxd * 0.08, ROOM)
    wet = filt(filt(wet, "highpass", 180), "lowpass", 9000)

    stems = {"piano": piano, "nag": nag, "fx dry": fxd, "fx wet": fxw, "reverb": wet}
    print("stem rms dB by section:  I     II    III    IV     V")
    for name, stem in stems.items():
        levels = [10 * math.log10((stem[round(at(2 * i + 1) * SR) : round(at(2 * i + 3) * SR)] ** 2).mean() + 1e-12) for i in range(5)]
        print(f"  {name:8s}            " + " ".join(f"{v:6.1f}" for v in levels))

    out = filt(sum(stems.values()), "highpass", 28)
    low = filt(out, "lowpass", 150)
    out = width(out - low, 0.8 * opening) + low.mean(axis=1, keepdims=True)  # bass in the middle, mono until the box opens
    out += 0.18 * filt(filt(out, "highpass", 2000), "lowpass", 5000) + 0.55 * filt(out, "highpass", 6500)  # presence, air
    out = glue(out)
    out *= auto((0, 1), (STOP + 0.10, 1), (STOP + 0.15, 0), (at(3) - 0.11, 0), (at(3) - 0.10, 1), (DUR - 0.6, 1), (DUR, 1))
    out[-round(0.6 * SR) :] *= (0.5 + 0.5 * np.cos(np.linspace(0, math.pi, round(0.6 * SR))))[:, None]
    out[:24] *= np.linspace(0, 1, 24)[:, None]  # the first thud straddles t=0: start from zero, not mid-click

    gain = 1.0
    for _ in range(6):  # loudness target with the limiter in the loop
        gain *= db(TARGET_LUFS - lufs(limit(out * gain)))
    final = limit(out * gain)
    held = 20 * np.log10((np.abs(final).max(axis=1) + 1e-9) / (np.abs(out * gain).max(axis=1) + 1e-9))
    print(f"limiter: max {-held.min():.1f} dB, over 1 dB for {100 * (held < -1).mean():.1f}% of the piece")
    return final


def timeline() -> dict:
    sections = ("noise", "tell", "never", "blitz", "pairo")
    return {
        "bpm": BPM,
        "beatsPerBar": BEATS,
        "fps": FPS,
        "durationInFrames": frame(DUR),
        "framesPerBeat": frame(BEAT),
        "motif": list(MOTIF),
        "sections": [{"id": s, "from": frame(at(2 * i + 1)), "to": frame(at(2 * i + 3))} for i, s in enumerate(sections)],
        "cuts": sorted(cues["cuts"]),
        "accents": sorted(cues["accents"]),
        "typing": cues["typing"],
        "sfx": sorted(cues["sfx"], key=lambda c: c["frame"]),
        "notes": [
            {"f": round(n.t * FPS, 2), "p": n.p, "v": n.vel, "d": round(n.dur * FPS, 1), "h": n.hand, "b": n.bus}
            for n in sorted(notes, key=lambda n: n.t)
        ],
    }


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def report(x: np.ndarray) -> None:
    def corr(seg: np.ndarray) -> float:
        return float(np.corrcoef(seg[:, 0], seg[:, 1])[0, 1])

    fold = lufs(x.mean(axis=1)) - lufs(x) + 3.01  # 0 = nothing lost when a phone sums it to mono
    print(f"integrated {lufs(x):6.2f} LUFS | true peak {true_peak_db(x):5.2f} dBTP | mono fold-down {fold:+.1f} dB | L/R corr {corr(x):.2f}")
    for i, name in enumerate(("I noise", "II tell", "III never", "IV blitz", "V pairo")):
        seg = x[round(at(2 * i + 1) * SR) : round(at(2 * i + 3) * SR)]
        bars = " ".join(f"{10 * math.log10((b**2).mean()):6.1f}" for b in np.split(seg, 2))
        print(f"  {name:10s} {lufs(seg):6.1f} LUFS  peak {20 * math.log10(np.abs(seg).max()):6.1f} dB  corr {corr(seg):5.2f}  bar rms {bars}")
    QA.mkdir(parents=True, exist_ok=True)
    for name, graph in (("spectrogram", "showspectrumpic=s=1800x700:legend=1:fscale=log:start=25:stop=20000"), ("waveform", "showwavespic=s=1800x400:split_channels=1")):
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(WAV), "-lavfi", graph, str(QA / f"{name}.png")], check=True)


def check(x: np.ndarray) -> None:
    assert x.shape == (N, 2) and np.isfinite(x).all(), "wrong length or NaN"
    assert abs(lufs(x) - TARGET_LUFS) <= 0.5, f"loudness {lufs(x):.2f} LUFS"
    assert true_peak_db(x) <= -1.0, f"true peak {true_peak_db(x):.2f} dBTP"
    assert abs(x.mean()) < 1e-4, "DC offset"
    bar1 = x[: round(BAR * SR)]
    assert np.corrcoef(bar1[:, 0], bar1[:, 1])[0, 1] > 0.98, "bar 1 should be one microphone"
    silence = x[round((STOP + 0.16) * SR) : round((at(3) - 0.12) * SR)]
    assert np.abs(silence).max() < db(-50), "the hard stop is not silent"
    assert len(cues["cuts"]) == len(set(cues["cuts"])) == 35, f"{len(cues['cuts'])} shots"  # 34 cuts + frame 0


def build() -> None:
    for section in (section_noise, section_tell, section_never, section_blitz, section_pairo):
        section()
    x = mixdown()
    WAV.parent.mkdir(parents=True, exist_ok=True)
    sf.write(WAV, x, SR, subtype="PCM_24")
    TIMELINE.write_text(json.dumps(timeline(), separators=(",", ":")) + "\n")
    report(x)
    check(x)
    print(f"ok: {len(notes)} notes, {len(cues['cuts']) - 1} cuts -> {WAV.relative_to(ROOT)}, {TIMELINE.relative_to(ROOT)}")


# ---------------------------------------------------------------- verify the finished film


def verify(mp4: Path) -> None:
    """Does the rendered film cut where the score says, with a sound on every cut?

    Picture: the frame-to-frame change must spike on the cut frame itself. Sound: a note onset
    (a peak of spectral flux) within a frame and a half, or, for the hard stop, the level falling
    away. And the film's audio track must line up with the score it was rendered from.
    """
    tl = json.loads(TIMELINE.read_text())
    grab = lambda *args: subprocess.run([ffmpeg(), "-loglevel", "error", "-i", str(mp4), *args, "-"], capture_output=True, check=True).stdout  # noqa: E731
    frames = np.frombuffer(grab("-vf", "scale=160:90,format=gray", "-f", "rawvideo"), np.uint8).reshape(-1, 90, 160).astype(np.int16)
    audio = np.frombuffer(grab("-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le"), np.float32).reshape(-1, 2)
    assert len(frames) == tl["durationInFrames"], f"{len(frames)} frames, expected {tl['durationInFrames']}"

    mono = audio.mean(axis=1)
    jump = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))  # jump[i]: change from frame i to i+1
    hop = SR // (4 * FPS)  # quarter frames
    spectrum = np.log1p(200 * np.abs(signal.stft(mono, SR, nperseg=1024, noverlap=1024 - hop)[2]))
    flux = np.concatenate([[0.0], np.maximum(0, np.diff(spectrum, axis=1)).sum(axis=0)])  # new energy arriving: note onsets
    level = 10 * np.log10((mono[: len(mono) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1) + 1e-10)

    ref = sf.read(WAV, dtype="float32")[0].mean(axis=1)
    span = round(0.05 * SR)
    a, r = mono[: 5 * SR], ref[: 5 * SR]
    xc = [float(np.dot(a[span + lag : len(a) - span + lag], r[span : len(r) - span])) for lag in range(-span, span)]
    offset_ms = (int(np.argmax(xc)) - span) / SR * 1000

    bad = 0
    print("frame   picture jump   x median   of local max   sound: onset   lag       drop")
    for f in tl["cuts"][1:]:
        spike = jump[f - 1] / max(float(np.median(jump[max(0, f - 9) : f + 8])), 0.05)
        share = jump[f - 1] / jump[max(0, f - 4) : f + 3].max()  # 1.0: nothing near the cut moves more than the cut
        c = 4 * f
        window = flux[c - 6 : c + 7]  # a frame and a half either side
        onset = float(window.max() / (np.median(flux[max(0, c - 60) : c + 60]) + 1e-9))
        lag_ms = (int(np.argmax(window)) - 6) * hop / SR * 1000
        drop = float(level[max(0, c - 8) : c].max() - level[c : c + 48].min())  # the hard stop has no onset: it has silence
        ok = spike >= 3 and share >= 0.6 and (onset >= 2 or drop >= 40)
        bad += not ok
        print(f"{f:5d}   {jump[f - 1]:12.2f}   {spike:7.1f}x   {100 * share:11.0f}%   {onset:11.1f}x   {lag_ms:+4.0f} ms   {drop:5.1f} dB   {'ok' if ok else 'FAIL'}")
    print(f"audio/video offset vs source score: {offset_ms:+.1f} ms")
    assert abs(offset_ms) < 10, "audio drifted from the score"
    assert not bad, f"{bad} cut(s) out of sync"
    print(f"ok: {len(tl['cuts']) - 1} cuts land on the score")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "verify":
        verify(Path(sys.argv[2]))
    else:
        build()
