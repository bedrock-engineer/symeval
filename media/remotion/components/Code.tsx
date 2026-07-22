// Minimal Python syntax highlighter for the promo's code scene. A tiny scanner
// (strings, numbers, comments, identifiers, punctuation) is plenty for one fixed
// snippet and keeps the render fully offline — no shiki/highlighter dependency.

import React from "react";
import { COLORS, FONTS } from "../theme";

const KEYWORDS = new Set(["import", "from", "as", "def", "return", "for", "in", "if", "else", "None", "True", "False"]);
const CALLABLES = new Set(["sym_evalf", "Equality", "Symbol", "Quantity"]);

const TOKEN = /(#[^\n]*)|(r?"(?:[^"\\]|\\.)*"|r?'(?:[^'\\]|\\.)*')|(\b\d[\d_]*(?:\.\d+)?\b)|([A-Za-z_]\w*)|(\s+)|([^\s\w])/g;

function color(type: "comment" | "string" | "number" | "name-kw" | "name-call" | "name" | "punct"): string {
  switch (type) {
    case "comment": return COLORS.gray;
    case "string": return COLORS.greenDark;
    case "number": return COLORS.brown;
    case "name-kw": return COLORS.brown;
    case "name-call": return COLORS.green;
    case "punct": return "#9aa39a";
    default: return COLORS.dark;
  }
}

function highlight(line: string, key: number): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  let m: RegExpExecArray | null;
  TOKEN.lastIndex = 0;
  let i = 0;
  const rest = line;
  while ((m = TOKEN.exec(rest)) !== null) {
    const [tok, comment, str, num, name, ws] = m;
    let c: string;
    if (comment) c = color("comment");
    else if (str) c = color("string");
    else if (num) c = color("number");
    else if (ws) { out.push(<span key={`${key}-${i++}`}>{tok}</span>); continue; }
    else if (name) {
      // Colour a call by peeking for the next '(' after the identifier.
      const after = rest.slice(m.index + tok.length).match(/^\s*\(/);
      c = KEYWORDS.has(name) ? color("name-kw") : CALLABLES.has(name) && after ? color("name-call") : color("name");
    } else c = color("punct");
    out.push(<span key={`${key}-${i++}`} style={{ color: c }}>{tok}</span>);
  }
  return out;
}

export const Code: React.FC<{ code: string; fontSize?: number; visibleLines?: number }> = ({
  code,
  fontSize = 34,
  visibleLines = Infinity,
}) => {
  const lines = code.replace(/\n$/, "").split("\n");
  return (
    <pre
      style={{
        margin: 0,
        fontFamily: FONTS.mono,
        fontSize,
        lineHeight: 1.5,
        color: COLORS.dark,
        background: COLORS.greenSoft,
        border: `1px solid ${COLORS.line}`,
        borderRadius: 18,
        padding: "36px 44px",
        boxShadow: "0 24px 60px -30px rgba(28,33,27,0.35)",
      }}
    >
      {lines.map((line, idx) => (
        <div
          key={idx}
          style={{
            opacity: idx < visibleLines ? 1 : 0,
            transition: "opacity 0.2s",
            minHeight: fontSize * 1.5,
            whiteSpace: "pre",
          }}
        >
          {highlight(line, idx)}
        </div>
      ))}
    </pre>
  );
};
