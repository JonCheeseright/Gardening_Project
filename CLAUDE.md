# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack decisions (locked — do not re-litigate without asking)

- **Language/style**: Python, PEP 8, light-to-medium comment density (comment *why*, not *what*). Favor simple, direct code over premature abstraction — this is a single-user desktop app, not a library.
- **Rendering/framework**: `pygame`. Architecture is a standard game loop (event pump → update → draw → flip) with a simple scene/state-machine (Menu → Garden Creation → Garden View, etc.).
- **Fonts**: pygame's own bundled default font (`pygame.font.get_default_font()`) — no external font files, no downloads. Headers use pygame's built-in synthetic bold flag; body text is regular weight. Retro pixelation of the font itself is deferred visual polish, not implemented yet.
- **UI chrome**: menu options are oval buttons. Pixel-stepped borders matching a font's pixelation level are deferred until the font/visual-style pass happens.
- **Sprite generation**: plants get 4 candidate sprites from a **procedural pixel-art generator** (Python code, not an image-gen API/model call) — parameters (expected height/diameter, a silhouette archetype, and a color palette) drive shape and color variation. The silhouette archetype is chosen from a fixed set of 10 — *tree, bush, variant tree, variant bush, and 4 distinct flower types, fern, sapling* — plus a color palette, both selected by an **Anthropic API classification call** keyed on species (see `species_classifier.py`) rather than randomly, so sprites are species-appropriate; the result is cached on the plant definition. Requires `ANTHROPIC_API_KEY` in the environment — if absent or the call fails, fall back to a neutral default archetype/palette with a visible warning so the app still works offline. Claude cannot generate images directly; do not attempt to call out to an image-gen model for this — only text classification feeding the local procedural generator.
- **Garden/bed outline drawing** (`garden_outline_tool.py`, `GardenOutlineTool`): the same tool and interaction model is used for both the garden outline and every flowerbed outline — there's no primitive picker. The outline always starts as a rectangle inscribed in the drawing canvas and is edited as an n-sided polygon directly:
  - Left-click on an edge inserts a new vertex there, splitting that edge in two.
  - Left-click (without dragging) an existing vertex removes it, as long as at least 3 vertices remain.
  - Dragging a vertex moves it.
  - Every edit (drag, edge-insert, vertex-remove, zoom) is only committed if the resulting polygon stays fully inside its **container** and doesn't **overlap** any obstacle polygon (see below) — otherwise it's silently discarded, so an outline can never escape its container or overlap another outline. Dragging a vertex toward a forbidden region doesn't just freeze: each motion event bisects between the vertex's last valid position and the mouse target to find the furthest point along that path that's still valid, so the vertex slides right up to the boundary and keeps tracking the mouse in any direction that's still allowed (e.g. sliding along a garden edge or around another bed) instead of getting stuck.
  - The outline's true geometry is stored in meters, anchored to a fixed screen point set once at creation (the container's canvas center for the garden, or the auto-fitted bed's own center for a bed — see below); screen positions are that geometry multiplied by `pixels_per_meter`. Round grey "+"/"-" buttons change `pixels_per_meter` — "+" grows the real-world area represented (outline appears smaller on screen), "-" shrinks it (outline appears larger on screen) — so it's a camera zoom, not a resize: the outline's real-world size and area stay exactly constant. Both buttons re-center the outline's bounding box on its anchor afterwards. Shrinking ("-") is refused, and the button flashes red 3 times, if it would push the on-screen outline outside its container.
  - **Container/obstacles** (`app/geometry.py` has the point/segment math): the garden outline's container is just the drawing canvas rect (no obstacles — gardens can't overlap anything). A flowerbed's container is its garden's confirmed outline polygon, and its obstacles are every other already-confirmed bed in that garden — so beds must stay fully inside the garden and can never overlap each other.
  - A new bed's initial rectangle is auto-fitted smaller than the garden, into the largest available free space: `_find_default_rect` tries a grid of candidate centers/sizes (largest first) inside the garden's bounding box and picks the first that fits without overlapping existing beds.
  - Each outline (garden or bed) has its own independent `pixels_per_meter` scale, set when it's drawn. Dimension and area labels are shown in meters / square meters.
- **Persistence**: JSON files, no database.
  - `plants_library.json` — shared plant *definitions* (id, species, expected height, expected diameter, sprite data), reusable across gardens.
  - `gardens/<garden_name>.json` — garden outline (plus its `outline_pixels_per_meter` scale), flowerbed outlines (plus a parallel `bed_pixels_per_meter` list, one scale per bed), and *plantings* (references to a plant id + instance state: position, current height/diameter, health, last-watered timestamp). Instance state lives on the planting, never on the shared plant definition.

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

- `pip install -r requirements.txt` — install dependencies (`pygame`, `anthropic`)
- `python main.py` — run the application

No linter or test suite is configured yet.

## Project layout

- `main.py` — entry point; owns the pygame init/event/update/draw loop.
- `requirements.txt` — Python dependencies.

This is a fresh scaffold — scenes (Menu, Garden Creation, Garden View), the plant library/garden JSON persistence, and the procedural sprite generator described above do not exist yet.
