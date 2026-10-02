import type React from "react";
import {AbsoluteFill, Easing} from "remotion";
import {BACK, BEAT, Backdrop, C, Chip, GROTESK, MONO, Rise, TL, blinkAt, pulse, section, swing, tween, useShots} from "../kit";
import {Mascot} from "../Mascot";

const SAID = "@pairo ignore we don't use Redis in this project"; // the README's own example
const TYPED = [3, 6, 10, 13, 16, 19, 22, 24, 26, 29, 32, 35, 40, 44, 48, 48]; // characters on screen after each keystroke; the last one is Enter

/** What the developer wrote becomes the rule: same words, new order. Columns are monospace cells. */
const MORPH: {word: string; from: number | null; to: number | null}[] = [
  {word: "we", from: 0, to: null},
  {word: "don't", from: 3, to: null},
  {word: "use", from: 9, to: 24},
  {word: "Redis", from: 13, to: 28},
  {word: "in", from: 19, to: null},
  {word: "this", from: 22, to: 2},
  {word: "project", from: 27, to: 7},
  {word: "-", from: null, to: 0},
  {word: "does", from: null, to: 15},
  {word: "not", from: null, to: 20},
  {word: ".", from: null, to: 33},
];

/** II. Tell it once. Colour arrives with Pairo; the keystrokes are the score's sixteenths. */
export const TellItOnce: React.FC = () => {
  const {shot, t} = useShots("tell");
  return shot === 0 ? <Thread t={t} /> : shot === 1 ? <Answer t={t} /> : <Rule t={t} />;
};

