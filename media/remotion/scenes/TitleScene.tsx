// Scene 1 — logo, tagline, and the three-step idea: Formula -> Substituted
// values + units -> Result. The steps mirror what sym_evalf renders.

import React from "react";
import { AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../theme";
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
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: 25 });
  return <div style={{ opacity: s, transform: `translateY(${(1 - s) * y}px)` }}>{children}</div>;
};

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const logoScale = spring({ frame, fps: 30, config: { damping: 200 }, durationInFrames: 30 });

  return (
    <AbsoluteFill style={{ background: COLORS.bg, alignItems: "center", justifyContent: "center", fontFamily: FONTS.sans }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 44 }}>
        <img
          src={staticFile("symeval-logo.svg")}
          alt="SymEval"
          style={{ width: 560, opacity: logoScale, transform: `scale(${interpolate(logoScale, [0, 1], [0.9, 1])})` }}
        />
        <Appear delay={16}>
          <div style={{ fontSize: 40, color: COLORS.gray, fontWeight: 500, letterSpacing: 0.2 }}>
            Symbolic, unit-aware evaluation of SymPy equations
          </div>
        </Appear>

        <div style={{ display: "flex", alignItems: "center", gap: 28, marginTop: 26 }}>
          {STEPS.map((step, i) => (
            <React.Fragment key={step.n}>
              {i > 0 && (
                <Appear delay={34 + i * 22} y={0}>
                  <div style={{ fontSize: 54, color: COLORS.green, opacity: 0.7 }}>→</div>
                </Appear>
              )}
              <Appear delay={30 + i * 22}>
                <div
                  style={{
                    background: COLORS.greenSoft,
                    border: `1px solid ${COLORS.line}`,
                    borderRadius: 20,
                    padding: "26px 34px",
                    minWidth: 300,
                    minHeight: 210,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "space-between",
                    boxShadow: "0 20px 50px -30px rgba(28,33,27,0.4)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 999,
                        background: COLORS.green,
                        color: "#fff",
                        fontSize: 24,
                        fontWeight: 700,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {step.n}
                    </div>
                    <div style={{ fontSize: 24, color: COLORS.greenDark, fontWeight: 600 }}>{step.label}</div>
                  </div>
                  <div style={{ fontSize: 40, color: COLORS.dark }}>
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
