import type React from "react";
import {Composition, Folder} from "remotion";
import {TL} from "./kit";
import {Blitz} from "./scenes/Blitz";
import {Lockup} from "./scenes/Lockup";
import {NeverBack} from "./scenes/NeverBack";
import {Noise} from "./scenes/Noise";
import {TellItOnce} from "./scenes/TellItOnce";
import {Showreel, length} from "./Showreel";

/** Frame rate and durations come from the score (src/timeline.json), not from literals here. */
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="PairoShowreel" component={Showreel} durationInFrames={TL.durationInFrames} fps={TL.fps} width={1920} height={1080} />
    <Folder name="Scenes">
      <Composition id="Noise" component={Noise} durationInFrames={length("noise")} fps={TL.fps} width={1920} height={1080} />
      <Composition id="TellItOnce" component={TellItOnce} durationInFrames={length("tell")} fps={TL.fps} width={1920} height={1080} />
      <Composition id="NeverBack" component={NeverBack} durationInFrames={length("never")} fps={TL.fps} width={1920} height={1080} />
      <Composition id="Blitz" component={Blitz} durationInFrames={length("blitz")} fps={TL.fps} width={1920} height={1080} />
      <Composition id="Lockup" component={Lockup} durationInFrames={length("pairo")} fps={TL.fps} width={1920} height={1080} />
    </Folder>
  </>
);
