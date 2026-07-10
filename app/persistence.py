"""JSON persistence for the plant library (shared) and garden save files.

Writes go through a temp-file-then-rename so a crash mid-write can't
corrupt an existing save.
"""
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTS_LIBRARY_PATH = os.path.join(PROJECT_ROOT, "plants_library.json")
GARDENS_DIR = os.path.join(PROJECT_ROOT, "gardens")


def _atomic_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def load_plants_library():
    """Return list of plant definition dicts, or [] if no library exists yet."""
    if not os.path.exists(PLANTS_LIBRARY_PATH):
        return []
    with open(PLANTS_LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plants_library(plant_defs):
    """plant_defs: list of plant definition dicts."""
    _atomic_write(PLANTS_LIBRARY_PATH, plant_defs)


def list_garden_names():
    if not os.path.isdir(GARDENS_DIR):
        return []
    return sorted(
        name[:-5] for name in os.listdir(GARDENS_DIR) if name.endswith(".json")
    )


def garden_path(name):
    return os.path.join(GARDENS_DIR, f"{name}.json")


def load_garden(name):
    with open(garden_path(name), "r", encoding="utf-8") as f:
        return json.load(f)


def save_garden(name, garden_data):
    _atomic_write(garden_path(name), garden_data)
