import type React from "react";
import {AbsoluteFill, Easing} from "remotion";
import {BACK, BEAT, Backdrop, C, GREY, GROTESK, MONO, Rise, blinkAt, pulse, swing, tween, useShots} from "../kit";
import {Mascot} from "../Mascot";

const DIFF = [
  {n: 14, code: "export async function checkout(cart) {"},
  {n: 15, code: "  const prices = await db.prices.all()", added: true},
  {n: 16, code: "  const total = sum(cart, prices)", added: true},
  {n: 17, code: "  return charge(total)", added: true},
  {n: 18, code: "}"},
];
const GHOST = "Cache it in Redis.";
/** Comment format and the a11y wording are the product's own (github/client.py, domain/rules/alt.py). */
const FINDINGS = [
  {emoji: "🔧", axis: "crafts", issue: "Dead code after `return`", where: "api/cart.ts:41"},
  {emoji: "🌱", axis: "eco", issue: "N+1 query inside a loop", where: "api/cart.ts:18"},
  {emoji: "♿", axis: "a11y", issue: "`<img>` without `alt` attribute", where: "ui/Cart.vue:9"},
];

/** III. It never comes back. The groove arrives, the old comment tries to return and is wiped. */
export const NeverBack: React.FC = () => {
  const {shot, t} = useShots("never");
  if (shot === 0) return <NextPr t={t} />;
  if (shot === 1) return <Title t={t} />;
  return <Findings t={shot === 2 ? t : t + 3 * BEAT} close={shot === 3} />;
};

