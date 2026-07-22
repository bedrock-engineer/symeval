// The SymEval promo: five scenes cross-faded end to end. Silent, and the last
// scene fades back toward the first so the file loops cleanly.

import React from "react";
import { AbsoluteFill } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { COLORS } from "./theme";
import { TitleScene } from "./scenes/TitleScene";
import { CodeToLatexScene } from "./scenes/CodeToLatexScene";
import { ClipScene } from "./scenes/ClipScene";

const XFADE = 18; // cross-fade length between scenes

const SCENES = [
  { dur: 165, node: <TitleScene /> },
  { dur: 210, node: <CodeToLatexScene /> },
  { dur: 150, node: <ClipScene src="table.mp4" eyebrow="DataFrame column" title="Select a row, the evaluation recomputes" startFrom={24} /> },
  { dur: 150, node: <ClipScene src="hss.mp4" eyebrow="Chained checks" title="Sweep a length, it ripples through the check" startFrom={45} /> },
  { dur: 150, node: <ClipScene src="piston.mp4" eyebrow="Explorable" title="Drive the inputs, watch the physics" startFrom={30} /> },
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
