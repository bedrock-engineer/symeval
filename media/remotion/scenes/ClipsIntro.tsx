// Interstitial before the example clips: "SymEval ♥ marimo". Only the heart is
// SymEval green; it gives a single beat as it appears.

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

export const ClipsIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 28 });

  // One beat, just after the text settles.
  const pump = interpolate(frame, [26, 33, 42], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const beat = 1 + 0.2 * pump;

  return (
    <AbsoluteFill style={{ background: COLORS.bg, alignItems: "center", justifyContent: "center", fontFamily: FONTS.heading }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 32,
          fontSize: 128,
          fontWeight: 700,
          color: COLORS.greenDeep,
          opacity: s,
          transform: `translateY(${(1 - s) * 30}px)`,
        }}
      >
        <span>SymEval</span>
        <span style={{ display: "inline-block", color: COLORS.green, transform: `scale(${beat})` }}>♥</span>
        <span>marimo</span>
      </div>
    </AbsoluteFill>
  );
};
