import {loadFont as loadGrotesk} from "@remotion/google-fonts/SpaceGrotesk";
import {loadFont as loadMono} from "@remotion/google-fonts/SpaceMono";
import type React from "react";
import {useLayoutEffect, useRef} from "react";
import {AbsoluteFill, Easing, interpolate, random, useCurrentFrame} from "remotion";
import timeline from "./timeline.json";

/**
 * The score is the master clock. Every cut, accent and keystroke in the film is read from
 * timeline.json, which score/score.py writes next to the audio. Nothing here hard-codes a
 * frame number, so picture cannot drift from sound. (It also means these timings are not
 * editable from the Studio: change the score instead.)
 */
export const TL = timeline;
export const BEAT = TL.framesPerBeat;

export const GROTESK = loadGrotesk("normal", {weights: ["500", "700"], subsets: ["latin"]}).fontFamily;
export const MONO = loadMono("normal", {weights: ["400", "700"], subsets: ["latin"]}).fontFamily;

/** Lifted from the landing page: `.landing` in dashboard/src/views/HomeView.vue. */
export const C = {
  bg: "#08090d",
  card: "#0f1118",
  border: "rgba(255, 255, 255, 0.08)",
  text: "#f5f7fa",
  sub: "#a6abb5",
  muted: "#6c7280",
  orange: "#ff7a32",
  gradient: "linear-gradient(90deg, #e05500, #ffcc66)",
  green: "#38d996",
  ink: "#0b0c10",
} as const;

/** The world before Pairo has no colour in it. */
export const GREY = {hi: "#d9dde4", mid: "#8a909c", low: "#3a3f4b", dim: "#23262f"} as const;

export const OUT = Easing.bezier(0.16, 1, 0.3, 1); // the landing page's own ease
export const BACK = Easing.bezier(0.34, 1.56, 0.64, 1); // and its overshoot

export const tween = (frame: number, range: [number, number], out: [number, number], easing = OUT) =>
  interpolate(frame, range, out, {easing, extrapolateLeft: "clamp", extrapolateRight: "clamp"});

export const section = (id: string) => TL.sections.find((s) => s.id === id)!;
export const sfx = (id: string) => TL.sfx.filter((s) => s.id === id).map((s) => s.frame);

/** Which shot of a section we are in, and how far into it. Shots start on the score's cut frames. */
export const useShots = (id: string) => {
  const frame = useCurrentFrame();
  const {from, to} = section(id);
  const cuts = TL.cuts.filter((c) => c >= from && c < to).map((c) => c - from);
  const shot = Math.max(0, cuts.filter((c) => c <= frame).length - 1);
  return {frame, shot, t: frame - cuts[shot], from};
};

/** 1 on a hit, decaying after it. */
export const pulse = (frame: number, hits: number[], decay = 8) =>
  hits.reduce((v, h) => (h <= frame ? Math.max(v, Math.exp(-(frame - h) / decay)) : v), 0);

/** A damped swing after a hit: antennas, cards settling. */
export const swing = (frame: number, hits: number[], amp = 16, decay = 10) =>
  hits.reduce((v, h) => (h <= frame ? v + amp * Math.exp(-(frame - h) / decay) * Math.sin((frame - h) * 0.55) : v), 0);

export const blinkAt = (frame: number, at: number) => Math.max(0, 1 - Math.abs(frame - at - 3) / 3.5);

/**
 * Text that rises out of its own baseline. It is already half out on its first frame, so when it
 * starts on a cut the cut frame carries the word, not an empty mask.
 */
export const Rise: React.FC<{t: number; delay?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({t, delay = 0, children, style}) => (
  <span style={{display: "inline-block", overflow: "hidden", verticalAlign: "bottom", paddingBottom: "0.12em", marginBottom: "-0.12em", ...style}}>
    <span style={{display: "inline-block", translate: `0 ${t < delay ? 105 : tween(t, [delay, delay + 9], [50, 0])}%`}}>{children}</span>
  </span>
);

export const Chip: React.FC<{children: React.ReactNode; color?: string; style?: React.CSSProperties}> = ({children, color = C.sub, style}) => (
  <span style={{display: "inline-block", fontFamily: MONO, fontWeight: 700, fontSize: 36, color, border: `2px solid ${color}`, borderRadius: 100, padding: "10px 28px", whiteSpace: "nowrap", ...style}}>
    {children}
  </span>
);

/** Pairo's world has depth: the landing page's 64 px grid and orange glow, drifting slowly. */
export const Backdrop: React.FC<{x?: number; y?: number; glow?: number}> = ({x = 50, y = 50, glow = 0.13}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <AbsoluteFill
        style={{
          backgroundImage: "linear-gradient(rgba(255, 255, 255, 0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.055) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          backgroundPosition: `${frame * 0.12}px ${frame * 0.08}px`,
          maskImage: `radial-gradient(ellipse at ${x}% ${y}%, black 12%, transparent 78%)`,
        }}
      />
      <AbsoluteFill style={{backgroundImage: `radial-gradient(circle at ${x}% ${y}%, rgba(255, 122, 50, ${glow}), transparent 46%)`}} />
    </AbsoluteFill>
  );
};

/** A hairline keyboard along the bottom edge: each of the 88 keys lights when the score plays it. */
export const KeyStrip: React.FC = () => {
  const frame = useCurrentFrame();
  const lit = new Map<number, number>();
  for (const n of TL.notes) {
    if (n.f > frame || frame - n.f > 40) continue;
    lit.set(n.p, Math.max(lit.get(n.p) ?? 0, (n.v / 127) * Math.exp(-(frame - n.f) / 9)));
  }
  const colour = frame < section("tell").from ? GREY.mid : C.text;
  return (
    <AbsoluteFill style={{pointerEvents: "none"}}>
      {Array.from({length: 88}, (_, i) => {
        const v = lit.get(i + 21) ?? 0;
        return <div key={i} style={{position: "absolute", left: 140 + (i / 87) * 1640, bottom: 30, width: 3, height: 5 + 34 * v, borderRadius: 2, backgroundColor: colour, opacity: 0.14 + 0.86 * v}} />;
      })}
    </AbsoluteFill>
  );
};

/** Film grain and a vignette: the grain keeps dark gradients from banding once the encoder gets hold of them. */
export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const ctx = ref.current?.getContext("2d");
    if (!ctx) return;
    const image = ctx.createImageData(960, 540);
    for (let i = 0, seed = ((frame + 1) * 2654435761) >>> 0; i < image.data.length; i += 4) {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      image.data[i] = image.data[i + 1] = image.data[i + 2] = 255;
      image.data[i + 3] = (seed >>> 24) * 0.03;
    }
    ctx.putImageData(image, 0, 0);
  }, [frame]);
  return (
    <AbsoluteFill style={{pointerEvents: "none", backgroundImage: "radial-gradient(ellipse at center, transparent 62%, rgba(0, 0, 0, 0.2) 100%)"}}>
      <canvas ref={ref} width={960} height={540} style={{width: "100%", height: "100%"}} />
    </AbsoluteFill>
  );
};

/** The whole frame flinches when the low strings hit. */
export const useImpact = () => {
  const frame = useCurrentFrame();
  const hit = pulse(frame, sfx("sub"), 5);
  const jolt = (axis: string) => Math.round((random(`${axis}${frame}`) - 0.5) * 22 * hit);
  return {scale: String(1 + 0.022 * hit), translate: `${jolt("x")}px ${jolt("y")}px`};
};
