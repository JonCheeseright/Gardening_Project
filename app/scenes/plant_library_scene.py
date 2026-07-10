"""Plant Library: list existing plant definitions, add a new one with
procedurally generated sprite candidates to choose from.
"""
import pygame

from app import persistence, species_classifier, sprite_gen, theme
from app.plant import PlantDefinition
from app.scene import Scene
from app.widgets import OvalButton, TextInputBox

STATE_LIST = "list"
STATE_FORM = "form"
STATE_CANDIDATES = "candidates"


class PlantLibraryScene(Scene):
    def __init__(self, manager, on_done):
        """on_done(plant_defs) is called with the updated list when the user leaves."""
        super().__init__(manager)
        self.on_done = on_done

    def on_enter(self):
        self.state = STATE_LIST
        self.plant_defs = [PlantDefinition.from_dict(d) for d in persistence.load_plants_library()]
        self._build_list_widgets()

    def _build_list_widgets(self):
        self.add_button = OvalButton((30, theme.WINDOW_SIZE[1] - 80, 160, 44), "Add Plant", self._start_form)
        self.done_button = OvalButton((theme.WINDOW_SIZE[0] - 190, theme.WINDOW_SIZE[1] - 80, 160, 44), "Done", self._finish)

    def _start_form(self):
        self.state = STATE_FORM
        self.species_input = TextInputBox((300, 160, 300, 40))
        self.height_input = TextInputBox((300, 220, 300, 40), numeric=True)
        self.diameter_input = TextInputBox((300, 280, 300, 40), numeric=True)
        self.species_input.active = True
        self.generate_button = OvalButton((300, 340, 200, 44), "Generate Sprites", self._generate)
        self.warning = None

    def _generate(self):
        species = self.species_input.text.strip()
        height = self.height_input.as_float(default=50.0)
        diameter = self.diameter_input.as_float(default=40.0)
        if not species:
            self.warning = "Enter a species name first."
            return
        result = species_classifier.classify_species(species)
        candidates = sprite_gen.generate_candidates(
            result.archetype, result.palette, height, diameter, species=species
        )
        self._pending = {
            "species": species, "height": height, "diameter": diameter,
            "archetype": result.archetype, "palette": result.palette,
            "fallback_used": result.fallback_used, "candidates": candidates,
        }
        self.state = STATE_CANDIDATES
        self._build_candidate_widgets()

    def _build_candidate_widgets(self):
        self.candidate_buttons = []
        spacing = theme.WINDOW_SIZE[0] // (sprite_gen.CANDIDATE_COUNT + 1)
        for i in range(sprite_gen.CANDIDATE_COUNT):
            x = spacing * (i + 1)
            rect = (x - 60, 400, 120, 40)
            self.candidate_buttons.append(OvalButton(rect, f"Choose #{i + 1}", (lambda idx=i: self._choose(idx))))

    def _choose(self, index):
        pending = self._pending
        plant_def = PlantDefinition.new(
            species=pending["species"],
            expected_height=pending["height"],
            expected_diameter=pending["diameter"],
            archetype=pending["archetype"],
            palette=pending["palette"],
            classifier_fallback_used=pending["fallback_used"],
        )
        plant_def.sprite_paths = sprite_gen.save_candidates(plant_def.plant_id, pending["candidates"])
        plant_def.selected_sprite_index = index
        self.plant_defs.append(plant_def)
        persistence.save_plants_library([p.to_dict() for p in self.plant_defs])
        self.state = STATE_LIST

    def _finish(self):
        self.on_done(self.plant_defs)

    def handle_event(self, event):
        if self.state == STATE_LIST:
            self.add_button.handle_event(event)
            self.done_button.handle_event(event)
        elif self.state == STATE_FORM:
            self.species_input.handle_event(event)
            self.height_input.handle_event(event)
            self.diameter_input.handle_event(event)
            self.generate_button.handle_event(event)
        elif self.state == STATE_CANDIDATES:
            for button in self.candidate_buttons:
                button.handle_event(event)

    def draw(self, surface):
        surface.fill(theme.SKY_BLUE)
        if self.state == STATE_LIST:
            header = theme.header_font().render("Plant Library", True, theme.BLACK)
            surface.blit(header, (30, 30))
            for i, plant_def in enumerate(self.plant_defs):
                label = theme.body_font().render(
                    f"{plant_def.species} (h={plant_def.expected_height:.0f}, d={plant_def.expected_diameter:.0f})",
                    True, theme.BLACK,
                )
                surface.blit(label, (30, 90 + i * 30))
            self.add_button.draw(surface)
            self.done_button.draw(surface)
        elif self.state == STATE_FORM:
            header = theme.header_font().render("Add Plant", True, theme.BLACK)
            surface.blit(header, (30, 90))
            for label_text, y in (("Species", 168), ("Expected height", 228), ("Expected diameter", 288)):
                label = theme.body_font().render(label_text, True, theme.BLACK)
                surface.blit(label, (100, y))
            self.species_input.draw(surface)
            self.height_input.draw(surface)
            self.diameter_input.draw(surface)
            self.generate_button.draw(surface)
            if self.warning:
                warn_surf = theme.small_font().render(self.warning, True, theme.WARNING_RED)
                surface.blit(warn_surf, (300, 390))
        elif self.state == STATE_CANDIDATES:
            header = theme.header_font().render("Choose a sprite", True, theme.BLACK)
            surface.blit(header, (30, 30))
            if self._pending["fallback_used"]:
                warn = theme.small_font().render(
                    "Could not reach Claude for species classification — using a neutral default.",
                    True, theme.WARNING_ORANGE,
                )
                surface.blit(warn, (30, 70))
            spacing = theme.WINDOW_SIZE[0] // (sprite_gen.CANDIDATE_COUNT + 1)
            for i, candidate in enumerate(self._pending["candidates"]):
                x = spacing * (i + 1)
                rect = candidate.get_rect(center=(x, 300))
                surface.blit(candidate, rect)
            for button in self.candidate_buttons:
                button.draw(surface)
