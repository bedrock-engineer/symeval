# media — README GIF generation

Records the live marimo widgets from `getting_started.py` into animated GIFs for
the project README. No browser install beyond Playwright's own Chromium, and no
ffmpeg: Playwright drives the real widgets, node-canvas composites the frames,
and gifenc encodes the GIF.

## Regenerate the piston GIF

1. Serve the tutorial notebook as a live marimo app (its PEP 723 header pulls
   `symeval` from PyPI):

   ```sh
   uvx marimo run --sandbox ../examples/getting_started.py --headless -p 2821 --no-token
   ```

2. Record (writes `../docs/public/piston.gif`):

   ```sh
   npm install          # first time only
   npx playwright install chromium   # first time only
   node src/record.mjs
   ```

   `MODE=test node src/record.mjs` runs a short version and dumps sample frames
   to `tmp/` for inspection. Set `APP_URL` to target a different port.

## Notes

- The 💥 out-of-bounds indicator needs an emoji font. If it renders as an empty
  box, install one into the user font dir (no root):
  `~/.local/share/fonts/NotoColorEmoji.ttf`, then `fc-cache -f`.
- `node_modules/` and `tmp/` are gitignored; the generated GIFs under
  `docs/public/` are committed.
