# media — example clips + promo video

Two pipelines that produce the visual assets in `../docs/public/`:

- **`recorders/`** — record the live marimo widgets from `getting_started.py` into
  short example clips (`table`, `hss`, `piston`), each in several formats.
- **`remotion/`** — the [Remotion](https://remotion.dev) promo (`symeval-promo.mp4`),
  which embeds those clips.

No browser install beyond Playwright's own Chromium, and no system ffmpeg — the
recorders drive the real widgets, node-canvas composites the frames, and the
encoders (`gifenc` + the bundled `ffmpeg-static`) write the files.

```sh
npm install                       # first time only
npx playwright install chromium   # first time only (recorders)
```

## Example clips (`recorders/`)

1. Serve the tutorial notebook as a live marimo app (its PEP 723 header pulls
   `symeval` from PyPI):

   ```sh
   uvx marimo run --sandbox ../examples/getting_started.py --headless -p 2821 --no-token
   ```

2. Record — each writes `../docs/public/<name>.{gif,mp4,webp}`:

   ```sh
   npm run piston   # ideal-gas explorable (canvas iframe)
   npm run hss      # beam-length sweep, chained equations
   npm run table    # marimo.ui.table row selection
   ```

   `MODE=test node recorders/<script>` runs a short version and dumps sample
   frames to `tmp/` for inspection. Set `APP_URL` to target a different port.

Each recorder drives the real widgets, composites the frames with node-canvas,
and hands one frame array to the shared encoder (`recorders/lib/`: `app.mjs`
launches Chromium, `encode.mjs` owns the encode). `record-piston.mjs` glides the
sliders and holds while the piston's requestAnimationFrame animates;
`record-hss.mjs` and `record-table.mjs` step discrete states with long per-frame
holds so viewers can read each one.

### Output formats

`encode.mjs` writes each clip in up to three formats from one frame array:

| Format | Resolution | Use | Notes |
| --- | --- | --- | --- |
| `.gif`  | downscaled | universal `<img>` fallback | palettized (gifenc), keeps per-frame delays |
| `.mp4`  | full capture | docs `<video>`, the promo, social | H.264; best for dense motion (the piston) |
| `.webp` | full capture | README (sharper + smaller than GIF) | animated; the *discrete-state* clips only |

The video formats come from ffmpeg's concat demuxer (one still per unique frame,
held for its delay), so a static hold stays one encoded frame rather than
ballooning to a constant-fps run. The **piston skips `.webp`**: its ~200 distinct
animation frames make animated webp ~8x larger than the mp4, so it emits gif + mp4.

## Promo video (`remotion/`)

```sh
npm run studio   # open the Remotion editor
npm run promo    # render ../docs/public/symeval-promo.mp4 (silent, 1920x1080, ~25s)
```

Five cross-faded scenes: title + the Formula→Substituted→Result idea, the
axial-stress snippet resolving to its rendered LaTeX, then the table / HSS /
piston clips embedded via `staticFile` (`publicDir` is `../docs/public`, set in
`remotion.config.ts`). Colours and IBM Plex fonts (via `@remotion/google-fonts`)
match the docs brand; see `remotion/theme.ts`.

## Notes

- The logo lives once at `../docs/public/symeval-logo.svg` — the docs navbar and
  the promo both reference that single file.
- The 💥 out-of-bounds indicator needs an emoji font. If it renders as an empty
  box, install one into the user font dir (no root):
  `~/.local/share/fonts/NotoColorEmoji.ttf`, then `fc-cache -f`.
- `node_modules/` and `tmp/` are gitignored; the generated clips and promo under
  `docs/public/` are committed.