const NextPr: React.FC<{t: number}> = ({t}) => {
  const eighths = [0, 1, 2, 3, 4, 5].map((k) => (k * BEAT) / 2);
  const line = Math.min(DIFF.length, eighths.filter((f) => f <= t).length) - 1;
  const haunt = 1.5 * BEAT; // second accent: the old suggestion starts to come back...
  const wiped = 3 * BEAT; // ...and is gone by the third, where the film cuts
  const ghost = GHOST.slice(0, Math.max(0, Math.floor((t - haunt) / 5) * 5 + 5));
  const strike = tween(t, [wiped - 16, wiped - 6], [0, 100]);
  const reading = t >= haunt ? 1 : line; // Pairo's eye goes back to the line the old comment was about
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, color: C.text}}>
      <Backdrop x={72} y={50} glow={0.1 + 0.06 * pulse(t, eighths, 6)} />
      <div style={{position: "absolute", left: 140, top: 92, fontFamily: MONO, fontWeight: 700, fontSize: 38, letterSpacing: "0.14em", color: C.muted}}>NEXT PULL REQUEST</div>
      <div
        style={{
          position: "absolute",
          left: 140,
          top: 170,
          width: 1210,
          borderRadius: 22,
          backgroundColor: C.card,
          border: `2px solid ${C.border}`,
          transformOrigin: "0 50%",
          transform: `perspective(2400px) translateX(${tween(t, [0, 22], [220, 0])}px) rotateY(${tween(t, [0, 26], [-20, -4])}deg)`,
        }}
      >
        <div style={{display: "flex", alignItems: "center", gap: 22, padding: "28px 40px", borderBottom: `2px solid ${C.border}`}}>
          <span style={{fontSize: 46, fontWeight: 700, letterSpacing: "-0.02em"}}>feat: cache checkout totals</span>
          <span style={{fontFamily: MONO, fontSize: 36, color: C.muted}}>#483</span>
          <span style={{marginLeft: "auto", fontSize: 30, fontWeight: 700, color: C.green, backgroundColor: "rgba(56, 217, 150, 0.1)", borderRadius: 12, padding: "6px 20px"}}>Open</span>
        </div>
        <div style={{padding: "26px 0 34px", fontFamily: MONO, fontSize: 38, lineHeight: 1.8, whiteSpace: "pre"}}>
          {DIFF.map((row, i) => (
            <div key={row.n}>
              <div style={{display: "flex", opacity: i <= line ? 1 : 0, backgroundColor: i === reading ? "rgba(255, 122, 50, 0.16)" : row.added ? "rgba(56, 217, 150, 0.07)" : "transparent"}}>
                <span style={{width: 110, textAlign: "right", color: C.muted}}>{row.n}</span>
                <span style={{width: 70, textAlign: "center", color: C.green}}>{row.added ? "+" : ""}</span>
                <span style={{color: row.added ? C.text : C.sub}}>{row.code}</span>
              </div>
              {i === 1 && t >= haunt ? (
                <div style={{position: "relative", margin: "10px 0 12px 180px", width: 760, display: "flex", alignItems: "center", gap: 20, padding: "14px 26px", border: `3px dashed ${GREY.low}`, borderRadius: 16, fontFamily: GROTESK, fontWeight: 700, fontSize: 46, color: GREY.mid, opacity: tween(t, [wiped - 8, wiped - 1], [1, 0.25]), translate: `${tween(t, [wiped - 8, wiped], [0, 90])}px 0`}}>
                  <div style={{width: 44, height: 44, borderRadius: 11, backgroundColor: GREY.low, flexShrink: 0}} />
                  {ghost}
                  <div style={{position: "absolute", left: 16, top: "50%", height: 7, borderRadius: 4, width: `calc(${strike}% - 32px)`, backgroundColor: C.orange}} />
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </div>
      <Mascot
        size={370}
        look={t >= haunt ? [-0.95, 0.05] : [-0.9, -0.45 + 0.3 * Math.max(0, line)]}
        glow={pulse(t, eighths, 5)}
        antenna={swing(t, [0, haunt], 15)}
        blink={blinkAt(t, wiped - 14)}
        style={{position: "absolute", left: 1430, top: 320, translate: `0 ${Math.sin(t / 9) * 6}px`}}
      />
    </AbsoluteFill>
  );
};

const Title: React.FC<{t: number}> = ({t}) => (
  <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, fontWeight: 700, color: C.text, letterSpacing: "-0.045em"}}>
    <Backdrop x={30} y={50} glow={0.1 + 0.08 * pulse(t, [0, BEAT], 8)} />
    {/* the old comment, still carrying its strike-through, thrown out of frame across the cut */}
    <svg width={0} height={0}>
      <filter id="thrown" x="-20%" width="140%">
        <feGaussianBlur stdDeviation={`${tween(t, [0, 30], [2, 46], Easing.in(Easing.quad))} 0`} />
      </filter>
    </svg>
    <div style={{position: "absolute", left: 140 + tween(t, [0, 30], [240, 2300], Easing.in(Easing.quad)), top: 800, fontSize: 132, lineHeight: 1, whiteSpace: "nowrap", color: GREY.mid, filter: "url(#thrown)", opacity: tween(t, [4, 28], [0.85, 0], Easing.linear)}}>
      {GHOST}
      <div style={{position: "absolute", left: -20, right: -20, top: "52%", height: 10, borderRadius: 5, backgroundColor: C.orange}} />
    </div>
    <div style={{position: "absolute", left: 132, top: 232, fontSize: 250, lineHeight: 1.02}}>
      <div>
        <Rise t={t}>
          It <span style={{color: C.orange}}>never</span>
        </Rise>
      </div>
      <div>
        <Rise t={t} delay={BEAT}>
          comes back.
        </Rise>
      </div>
    </div>
  </AbsoluteFill>
);

const code = (text: string) =>
  text.split("`").map((part, i) =>
    i % 2 ? (
      <span key={i} style={{fontFamily: MONO, fontSize: "0.86em", backgroundColor: "rgba(255, 255, 255, 0.08)", borderRadius: 10, padding: "2px 12px"}}>
        {part}
      </span>
    ) : (
      part
    ),
  );

const Findings: React.FC<{t: number; close: boolean}> = ({t, close}) => {
  const pops = [0, 1.5 * BEAT, 3 * BEAT]; // three accents, three findings; the film cuts in on the third
  const last = 4 * BEAT;
  const newest = pops.filter((f) => f <= t).length - 1;
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, color: C.text}}>
      <Backdrop x={22} y={52} glow={0.11 + 0.08 * pulse(t, [...pops, last], 8)} />
      <AbsoluteFill style={{scale: close ? "1.12" : "1", transformOrigin: "62% 62%"}}>
        <Mascot
          size={470}
          look={[0.9, (newest - 1) * 0.6]}
          glow={pulse(t, pops, 7)}
          antenna={swing(t, [...pops, last], 15)}
          squash={pops.reduce((v, f) => (f <= t ? v + 0.09 * Math.exp(-(t - f) / 5) * Math.cos((t - f) * 0.6) : v), 0)}
          blink={blinkAt(t, last)}
          style={{position: "absolute", left: 170, top: 290}}
        />
        {FINDINGS.map((f, i) =>
          t < pops[i] ? null : (
            <div
              key={f.axis}
              style={{
                position: "absolute",
                left: 720,
                top: 214 + i * 222,
                width: 1060,
                padding: "26px 38px 30px",
                borderRadius: 22,
                backgroundColor: C.card,
                border: `2px solid ${C.border}`,
                transformOrigin: "0 50%",
                scale: String(tween(t, [pops[i], pops[i] + 11], [0.84, 1], BACK)),
                translate: `${tween(t, [pops[i], pops[i] + 11], [70, 0])}px 0`,
              }}
            >
              <div style={{display: "flex", alignItems: "center", fontFamily: MONO, fontSize: 34}}>
                <span style={{fontWeight: 700, color: C.orange, border: `2px solid ${C.orange}`, borderRadius: 100, padding: "4px 24px", scale: String(1 + 0.12 * pulse(t, [last], 6))}}>
                  {f.emoji} {f.axis}
                </span>
                <span style={{marginLeft: "auto", color: C.muted}}>{f.where}</span>
              </div>
              <div style={{marginTop: 16, fontSize: 58, fontWeight: 700, letterSpacing: "-0.025em", whiteSpace: "nowrap"}}>{code(f.issue)}</div>
            </div>
          ),
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
