import type React from "react";
import {Img, staticFile} from "remotion";

/**
 * The Pairo mascot, rigged. The body is the original logo artwork (public/mascot.png, cut out
 * by score/mascot.py); only the eyes are redrawn on top so they can look around and blink, and
 * the antenna is the same image clipped at the stem so it can swing. Coordinates are in the
 * logo's own 1254 px grid.
 */
const ART = 1254;
const HEAD = "#fc7c18"; // flat all around the eyes, so a disc of it hides the painted ones
const EYES = [
  {x: 430.5, pupil: 4, shine: 1},
  {x: 821.5, pupil: -4.5, shine: -1},
] as const;
const ANTENNA = "polygon(0 0, 100% 0, 100% 26.87%, 52.1% 26.87%, 52.1% 28.2%, 47.8% 28.2%, 47.8% 26.87%, 0 26.87%)";
const fill: React.CSSProperties = {position: "absolute", inset: 0, width: "100%", height: "100%"};

type Props = {
  readonly size: number;
  /** Where the eyes point, each axis -1..1. */
  readonly look?: readonly [number, number];
  /** 0 open, 1 shut. */
  readonly blink?: number;
  /** Antenna swing in degrees. */
  readonly antenna?: number;
  /** Antenna light, 0..1. */
  readonly glow?: number;
  /** Squash (positive) and stretch (negative), about the chin. */
  readonly squash?: number;
  readonly style?: React.CSSProperties;
};

export const Mascot: React.FC<Props> = ({size, look = [0, 0], blink = 0, antenna = 0, glow = 0, squash = 0, style}) => {
  const src = staticFile("mascot.png");
  return (
    <div style={{position: "relative", width: size, height: size, flexShrink: 0, transformOrigin: "50% 84.4%", scale: `${1 + squash * 0.6} ${1 - squash}`, ...style}}>
      <div style={{...fill, transformOrigin: "49.95% 27.1%", rotate: `${antenna}deg`}}>
        <Img src={src} style={{...fill, clipPath: ANTENNA}} />
        <svg viewBox={`0 0 ${ART} ${ART}`} style={{...fill, overflow: "visible"}}>
          <defs>
            <radialGradient id="mascot-halo">
              <stop offset="0" stopColor="#ffd9a0" stopOpacity="0.95" />
              <stop offset="0.35" stopColor="#ff9a4a" stopOpacity="0.5" />
              <stop offset="1" stopColor="#ff7a32" stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle cx={626.5} cy={194.5} r={90 + 200 * glow} fill="url(#mascot-halo)" opacity={Math.min(1, glow * 1.4)} />
        </svg>
      </div>
      <Img src={src} style={{...fill, clipPath: "inset(26.87% 0 0 0)"}} />
      <svg viewBox={`0 0 ${ART} ${ART}`} style={fill}>
        <defs>
          <clipPath id="mascot-eye">
            <circle r={116.5} />
          </clipPath>
        </defs>
        {EYES.map((eye) => (
          <g key={eye.x} transform={`translate(${eye.x} 725.5)`}>
            <circle r={121} fill={HEAD} />
            <g transform={`scale(1 ${1 - 0.93 * blink})`} clipPath="url(#mascot-eye)">
              <circle r={116.5} fill="#fde6b8" />
              <circle cx={eye.pupil + look[0] * 20} cy={1.5 + look[1] * 20} r={92} fill="#311a0c" />
              <circle cx={eye.shine * 33 + look[0] * 13} cy={-38 + look[1] * 13} r={25.5} fill="#fdf8f0" />
              <circle cx={eye.shine * 18.5 + look[0] * 13} cy={12 + look[1] * 13} r={5.5} fill="#fdf8f0" />
            </g>
          </g>
        ))}
      </svg>
    </div>
  );
};
