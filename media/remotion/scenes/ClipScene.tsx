// Scenes 3-5 — embed a recorded example clip (table / HSS / piston) at full
// resolution. The clips keep their native aspect; this scene contains them and
// pads the 16:9 frame with whitespace around the edges.

import React from "react";
import { AbsoluteFill, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";

export const ClipScene: React.FC<{
  src: string;
  eyebrow: string;
  title: string;
  startFrom?: number;
}> = ({ src, eyebrow, title, startFrom = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const header = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 24 });
  const clipIn = spring({ frame: frame - 8, fps, config: { damping: 200 }, durationInFrames: 26 });

  return (
    <AbsoluteFill style={{ background: COLORS.bg, fontFamily: FONTS.sans, padding: "70px 90px" }}>
      <div style={{ opacity: header, transform: `translateY(${(1 - header) * -20}px)` }}>
        <div style={{ fontSize: 26, color: COLORS.green, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>
          {eyebrow}
        </div>
        <div style={{ fontSize: 50, fontFamily: FONTS.heading, color: COLORS.greenDeep, fontWeight: 600, marginTop: 4 }}>{title}</div>
      </div>

      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", marginTop: 30 }}>
        <div
          style={{
            opacity: clipIn,
            transform: `scale(${0.97 + clipIn * 0.03})`,
            maxWidth: "100%",
            maxHeight: "100%",
            borderRadius: 20,
            overflow: "hidden",
            border: `1px solid ${COLORS.line}`,
            boxShadow: "0 30px 80px -40px rgba(28,33,27,0.5)",
            background: COLORS.bg,
          }}
        >
          <OffthreadVideo
            src={staticFile(src)}
            startFrom={startFrom}
            muted
            style={{ display: "block", maxHeight: "78vh", maxWidth: "100%", objectFit: "contain" }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
