// Scene 1 — logo + SymEval wordmark, tagline, and the three-step idea:
// Formula -> Substituted values + units -> Result. The steps mirror sym_evalf.

import React from "react";
import { AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CARD, COLORS, FONTS } from "../theme";
import { Latex } from "../components/Latex";
// Single source of truth: the canonical docs logo, served from docs/public
// (Remotion's publicDir, set in remotion.config.ts).

const STEPS = [
  { n: 1, label: "Formula", tex: String.raw`\sigma = \dfrac{F}{A}` },
  { n: 2, label: "Substituted values + units", tex: String.raw`= \dfrac{-680\ \text{kN}}{10580\ \text{mm}^2}` },
  { n: 3, label: "Result", tex: String.raw`= -64.3\ \text{MPa}` },
];

const Appear: React.FC<{ delay: number; children: React.ReactNode; y?: number }> = ({ delay, children, y = 40 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: 34 });
  return <div style={{ opacity: s, transform: `translateY(${(1 - s) * y}px)` }}>{children}</div>;
};

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const logoScale = spring({ frame, fps: 30, config: { damping: 200 }, durationInFrames: 42 });

  return (
    <AbsoluteFill style={{ background: COLORS.bg, alignItems: "center", justifyContent: "center", fontFamily: FONTS.sans }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 34 }}>
        {/* Logo mark + SymEval wordmark, as one compact lockup. */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 26,
            opacity: logoScale,
            transform: `scale(${interpolate(logoScale, [0, 1], [0.92, 1])})`,
          }}
        >
          <img src={staticFile("symeval-logo.svg")} alt="" style={{ height: 164 }} />
          <div style={{ fontFamily: FONTS.heading, fontSize: 120, fontWeight: 700, color: COLORS.greenDeep, letterSpacing: -1 }}>
            SymEval
          </div>
        </div>

        <Appear delay={26}>
          <div style={{ fontSize: 58, color: COLORS.gray, fontWeight: 500, textAlign: "center" }}>
            Symbolic, unit-aware evaluation of SymPy equations
          </div>
        </Appear>

        <div style={{ display: "flex", alignItems: "stretch", gap: 30, marginTop: 34 }}>
          {STEPS.map((step, i) => (
            <React.Fragment key={step.n}>
              {i > 0 && (
                <Appear delay={52 + i * 34} y={0}>
                  <div style={{ display: "flex", alignItems: "center", height: "100%", fontSize: 60, color: COLORS.green, opacity: 0.7 }}>→</div>
                </Appear>
              )}
              <Appear delay={46 + i * 34}>
                <div
                  style={{
                    ...CARD,
                    padding: "30px 46px",
                    height: 330, // equal height; width follows content
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 14, height: 52 }}>
                    <div
                      style={{
                        width: 48,
                        height: 48,
                        flexShrink: 0,
                        borderRadius: 999,
                        background: COLORS.green,
                        color: "#fff",
                        fontSize: 28,
                        fontWeight: 700,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {step.n}
                    </div>
                    <div style={{ fontSize: 28, color: COLORS.greenDark, fontWeight: 600, lineHeight: 1.1 }}>{step.label}</div>
                  </div>
                  {/* Equations vertically centred in the shared remaining space, so the
                      "=" signs land at the same height across all three cards. */}
                  <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 54, color: COLORS.dark }}>
                    <Latex tex={step.tex} />
                  </div>
                </div>
              </Appear>
            </React.Fragment>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
