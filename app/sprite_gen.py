"""Procedural pixel-art sprite generator.

Draws onto a small low-resolution Surface per archetype (from
species_classifier.py's 10-archetype set), then scales up without
smoothing for a blocky pixel-art look. Generates 4 candidates per plant:
same archetype/palette, small per-candidate jitter for visible variety.
"""
import os
import random

import pygame

from app.persistence import PROJECT_ROOT

SPRITES_DIR = os.path.join(PROJECT_ROOT, "sprites")
GRID_SIZE = 24
TRUNK_BROWN = (110, 78, 50)

CANDIDATE_COUNT = 4


def _jittered_color(hex_color, rng, amount=24):
    color = pygame.Color(hex_color)
    r = max(0, min(255, color.r + rng.randint(-amount, amount)))
    g = max(0, min(255, color.g + rng.randint(-amount, amount)))
    b = max(0, min(255, color.b + rng.randint(-amount, amount)))
    return (r, g, b)


def _draw_trunk(surface, rng, height_frac=0.4):
    trunk_h = int(GRID_SIZE * height_frac)
    trunk_w = max(2, GRID_SIZE // 10)
    x = GRID_SIZE // 2 - trunk_w // 2
    y = GRID_SIZE - trunk_h
    pygame.draw.rect(surface, TRUNK_BROWN, (x, y, trunk_w, trunk_h))
    return y  # top of trunk, where canopy sits


def _draw_tree(surface, palette, rng):
    canopy_y = _draw_trunk(surface, rng, height_frac=0.45)
    color = _jittered_color(rng.choice(palette), rng)
    radius = GRID_SIZE // 2 - 2
    pygame.draw.circle(surface, color, (GRID_SIZE // 2, canopy_y), radius)


def _draw_variant_tree(surface, palette, rng):
    canopy_y = _draw_trunk(surface, rng, height_frac=0.4)
    color = _jittered_color(rng.choice(palette), rng)
    # Conifer-style triangular stack.
    cx = GRID_SIZE // 2
    width = GRID_SIZE - 4
    for i, w in enumerate((width, int(width * 0.7), int(width * 0.4))):
        top = canopy_y - GRID_SIZE // 3 * (2 - i)
        pygame.draw.polygon(surface, color, [
            (cx - w // 2, top + GRID_SIZE // 3),
            (cx + w // 2, top + GRID_SIZE // 3),
            (cx, top),
        ])


def _draw_bush(surface, palette, rng):
    color = _jittered_color(rng.choice(palette), rng)
    cx, cy = GRID_SIZE // 2, GRID_SIZE - GRID_SIZE // 3
    for dx, dy, r in ((-5, 0, 7), (5, 0, 7), (0, -4, 8)):
        pygame.draw.circle(surface, color, (cx + dx, cy + dy), r)


def _draw_variant_bush(surface, palette, rng):
    color = _jittered_color(rng.choice(palette), rng)
    cx, cy = GRID_SIZE // 2, GRID_SIZE - GRID_SIZE // 4
    width = GRID_SIZE - 2
    pygame.draw.ellipse(surface, color, (cx - width // 2, cy - 6, width, 12))


def _draw_flower(surface, palette, rng, petal_shape="round"):
    stem_x = GRID_SIZE // 2
    pygame.draw.line(surface, (60, 130, 60), (stem_x, GRID_SIZE), (stem_x, GRID_SIZE // 2), 2)
    bloom_color = _jittered_color(rng.choice(palette), rng)
    cy = GRID_SIZE // 2 - 3
    if petal_shape == "ring":  # daisy
        for i in range(8):
            import math
            angle = math.pi * 2 * i / 8
            px = stem_x + int(6 * math.cos(angle))
            py = cy + int(6 * math.sin(angle))
            pygame.draw.circle(surface, bloom_color, (px, py), 3)
        pygame.draw.circle(surface, (240, 200, 60), (stem_x, cy), 3)
    elif petal_shape == "cup":  # tulip
        pygame.draw.polygon(surface, bloom_color, [
            (stem_x - 5, cy + 4), (stem_x + 5, cy + 4),
            (stem_x + 4, cy - 5), (stem_x, cy - 2), (stem_x - 4, cy - 5),
        ])
    elif petal_shape == "layered":  # rose
        for r in (7, 5, 3):
            pygame.draw.circle(surface, bloom_color, (stem_x, cy), r, width=2)
        pygame.draw.circle(surface, bloom_color, (stem_x, cy), 2)
    else:  # orchid — irregular petals
        for dx, dy in ((-5, -2), (5, -2), (0, -6), (-3, 3), (3, 3)):
            pygame.draw.circle(surface, bloom_color, (stem_x + dx, cy + dy), 3)


def _draw_fern(surface, palette, rng):
    color = _jittered_color(rng.choice(palette), rng)
    base = (GRID_SIZE // 2, GRID_SIZE - 2)
    for i in range(5):
        angle_deg = -90 + (i - 2) * 20
        import math
        length = GRID_SIZE // 2
        angle = math.radians(angle_deg)
        end = (base[0] + int(length * math.sin(angle)), base[1] - int(length * abs(math.cos(angle))))
        pygame.draw.line(surface, color, base, end, 2)


def _draw_sapling(surface, palette, rng):
    canopy_y = _draw_trunk(surface, rng, height_frac=0.55)
    color = _jittered_color(rng.choice(palette), rng)
    pygame.draw.circle(surface, color, (GRID_SIZE // 2, canopy_y), GRID_SIZE // 5)


_ARCHETYPE_DRAWERS = {
    "tree": _draw_tree,
    "variant_tree": _draw_variant_tree,
    "bush": _draw_bush,
    "variant_bush": _draw_variant_bush,
    "flower_rose": lambda s, p, r: _draw_flower(s, p, r, "layered"),
    "flower_tulip": lambda s, p, r: _draw_flower(s, p, r, "cup"),
    "flower_daisy": lambda s, p, r: _draw_flower(s, p, r, "ring"),
    "flower_orchid": lambda s, p, r: _draw_flower(s, p, r, "orchid"),
    "fern": _draw_fern,
    "sapling": _draw_sapling,
}


def _generate_one(archetype, palette, seed, target_size):
    rng = random.Random(seed)
    surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
    drawer = _ARCHETYPE_DRAWERS.get(archetype, _draw_bush)
    drawer(surface, palette, rng)
    return pygame.transform.scale(surface, target_size)


def generate_candidates(archetype, palette, expected_height, expected_diameter, species=""):
    """Return CANDIDATE_COUNT pygame Surfaces for the given archetype/palette.

    Size is scaled from expected_height/expected_diameter (arbitrary units,
    clamped to a reasonable on-screen sprite range).
    """
    target_w = int(max(24, min(96, expected_diameter)))
    target_h = int(max(24, min(96, expected_height)))
    base_seed = hash((species, archetype, tuple(palette))) & 0xFFFFFFFF
    return [
        _generate_one(archetype, palette, base_seed + i, (target_w, target_h))
        for i in range(CANDIDATE_COUNT)
    ]


def save_candidates(plant_id, surfaces):
    """Write each candidate Surface to sprites/<plant_id>_<i>.png, return the paths."""
    os.makedirs(SPRITES_DIR, exist_ok=True)
    paths = []
    for i, surface in enumerate(surfaces):
        path = os.path.join(SPRITES_DIR, f"{plant_id}_{i}.png")
        pygame.image.save(surface, path)
        paths.append(path)
    return paths


def load_sprite(path):
    return pygame.image.load(path).convert_alpha()
