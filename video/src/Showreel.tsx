import {Audio} from "@remotion/media";
import type React from "react";
import {AbsoluteFill, Series, staticFile, useVideoConfig} from "remotion";
import {C, Grain, KeyStrip, section, useImpact} from "./kit";
import {Blitz} from "./scenes/Blitz";
import {Lockup} from "./scenes/Lockup";
import {NeverBack} from "./scenes/NeverBack";
import {Noise} from "./scenes/Noise";
import {TellItOnce} from "./scenes/TellItOnce";

export const length = (id: string) => section(id).to - section(id).from;

/** Five sections of two bars each, laid end to end with hard cuts: the lengths come from the score. */
export const Showreel: React.FC = () => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <Audio name="Score" src={staticFile("score.wav")} premountFor={fps} />
      <AbsoluteFill style={useImpact()}>
        <Series>
          <Series.Sequence name="I · Noise" durationInFrames={length("noise")} premountFor={fps}>
            <Noise />
          </Series.Sequence>
          <Series.Sequence name="II · Tell it once" durationInFrames={length("tell")} premountFor={fps}>
            <TellItOnce />
          </Series.Sequence>
          <Series.Sequence name="III · It never comes back" durationInFrames={length("never")} premountFor={fps}>
            <NeverBack />
          </Series.Sequence>
          <Series.Sequence name="IV · Blitz" durationInFrames={length("blitz")} premountFor={fps}>
            <Blitz />
          </Series.Sequence>
          <Series.Sequence name="V · Pairo" durationInFrames={length("pairo")} premountFor={fps}>
            <Lockup />
          </Series.Sequence>
        </Series>
      </AbsoluteFill>
      <KeyStrip />
      <Grain />
    </AbsoluteFill>
  );
};
