// Scenes for the recorded example clips (table / HSS / piston). Each keeps its
// native aspect and fills the full available height; the 16:9 frame is padded
// with whitespace at the sides. No frame around the clip — just a soft shadow.

import React from "react";
import { AbsoluteFill, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

// One title size across all clip scenes (sized so "Chained checks" fits nicely
// above the full-height HSS clip).
const TITLE_SIZE = 72;

export const ClipScene: React.FC<{
  src: string;
  title: string;
  startFrom?: number;
  shiftX?: number; // nudge the clip right (+) / left (-)
  shiftY?: number; // nudge the clip up (-) / down (+)
  scale?: number; // enlarge the clip; anchored top-left, so it grows toward bottom-right
}> = ({ src, title, startFrom = 0, shiftX = 0, shiftY = 0, scale = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Title and clip enter together.
  const enter = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 26 });

  return (
    <AbsoluteFill style={{ background: COLORS.bg, fontFamily: FONTS.sans, padding: "18px 48px 20px" }}>
      <div
        style={{
          fontSize: TITLE_SIZE,
          fontFamily: FONTS.heading,
          color: COLORS.greenDeep,
          fontWeight: 600,
          lineHeight: 1.05,
          paddingLeft: 32,
          opacity: enter,
          transform: `translateY(${(1 - enter) * -20}px)`,
        }}
      >
        {title}
      </div>

      <div style={{ flex: 1, minHeight: 0, display: "flex", alignItems: "center", justifyContent: "center", marginTop: 8 }}>
        <OffthreadVideo
          src={staticFile(src)}
          startFrom={startFrom}
          muted
          style={{
            display: "block",
            maxHeight: "100%",
            maxWidth: "100%",
            objectFit: "contain",
            opacity: enter,
            transformOrigin: "top left", // scale grows toward the bottom-right
            transform: `translate(${shiftX}px, ${shiftY}px) scale(${scale * (0.97 + enter * 0.03)})`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
