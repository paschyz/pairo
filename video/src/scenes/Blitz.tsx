import type React from "react";
import {AbsoluteFill} from "remotion";
import {BACK, BEAT, Backdrop, C, Chip, GROTESK, MONO, Rise, tween, useShots} from "../kit";

/** The four claims are the README's "Why Pairo?"; the proof under each is the README's too. */
const CLAIMS = [
  {lines: ["It", "learns."], proof: ["👎 reaction", "resolved thread", "@pairo ignore"]},
  {lines: ["It's", "transparent."], proof: ["tracked", "visible", "reversible"]},
  {lines: ["It's", "fast."], proof: ["cached result", "zero LLM cost"]},
  {lines: ["It's", "yours."], proof: ["open-source", "self-hosted"]},
];
/** The three review axes and what each looks for (backend/src/pairo/infrastructure/llm/prompt.py). */
const AXES = [
  {emoji: "🔧", name: "crafts", what: "naming · duplication · dead code"},
  {emoji: "🌱", name: "eco", what: "N+1 queries · pagination · heavy deps"},
  {emoji: "♿", name: "a11y", what: "alt text · contrast · keyboard"},
];

/** IV. Blitz. Eight shots, cut on the left hand: long, long, short, short, twice. */
export const Blitz: React.FC = () => {
  const {shot, t} = useShots("blitz");
  if (shot < 4) return <Claim n={shot} t={t} />;
  if (shot < 7) return <Axis n={shot - 4} t={t} />;
  return <Implode t={t} />;
};

const Claim: React.FC<{n: number; t: number}> = ({n, t}) => {
  const {lines, proof} = CLAIMS[n];
  const lit = n % 2 === 1; // orange ground, ink type
  const ink = lit ? C.ink : C.text;
  const size = Math.min(350, 1640 / (0.56 * lines[1].length));
  const verb: React.CSSProperties = [
    {color: C.orange},
    {},
    {translate: `${tween(t, [0, 7], [-320, 0])}px 0`, transform: "skewX(-11deg)"},
    {scale: String(tween(t, [0, 11], [1.32, 1], BACK)), transformOrigin: "0 70%"},
  ][n];
  const solid = n === 1 ? tween(t, [3, 20], [100, 0]) : 0; // "transparent." starts as an outline and fills in
  return (
    <AbsoluteFill style={{backgroundColor: lit ? C.orange : C.bg, fontFamily: GROTESK, fontWeight: 700, color: ink, letterSpacing: "-0.045em"}}>
      {lit ? null : <Backdrop x={30} y={52} glow={0.1} />}
      {n === 2
        ? [0, 1, 2, 3, 4].map((i) => (
            <div key={i} style={{position: "absolute", left: tween(t, [i, i + 12], [1920, -900]), top: 250 + i * 118, width: 500 + i * 90, height: 8, borderRadius: 4, backgroundColor: C.orange, opacity: 0.8}} />
          ))
        : null}
      <div style={{position: "absolute", left: 140, top: 128, fontSize: 176, lineHeight: 1}}>
        <Rise t={t}>{lines[0]}</Rise>
      </div>
      <div style={{position: "absolute", left: 132, top: 330, fontSize: size, lineHeight: 1.1, whiteSpace: "nowrap", ...verb}}>
        <Rise t={t}>{n === 1 ? <span style={{color: "transparent", WebkitTextStroke: `5px ${ink}`}}>{lines[1]}</span> : lines[1]}</Rise>
        {n === 1 ? (
          <div style={{position: "absolute", inset: 0, clipPath: `inset(0 ${solid}% 0 0)`}}>
            <Rise t={t}>{lines[1]}</Rise>
          </div>
        ) : null}
      </div>
      <div style={{position: "absolute", left: 140, top: 826, display: "flex", gap: 22, letterSpacing: 0}}>
        {proof.map((p, i) => (
          <Chip key={p} color={ink} style={{fontSize: 42, opacity: t >= 5 + i * 4 ? 1 : 0, translate: `0 ${tween(t, [5 + i * 4, 13 + i * 4], [22, 0])}px`}}>
            {p}
          </Chip>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Axis: React.FC<{n: number; t: number}> = ({n, t}) => {
  const {emoji, name, what} = AXES[n];
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, color: C.text}}>
      <Backdrop x={78} y={44} glow={0.14} />
      <div style={{position: "absolute", left: 140, top: 176, fontFamily: GROTESK, fontWeight: 500, fontSize: 56, color: C.muted}}>Pairo reviews</div>
      <div style={{position: "absolute", left: 122, top: 290, fontFamily: MONO, fontWeight: 700, fontSize: 400, lineHeight: 1.05, letterSpacing: "-0.06em"}}>
        <Rise t={t}>{name}</Rise>
      </div>
      <div style={{position: "absolute", right: 150, top: 300, fontSize: 250, lineHeight: 1, scale: String(tween(t, [1, 12], [0.4, 1], BACK)), rotate: `${tween(t, [1, 14], [-24, 0], BACK)}deg`}}>{emoji}</div>
      <div style={{position: "absolute", left: 140, top: 806, fontFamily: MONO, fontWeight: 700, fontSize: 46, color: C.orange, opacity: tween(t, [5, 12], [0, 1]), translate: `0 ${tween(t, [5, 14], [20, 0])}px`}}>{what}</div>
      <div style={{position: "absolute", left: 140, top: 924, display: "flex", gap: 14}}>
        {AXES.map((a, i) => (
          <div key={a.name} style={{width: i === n ? 120 : 40, height: 10, borderRadius: 5, backgroundColor: i === n ? C.orange : "rgba(255, 255, 255, 0.16)"}} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Implode: React.FC<{t: number}> = ({t}) => {
  const sixteenth = BEAT / 4; // the piano runs upward in sixteenths; each one folds an axis into the dot
  const folded = Math.floor(t / sixteenth);
  const radius = [34, 74, 118, 168][Math.min(3, folded)] * tween(t, [folded * sixteenth, folded * sixteenth + 5], [0.7, 1], BACK);
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, color: C.text, fontFamily: MONO, fontWeight: 700, fontSize: 150, letterSpacing: "-0.05em"}}>
      <Backdrop x={50} y={67} glow={0.1 + 0.05 * folded} />
      {AXES.map((a, i) => {
        const fold = tween(t, [(i + 1) * sixteenth, (i + 2) * sixteenth], [0, 1]);
        const x = [270, 880, 1250][i];
        return (
          <div key={a.name} style={{position: "absolute", left: x + (960 - x - 150) * fold, top: 260 + 380 * fold, lineHeight: 1, opacity: 1 - fold ** 3, scale: String(1 - 0.9 * fold)}}>
            {a.name}
          </div>
        );
      })}
      <div style={{position: "absolute", left: 960 - radius, top: 720 - radius, width: 2 * radius, height: 2 * radius, borderRadius: "50%", backgroundColor: C.orange, boxShadow: `0 0 ${radius}px rgba(255, 122, 50, 0.55)`}} />
    </AbsoluteFill>
  );
};
