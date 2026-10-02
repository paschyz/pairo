import type React from "react";
import {AbsoluteFill} from "remotion";
import {BACK, BEAT, Backdrop, C, GROTESK, MONO, Rise, TL, blinkAt, section, sfx, swing, tween, useShots} from "../kit";
import {Mascot} from "../Mascot";

const NAME = "PAIRO";

/** V. The name, one letter per chord, then home. The top voice of those five chords is B A B D A. */
export const Lockup: React.FC = () => {
  const {shot, t} = useShots("pairo");
  return shot < NAME.length ? <Letter n={shot} t={t} /> : <Home t={t} />;
};

const Letter: React.FC<{n: number; t: number}> = ({n, t}) => {
  const lit = n % 2 === 1;
  const ink = lit ? C.ink : C.text;
  return (
    <AbsoluteFill style={{backgroundColor: lit ? C.orange : C.bg, alignItems: "center", fontFamily: GROTESK}}>
      <div style={{fontWeight: 700, fontSize: 860, lineHeight: 1, marginTop: -6, color: lit ? C.ink : n === 2 ? C.text : C.orange, scale: String(tween(t, [0, 12], [1.26, 1])), rotate: `${tween(t, [0, 12], [n % 2 ? 4 : -4, 0])}deg`}}>
        {NAME[n]}
      </div>
      {/* the cipher, spelled out as it is played: each letter of the name and the note it becomes */}
      <div style={{position: "absolute", bottom: 96, display: "flex", gap: 64, fontFamily: MONO, textAlign: "center"}}>
        {[...NAME].map((letter, i) => (
          <div key={i} style={{width: 70, opacity: i <= n ? 1 : 0.18, scale: String(i === n ? tween(t, [0, 9], [1.6, 1], BACK) : 1)}}>
            <div style={{fontWeight: 700, fontSize: 54, lineHeight: 1.1, color: ink}}>{letter}</div>
            <div style={{fontSize: 44, lineHeight: 1.2, color: lit ? C.ink : C.orange, visibility: i <= n ? "visible" : "hidden"}}>{TL.motif[i]}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Home: React.FC<{t: number}> = ({t}) => {
  const {from} = section("pairo");
  const ping = sfx("ping")[0] - from - NAME.length * BEAT;
  const echoes = [0, 1, 2, 3].map((k) => ping + k * 0.75 * BEAT); // the score echoes the ping in dotted eighths
  const light = echoes.reduce((v, f, k) => (t >= f ? Math.max(v, Math.exp(-(t - f) / 7) * 0.5 ** k) : v), 0);
  const arrive = Math.exp(-t / 14);
  const orbit = t * 0.045 + 2.4;
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: GROTESK, color: C.text}}>
      <Backdrop x={50} y={44} glow={0.15 + 0.2 * arrive + 0.08 * light} />
      <div style={{position: "absolute", left: 0, right: 0, top: 232, display: "flex", justifyContent: "center", alignItems: "center", gap: 44}}>
        <div style={{position: "relative", translate: `0 ${Math.sin(t / 22) * 6}px`}}>
          <div style={{position: "absolute", left: -76, top: 150, width: 500, height: 170, borderRadius: "50%", border: "2px solid rgba(255, 255, 255, 0.07)", opacity: tween(t, [10, 30], [0, 1])}}>
            <div style={{position: "absolute", left: 250 + 250 * Math.cos(orbit) - 7, top: 85 + 85 * Math.sin(orbit) - 7, width: 14, height: 14, borderRadius: "50%", backgroundColor: C.orange, boxShadow: "0 0 18px rgba(255, 122, 50, 0.9)"}} />
          </div>
          {echoes.map((f, k) => (
            <div key={k} style={{position: "absolute", left: 174, top: 54, width: 0, height: 0, opacity: t >= f ? (1 - tween(t, [f, f + 26], [0, 1])) * 0.8 * 0.6 ** k : 0}}>
              <div style={{position: "absolute", borderRadius: "50%", border: `3px solid ${C.orange}`, width: 2 * tween(t, [f, f + 26], [20, 150]), height: 2 * tween(t, [f, f + 26], [20, 150]), translate: "-50% -50%"}} />
            </div>
          ))}
          <Mascot
            size={348}
            look={[tween(t, [16, 40], [0.9, 0]), 0]}
            blink={Math.max(blinkAt(t, ping), blinkAt(t, ping + 2.6 * BEAT))}
            antenna={swing(t, [0], 22, 12) + swing(t, [ping], 12, 12)}
            glow={Math.max(light, 0.8 * Math.exp(-t / 6))}
            squash={0.16 * Math.exp(-t / 6) * Math.cos(t * 0.55)}
            style={{scale: String(tween(t, [0, 13], [0.62, 1], BACK)), filter: "drop-shadow(0 24px 60px rgba(255, 122, 50, 0.32))"}}
          />
        </div>
        <div style={{fontSize: 290, fontWeight: 700, letterSpacing: "-0.05em", lineHeight: 1.1}}>
          <Rise t={t}>Pairo</Rise>
        </div>
      </div>
      <div style={{position: "absolute", left: 0, right: 0, top: 676, textAlign: "center", fontSize: 84, fontWeight: 700, letterSpacing: "-0.04em", opacity: tween(t, [14, 30], [0, 1]), translate: `0 ${tween(t, [14, 34], [30, 0])}px`}}>
        AI code reviews <span style={{backgroundImage: C.gradient, backgroundClip: "text", WebkitBackgroundClip: "text", color: "transparent"}}>that actually help</span>
      </div>
      <div style={{position: "absolute", left: 0, right: 0, top: 846, textAlign: "center", fontFamily: MONO, fontSize: 42, color: C.sub, opacity: tween(t, [30, 46], [0, 1])}}>github.com/paschyz/pairo</div>
    </AbsoluteFill>
  );
};
