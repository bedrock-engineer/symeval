// The SymEval promo: five scenes cross-faded end to end. Silent, and the last
// scene fades back toward the first so the file loops cleanly.

import React from "react";
import { AbsoluteFill } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { COLORS } from "./theme";
import { TitleScene } from "./scenes/TitleScene";
import { CodeToLatexScene } from "./scenes/CodeToLatexScene";
import { ClipsIntro } from "./scenes/ClipsIntro";
import { ClipScene } from "./scenes/ClipScene";

const XFADE = 18; // cross-fade length between scenes

const SCENES = [
  { dur: 215, node: <TitleScene /> },
  { dur: 210, node: <CodeToLatexScene /> },
  { dur: 80, node: <ClipsIntro /> },
  { dur: 130, node: <ClipScene src="table.mp4" title="DataFrame-ready" startFrom={29} /> },
  { dur: 150, node: <ClipScene src="hss.mp4" title="Chained checks" startFrom={45} shiftX={70} shiftY={-35} scale={1.16} /> },
  { dur: 300, node: <ClipScene src="piston.mp4" title="Explorable explanations" startFrom={30} /> },
];

/** Composition length = Σ scene durations − Σ cross-fade overlaps. */
export const PROMO_DURATION = SCENES.reduce((a, s) => a + s.dur, 0) - XFADE * (SCENES.length - 1);

export const Promo: React.FC = () => (
  <AbsoluteFill style={{ background: COLORS.bg }}>
    <TransitionSeries>
      {SCENES.map((scene, i) => (
        <React.Fragment key={i}>
          {i > 0 && <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: XFADE })} />}
          <TransitionSeries.Sequence durationInFrames={scene.dur}>{scene.node}</TransitionSeries.Sequence>
        </React.Fragment>
      ))}
    </TransitionSeries>
  </AbsoluteFill>
);
