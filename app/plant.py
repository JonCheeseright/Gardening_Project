"""Plant data model: shared definitions (library) vs. per-garden plantings.

Instance state (size, health, watering) lives entirely on the Planting,
never on the shared PlantDefinition, per CLAUDE.md's persistence design.
"""
import uuid

HEALTH_OPTIONS = ("too well", "healthy", "struggling", "dead")


class PlantDefinition:
    """A shared, reusable plant definition stored in plants_library.json."""

    def __init__(self, plant_id, species, expected_height, expected_diameter,
                 archetype, palette, sprite_paths=None, selected_sprite_index=0,
                 classifier_fallback_used=False):
        self.plant_id = plant_id
        self.species = species
        self.expected_height = expected_height
        self.expected_diameter = expected_diameter
        self.archetype = archetype
        self.palette = palette
        self.sprite_paths = sprite_paths or []
        self.selected_sprite_index = selected_sprite_index
        self.classifier_fallback_used = classifier_fallback_used

    @classmethod
    def new(cls, species, expected_height, expected_diameter, archetype, palette,
            classifier_fallback_used=False):
        return cls(
            plant_id=str(uuid.uuid4()),
            species=species,
            expected_height=expected_height,
            expected_diameter=expected_diameter,
            archetype=archetype,
            palette=palette,
            classifier_fallback_used=classifier_fallback_used,
        )

    def to_dict(self):
        return {
            "plant_id": self.plant_id,
            "species": self.species,
            "expected_height": self.expected_height,
            "expected_diameter": self.expected_diameter,
            "archetype": self.archetype,
            "palette": self.palette,
            "sprite_paths": self.sprite_paths,
            "selected_sprite_index": self.selected_sprite_index,
            "classifier_fallback_used": self.classifier_fallback_used,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            plant_id=d["plant_id"],
            species=d["species"],
            expected_height=d["expected_height"],
            expected_diameter=d["expected_diameter"],
            archetype=d["archetype"],
            palette=d["palette"],
            sprite_paths=d.get("sprite_paths", []),
            selected_sprite_index=d.get("selected_sprite_index", 0),
            classifier_fallback_used=d.get("classifier_fallback_used", False),
        )


class Planting:
    """A garden-specific instance of a plant, placed in a bed."""

    def __init__(self, planting_id, plant_id, bed_index, position,
                 current_height, current_diameter, health="healthy",
                 last_watered=None, watering_requirement=None):
        self.planting_id = planting_id
        self.plant_id = plant_id
        self.bed_index = bed_index
        self.position = position  # (x, y) in garden canvas coordinates
        self.current_height = current_height
        self.current_diameter = current_diameter
        self.health = health
        self.last_watered = last_watered  # ISO timestamp string, or None
        # Deferred per CLAUDE.md item 5: not calculated yet, just stored.
        self.watering_requirement = watering_requirement

    @classmethod
    def new(cls, plant_id, bed_index, position, current_height, current_diameter):
        return cls(
            planting_id=str(uuid.uuid4()),
            plant_id=plant_id,
            bed_index=bed_index,
            position=position,
            current_height=current_height,
            current_diameter=current_diameter,
        )

    def to_dict(self):
        return {
            "planting_id": self.planting_id,
            "plant_id": self.plant_id,
            "bed_index": self.bed_index,
            "position": list(self.position),
            "current_height": self.current_height,
            "current_diameter": self.current_diameter,
            "health": self.health,
            "last_watered": self.last_watered,
            "watering_requirement": self.watering_requirement,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            planting_id=d["planting_id"],
            plant_id=d["plant_id"],
            bed_index=d["bed_index"],
            position=tuple(d["position"]),
            current_height=d["current_height"],
            current_diameter=d["current_diameter"],
            health=d.get("health", "healthy"),
            last_watered=d.get("last_watered"),
            watering_requirement=d.get("watering_requirement"),
        )
