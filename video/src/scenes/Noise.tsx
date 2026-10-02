import type React from "react";
import {AbsoluteFill} from "remotion";
import {C, GREY, GROTESK, MONO, useShots} from "../kit";

const COMMENT = "Cache it in Redis.";
const FILES = ["api/users.ts", "api/orders.ts", "jobs/sync.ts", "api/cart.ts", "lib/search.ts"];
const TILT = [-2, 1.5, -1, 2, -1.5];
const ROWS = [2, 3, 4, 6, 8, 11, 15, 20]; // the wall after each cut of bar 2
const WORDS = ["Most", "AI", "reviewers", "repeat", "themselves."];
const SHOWN = [1, 2, 3, 3, 4, 4, 5, 5]; // headline words on screen after each of those cuts

/**
 * I. Noise. A faceless reviewer leaves the same comment on every PR: one piano note, repeated.
 * There is no orange in this world, and it moves on fives (12 fps) while the film runs at 60.
 */
export const Noise: React.FC = () => {
  const {shot, t} = useShots("noise");
  const step = Math.floor(t / 5) * 5;
  return shot < 5 ? <Stamp n={shot} t={step} /> : <Wall n={Math.min(shot - 5, 7)} t={step} silenced={shot === 13} />;
};

/** Bar 1: the same comment lands on five PRs in a row, each stamped on top of the last. */
const Stamp: React.FC<{n: number; t: number}> = ({n, t}) => (
  <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK}}>
    {Array.from({length: n + 1}, (_, k) => (
      <div
        key={k}
        style={{
          position: "absolute",
          left: 130 + [-34, 26, -12, 40, 0][k],
          top: 256 + k * 30,
          width: 1250,
          padding: "44px 60px 56px",
          borderRadius: 22,
          backgroundColor: "#101218",
          border: `2px solid ${GREY.dim}`,
          boxShadow: "0 -18px 50px rgba(0, 0, 0, 0.55)",
          color: k === n ? GREY.hi : GREY.low,
          rotate: `${TILT[k]}deg`,
          scale: String(k === n && t < 5 ? 1.07 : 1),
        }}
      >
        <div style={{display: "flex", alignItems: "center", gap: 20, fontSize: 36, fontWeight: 500, color: k === n ? GREY.mid : GREY.low}}>
          <div style={{width: 56, height: 56, borderRadius: 14, backgroundColor: GREY.low}} />
          ai-reviewer
          <span style={{fontSize: 24, border: `2px solid ${GREY.low}`, borderRadius: 100, padding: "2px 14px"}}>bot</span>
          <span style={{marginLeft: "auto", fontFamily: MONO}}>#{212 + k}</span>
        </div>
        <div style={{marginTop: 34, fontFamily: MONO, fontSize: 32, color: k === n ? GREY.mid : GREY.low}}>{FILES[k]}</div>
        <div style={{marginTop: 12, fontSize: 112, fontWeight: 700, letterSpacing: "-0.04em", lineHeight: 1.05, whiteSpace: "nowrap"}}>{COMMENT}</div>
      </div>
    ))}
    <div style={{position: "absolute", right: 130, top: 380, fontFamily: MONO, fontWeight: 700, fontSize: 290, lineHeight: 1, color: GREY.mid, scale: String(t < 5 ? 1.12 : 1), transformOrigin: "100% 50%"}}>×{n + 1}</div>
  </AbsoluteFill>
);

const Wall: React.FC<{n: number; t: number; silenced: boolean}> = ({n, t, silenced}) => {
  const rows = ROWS[n];
  const height = 1080 / rows;
  const size = height * 0.7;
  const repeats = Math.ceil(2800 / (13.5 * size)) + 1;
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, fontWeight: 700, justifyContent: "center", alignItems: "center"}}>
      {silenced
        ? null
        : Array.from({length: rows}, (_, i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                top: i * height,
                left: -420,
                height,
                lineHeight: `${height}px`,
                fontSize: size,
                letterSpacing: "-0.03em",
                whiteSpace: "pre",
                color: i % 2 ? GREY.dim : GREY.low,
                translate: `${(i % 2 ? 1 : -1) * (t * 4 + ((i * 37) % 200))}px 0`,
              }}
            >
              {Array.from({length: repeats}, (_, k) => `#${217 + n * 7 + i + k}  ${COMMENT}   `).join("")}
            </div>
          ))}
      <div style={{position: "relative", padding: "38px 64px 46px", backgroundColor: C.bg, fontSize: 132, letterSpacing: "-0.04em", lineHeight: 1.04, color: GREY.hi, textAlign: "center"}}>
        {WORDS.map((word, i) => (
          <span key={word}>
            <span style={{display: "inline-block", visibility: i < SHOWN[n] ? "visible" : "hidden", scale: String(!silenced && i === SHOWN[n] - 1 && SHOWN[n] !== SHOWN[n - 1] && t < 5 ? 1.1 : 1)}}>{word}</span>
            {i === 2 ? <br /> : " "}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};
