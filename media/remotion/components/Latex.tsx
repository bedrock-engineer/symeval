// Renders a LaTeX string with KaTeX. KaTeX ships its own web fonts; we hold the
// Remotion render until they are ready so no frame captures fallback glyphs.

import { useEffect, useState } from "react";
import { continueRender, delayRender } from "remotion";
import katex from "katex";
import "katex/dist/katex.min.css";

export const Latex: React.FC<{ tex: string; displayMode?: boolean; color?: string }> = ({
  tex,
  displayMode = true,
  color,
}) => {
  const [handle] = useState(() => delayRender(`katex-fonts:${tex.slice(0, 24)}`));
  useEffect(() => {
    document.fonts.ready.then(() => continueRender(handle));
  }, [handle]);

  const html = katex.renderToString(tex, { displayMode, throwOnError: false });
  return <span style={{ color }} dangerouslySetInnerHTML={{ __html: html }} />;
};
