// Scene 2 — the Usain's-speed snippet types in line by line, then its rendered
// symbolic evaluation slides in beside it.

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CARD, COLORS, FONTS } from "../theme";
import { Code } from "../components/Code";
import { Latex } from "../components/Latex";

const SNIPPET = String.raw`usains_speed = sym_evalf(
    Equality(Symbol("v"), Symbol("d") / Symbol("t")),
    subs={
        Symbol("d"): Quantity(100, "m"),
        Symbol("t"): Quantity(9.58, "s"),
    },
    output_unit="km/h",
)`;

const RESULT = String.raw`\begin{aligned}
v &= \frac{d}{t} \\[6pt]
&= \frac{100\ \text{m}}{9.58\ \text{s}} \\[6pt]
v &= 10.44\ \frac{\text{m}}{\text{s}} = 37.58\ \frac{\text{km}}{\text{h}}
\end{aligned}`;

const LINES = SNIPPET.split("\n").length;
const REVEAL_START = 8;
const REVEAL_STEP = 9;

export const CodeToLatexScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const visibleLines = Math.floor((frame - REVEAL_START) / REVEAL_STEP) + 1;
  const resultDelay = REVEAL_START + LINES * REVEAL_STEP + 6;
  const resultIn = spring({ frame: frame - resultDelay, fps, config: { damping: 200 }, durationInFrames: 26 });

  return (
    <AbsoluteFill style={{ background: COLORS.bg, alignItems: "center", justifyContent: "center", fontFamily: FONTS.sans }}>
      <div style={{ display: "flex", alignItems: "center", gap: 48, padding: "0 80px", maxWidth: 1920 }}>
        <div style={{ flexShrink: 0 }}>
          <Code code={SNIPPET} fontSize={25} visibleLines={visibleLines} />
        </div>

        <div style={{ fontSize: 60, color: COLORS.green, opacity: interpolate(resultIn, [0, 1], [0, 0.8]) }}>→</div>

        <div
          style={{
            ...CARD,
            opacity: resultIn,
            transform: `translateX(${(1 - resultIn) * 40}px)`,
            padding: "44px 52px",
            fontSize: 42,
            color: COLORS.dark,
          }}
        >
          <Latex tex={RESULT} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
