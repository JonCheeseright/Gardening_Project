# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack decisions (locked — do not re-litigate without asking)

- **Language/style**: Python, PEP 8, light-to-medium comment density (comment *why*, not *what*). Favor simple, direct code over premature abstraction — this is a single-user desktop app, not a library.
- **Rendering/framework**: `pygame`. Architecture is a standard game loop (event pump → update → draw → flip) with a simple scene/state-machine (Menu → Garden Creation → Garden View, etc.).
- **Fonts**: DotGothic16 (Google Fonts, OFL-licensed) — bundle the `.ttf` under `assets/fonts/`. Headers render at weight 600 (semibold), body text at weight 400 (regular). If only one static weight file is available upstream, source both weights explicitly rather than faking bold with pygame's synthetic bold.
- **UI chrome**: menu options are oval buttons with pixel-stepped (aliased) borders matching the font's pixelation level — not smooth anti-aliased ovals.
- **Sprite generation**: plants get 4 candidate sprites from a **procedural pixel-art generator** (Python code, not an image-gen API/model call) — parameters (species, expected height/diameter, a palette/silhouette seed) drive shape and color variation. Claude cannot generate images directly; do not attempt to call out to an image model for this.
- **Garden/bed drawing**: preset primitive shapes (rectangle, circle, quarter-circle/arc, polygon) placed first, then vertices/radius are draggable for freehand refinement. This keeps "critical dimension" extraction (length/width, radius of curvature) tractable — it's a lookup per shape type, not general curve-fitting.
- **Persistence**: JSON files, no database.
  - `plants_library.json` — shared plant *definitions* (id, species, expected height, expected diameter, sprite data), reusable across gardens.
  - `gardens/<garden_name>.json` — garden outline, flowerbed outlines, and *plantings* (references to a plant id + instance state: position, current height/diameter, health, last-watered timestamp). Instance state lives on the planting, never on the shared plant definition.

## Plant data model

Each plant **definition** (shared, in the library): id, species, expected mature height, expected mature diameter, sprite (4 generated candidates + selected one).

Each **planting** (garden-specific instance): plant id reference, position in bed, current height, current diameter, health (enum: *too well / healthy / struggling / dead* — user-selected, not auto-computed), time since last watered, expected watering requirement (placeholder/deferred — do not implement the calculation yet, stub it).

## Consult-before-building list

Do not silently invent logic for these — stop and present a short set of concrete options, as previously requested:

1. **Critical-dimension extraction per shape type** — what exactly gets shown for each primitive (e.g. rectangle → length+width; circle → radius; quarter-circle → radius + orientation; polygon → ?), and how it's computed/displayed on screen.
2. **Area calculation** for each shape type, including irregular/adjusted polygons after freehand vertex dragging.
3. **Overlap detection math** — plants are compared by current diameter (circle-circle overlap) for the immediate-conflict warning, and by expected mature diameter for the >30% future-overlap warning. Confirm the overlap-percentage formula (e.g. relative to smaller circle's area vs. union) before implementing.
4. **Procedural sprite generation parameters** — how species/height/diameter map to visual variation (palette, silhouette, animation style) across the 4 candidates.
5. **Watering requirement calculation** — explicitly deferred; do not build this now, just leave a stub field.

## Commands

- `pip install -r requirements.txt` — install dependencies (currently just `pygame`)
- `python main.py` — run the application

No linter or test suite is configured yet.

## Project layout

- `main.py` — entry point; owns the pygame init/event/update/draw loop.
- `assets/fonts/` — bundled font files (DotGothic16 weights go here).
- `requirements.txt` — Python dependencies.

This is a fresh scaffold — scenes (Menu, Garden Creation, Garden View), the plant library/garden JSON persistence, and the procedural sprite generator described above do not exist yet.