const Thread: React.FC<{t: number}> = ({t}) => {
  const {from} = section("tell");
  const typed = TYPED[TL.typing.filter((f) => f - from <= t).length - 1] ?? 0;
  const melody = TL.notes.filter((n) => n.h === "R" && n.p >= 80 && n.f >= from + BEAT - 2 && n.f < from + 5 * BEAT).map((n) => Math.round(n.f - from));
  const typing = typed > 0 && typed < SAID.length;
  const sent = 5 * BEAT - 6;
  const caret = (
    <span style={{display: "inline-block", width: "0.5ch", height: "1.05em", marginLeft: 6, verticalAlign: "-0.18em", backgroundColor: C.orange, opacity: typing || Math.floor(t / 14) % 2 === 0 ? 1 : 0}} />
  );
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, color: C.text}}>
      <Backdrop x={54} y={70} glow={0.07 + 0.05 * pulse(t, melody, 10)} />
      <AbsoluteFill style={{scale: String(tween(t, [0, 5 * BEAT], [1, 1.04], Easing.linear)), transformOrigin: "30% 62%"}}>
        <div style={{position: "absolute", left: 140, top: 92, fontSize: 132, fontWeight: 700, letterSpacing: "-0.04em", lineHeight: 1}}>
          <Rise t={t}>Tell it once.</Rise>
        </div>
        <div style={{position: "absolute", left: 140, top: 310, width: 1640, display: "flex", gap: 32, alignItems: "flex-start", opacity: tween(t, [2, 12], [0, 1]), translate: `0 ${tween(t, [2, 16], [28, 0])}px`}}>
          <Mascot size={120} look={[0.5, 0.7]} glow={pulse(t, melody, 7)} antenna={swing(t, melody, 12)} blink={blinkAt(t, 3 * BEAT - 8)} />
          <div style={{flex: 1, backgroundColor: C.card, border: `2px solid ${C.border}`, borderRadius: 20, padding: "28px 40px 32px"}}>
            <div style={{fontSize: 34, fontWeight: 500, color: C.sub}}>
              pairo <span style={{color: C.muted}}>commented on api/cart.ts</span>
            </div>
            <div style={{marginTop: 14, fontFamily: MONO, fontSize: 36, color: C.sub}}>
              🌱 <b style={{color: C.text}}>eco</b> : Result recomputed on every request
            </div>
            <div style={{marginTop: 4, fontSize: 54, fontWeight: 700, letterSpacing: "-0.02em"}}>Cache it in Redis.</div>
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            left: 292,
            top: 640,
            width: 1488,
            height: 250,
            border: `3px solid ${C.orange}`,
            borderRadius: 20,
            backgroundColor: "rgba(8, 9, 13, 0.7)",
            boxShadow: "0 0 80px rgba(255, 122, 50, 0.14)",
            padding: "30px 44px",
            fontFamily: MONO,
            fontWeight: 700,
            fontSize: 64,
            lineHeight: 1.4,
            whiteSpace: "pre",
            // in on the first chord; sent (up and away) on the last sixteenth before the cut
            opacity: tween(t, [8, 18], [0, 1]) * tween(t, [sent, sent + 6], [1, 0.2], Easing.in(Easing.quad)),
            translate: `0 ${tween(t, [8, 22], [28, 0]) - tween(t, [sent, sent + 6], [0, 70], Easing.in(Easing.cubic))}px`,
          }}
        >
          <div>
            <span style={{color: C.orange}}>{SAID.slice(0, Math.min(typed, 6))}</span>
            {SAID.slice(6, Math.min(typed, 13))}
            {typed <= 14 ? caret : null}
          </div>
          <div>
            {SAID.slice(14, Math.max(typed, 14))}
            {typed > 14 ? caret : null}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Answer: React.FC<{t: number}> = ({t}) => {
  const steps = [0, 1, 2, 3].map((k) => BEAT * (1 + k / 2)); // the four notes that climb under Pairo's answer
  const word = (i: number): React.CSSProperties => ({display: "inline-block", opacity: t >= steps[i] ? 1 : 0, translate: `0 ${tween(t, [steps[i], steps[i] + 8], [18, 0])}px`});
  const dive = tween(t, [3 * BEAT - 9, 3 * BEAT], [0, 1], Easing.in(Easing.cubic)); // into the file name, and the film cuts to the file
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, color: C.text, scale: String(1 + 3.4 * dive), transformOrigin: "78% 64.5%", filter: `blur(${7 * dive}px)`}}>
      <Backdrop x={24} y={52} glow={0.12 + 0.08 * pulse(t, [0, ...steps], 9)} />
      <div style={{position: "absolute", left: 140, top: 104, fontFamily: MONO, fontSize: 38, color: C.muted, borderLeft: `4px solid ${C.muted}`, paddingLeft: 26}}>
        <span style={{color: C.orange}}>@pairo</span>
        {SAID.slice(6)}
      </div>
      <div style={{position: "absolute", left: 0, right: 0, top: 280, display: "flex", justifyContent: "center", alignItems: "center", gap: 84}}>
        <Mascot size={480} look={[0.85, 0.05]} blink={blinkAt(t, BEAT + 8)} antenna={swing(t, [0, ...steps], 13)} glow={pulse(t, [0, ...steps], 6)} squash={0.1 * Math.exp(-t / 5) * Math.cos(t * 0.6)} />
        <div>
          <div style={{fontSize: 150, fontWeight: 700, letterSpacing: "-0.045em", lineHeight: 1.02, scale: String(tween(t, [0, 10], [1.07, 1])), transformOrigin: "0 60%"}}>
            👍 Ignored
            <br />
            on this PR.
          </div>
          {/* two words on each of the first two notes; the file name is hit again by the last two */}
          <div style={{marginTop: 46, fontSize: 66, fontWeight: 500, color: C.sub, display: "flex", gap: 20, alignItems: "center"}}>
            <span style={word(0)}>Rule proposed</span>
            <span style={word(1)}>in</span>
            <span style={{...word(1), scale: String(1 + 0.2 * pulse(t, steps.slice(1), 5)), fontFamily: MONO, fontWeight: 700, fontSize: 62, color: C.orange, backgroundColor: "rgba(255, 122, 50, 0.13)", borderRadius: 16, padding: "4px 24px"}}>.pairo.md</span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Rule: React.FC<{t: number}> = ({t}) => {
  const run = [0, 1, 2, 3].map((k) => BEAT * (1 + k / 4)); // the sixteenths that run into the drop
  const move = tween(t, [3, 21], [0, 1], Easing.bezier(0.65, 0, 0.35, 1));
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: MONO, color: C.text}}>
      <Backdrop x={50} y={46} glow={0.08 + 0.1 * tween(t, [0, 2 * BEAT], [0, 1], Easing.in(Easing.cubic))} />
      <AbsoluteFill style={{scale: String(tween(t, [0, 2 * BEAT], [1, 1.07], Easing.in(Easing.cubic))), transformOrigin: "50% 48%"}}>
        <div style={{position: "absolute", left: 140, top: 286, width: 1640, borderRadius: 22, backgroundColor: C.card, border: `2px solid ${C.border}`, overflow: "hidden"}}>
          <div style={{display: "flex", alignItems: "center", padding: "24px 40px", borderBottom: `2px solid ${C.border}`, fontSize: 36}}>
            <span style={{fontWeight: 700}}>.pairo.md</span>
            <span style={{marginLeft: "auto", color: C.muted}}>branch pairo/context</span>
          </div>
          <div style={{padding: "34px 0 44px", fontSize: 64, fontWeight: 700, lineHeight: 1.75}}>
            <div style={{display: "flex"}}>
              <span style={{width: 150, textAlign: "right", color: C.muted, fontWeight: 400}}>1</span>
              <span style={{marginLeft: 90, color: C.muted}}># Pairo context</span>
            </div>
            <div style={{display: "flex", position: "relative"}}>
              <div style={{position: "absolute", inset: 0, width: `${tween(t, [run[0], run[0] + 10], [0, 100])}%`, backgroundColor: "rgba(56, 217, 150, 0.13)"}} />
              <span style={{width: 150, textAlign: "right", color: C.muted, fontWeight: 400}}>2</span>
              <span style={{width: 90, textAlign: "center", color: C.green, scale: String(tween(t, [run[1], run[1] + 8], [0, 1], BACK))}}>+</span>
              <span style={{position: "relative", flex: 1}}>
                {MORPH.map(({word, from, to}) => {
                  const stays = from !== null && to !== null;
                  const column = stays ? from + (to - from) * move : (from ?? to)!;
                  const opacity = stays ? 1 : to === null ? tween(t, [1, 9], [1, 0]) : tween(t, [17, 23], [0, 1]);
                  // words heading left go over the top, words heading right duck under: they pass without colliding
                  const lift = stays ? Math.sign(to - from) * Math.sin(move * Math.PI) * 42 : to === null ? tween(t, [1, 9], [0, 40], Easing.in(Easing.quad)) : tween(t, [17, 23], [-24, 0]);
                  return (
                    <span key={word} style={{position: "absolute", left: `${column}ch`, top: 0, opacity, translate: `0 ${lift}px`}}>
                      {word === "this" && move > 0.5 ? "This" : word}
                    </span>
                  );
                })}
                &nbsp;
              </span>
            </div>
          </div>
        </div>
        <div style={{position: "absolute", left: 140, top: 770, opacity: t >= run[2] ? 1 : 0, scale: String(tween(t, [run[2], run[2] + 9], [0.8, 1], BACK)), transformOrigin: "0 50%"}}>
          <Chip color={C.green} style={{fontSize: 40}}>
            PR opened · Add Pairo context rule
          </Chip>
        </div>
        <Mascot size={340} look={[-0.7, -0.7]} antenna={swing(t, [run[3] - 4], 16)} glow={pulse(t, run, 6)} style={{position: "absolute", right: 170, top: 760, translate: `0 ${tween(t, [run[3] - 8, run[3] + 6], [400, 0], BACK)}px`}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
