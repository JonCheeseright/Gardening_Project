"""Garden View: render the garden/beds/plantings, plant new plants into
beds with overlap warnings, and edit planting status (health, size, watering).
"""
import datetime

import pygame

from app import overlap, persistence, theme
from app.plant import HEALTH_OPTIONS, Planting, PlantDefinition
from app.scene import Scene
from app.shapes import shape_from_dict
from app.sprite_gen import load_sprite
from app.widgets import CycleSelector, OvalButton, TextInputBox

MODE_VIEW = "view"
MODE_PICK_PLANT = "pick_plant"
MODE_PLACING = "placing"
MODE_EDIT_PLANTING = "edit_planting"

CANVAS_RECT = (40, 90, theme.WINDOW_SIZE[0] - 80, 420)


class GardenViewScene(Scene):
    def __init__(self, manager, garden_data):
        super().__init__(manager)
        self.garden_data = garden_data

    def on_enter(self):
        self.mode = MODE_VIEW
        self.garden_shape = shape_from_dict(self.garden_data["outline"]) if self.garden_data.get("outline") else None
        self.beds = [shape_from_dict(d) for d in self.garden_data.get("beds", [])]
        self.plantings = [Planting.from_dict(d) for d in self.garden_data.get("plantings", [])]
        self.plant_defs = {p.plant_id: p for p in (
            PlantDefinition.from_dict(d) for d in persistence.load_plants_library()
        )}
        self._sprite_cache = {}
        self.warning_text = None
        self.selected_planting = None

        self.plant_button = OvalButton((30, theme.WINDOW_SIZE[1] - 80, 140, 44), "Plant", self._start_picking)
        self.library_button = OvalButton((190, theme.WINDOW_SIZE[1] - 80, 140, 44), "Library", self._open_library)
        self.save_button = OvalButton((350, theme.WINDOW_SIZE[1] - 80, 140, 44), "Save", self._save)
        self.menu_button = OvalButton((510, theme.WINDOW_SIZE[1] - 80, 140, 44), "Menu", self._to_menu)

    def _open_library(self):
        from app.scenes.plant_library_scene import PlantLibraryScene
        self.manager.push(PlantLibraryScene(self.manager, self._on_library_done))

    def _on_library_done(self, plant_defs):
        self.plant_defs = {p.plant_id: p for p in plant_defs}
        self.manager.pop()

    def _sprite_for(self, plant_def):
        if plant_def.plant_id not in self._sprite_cache:
            path = plant_def.sprite_paths[plant_def.selected_sprite_index]
            self._sprite_cache[plant_def.plant_id] = load_sprite(path)
        return self._sprite_cache[plant_def.plant_id]

    def _start_picking(self):
        if not self.plant_defs:
            self.warning_text = "No plants in the library yet — add one first."
            return
        self.mode = MODE_PICK_PLANT
        self.pick_buttons = []
        for i, plant_def in enumerate(self.plant_defs.values()):
            rect = (theme.WINDOW_SIZE[0] // 2 - 150, 150 + i * 50, 300, 40)
            self.pick_buttons.append(
                OvalButton(rect, plant_def.species, (lambda pd=plant_def: self._pick_plant(pd)))
            )

    def _pick_plant(self, plant_def):
        self._picking_plant_def = plant_def
        self.mode = MODE_PLACING

    def _place_at(self, pos, bed_index):
        plant_def = self._picking_plant_def
        planting = Planting.new(
            plant_id=plant_def.plant_id, bed_index=bed_index, position=pos,
            current_height=plant_def.expected_height * 0.2,
            current_diameter=plant_def.expected_diameter * 0.2,
        )
        self.plantings.append(planting)
        self._check_overlaps()
        self.mode = MODE_VIEW

    def _check_overlaps(self):
        messages = []
        for i in range(len(self.plantings)):
            for j in range(i + 1, len(self.plantings)):
                a, b = self.plantings[i], self.plantings[j]
                pa, pb = self.plant_defs.get(a.plant_id), self.plant_defs.get(b.plant_id)
                if not pa or not pb:
                    continue
                if overlap.immediate_conflict(a.position, a.current_diameter, b.position, b.current_diameter):
                    messages.append(f"{pa.species} and {pb.species} are too close right now.")
                elif overlap.future_conflict(a.position, pa.expected_diameter, b.position, pb.expected_diameter):
                    messages.append(f"{pa.species} and {pb.species} may crowd each other once fully grown.")
        self.warning_text = "; ".join(messages) if messages else None

    def _select_planting(self, planting):
        self.selected_planting = planting
        self.mode = MODE_EDIT_PLANTING
        self.health_selector = CycleSelector((300, 200, 220, 40), list(HEALTH_OPTIONS),
                                              initial_index=HEALTH_OPTIONS.index(planting.health))
        self.height_input = TextInputBox((300, 260, 220, 40), str(planting.current_height), numeric=True)
        self.diameter_input = TextInputBox((300, 320, 220, 40), str(planting.current_diameter), numeric=True)
        self.water_button = OvalButton((300, 380, 220, 40), "Mark Watered", self._mark_watered)
        self.apply_button = OvalButton((300, 440, 100, 40), "Apply", self._apply_edit)
        self.remove_button = OvalButton((420, 440, 100, 40), "Remove", self._remove_planting)

    def _mark_watered(self):
        self.selected_planting.last_watered = datetime.datetime.now().isoformat()

    def _apply_edit(self):
        self.selected_planting.health = self.health_selector.value
        self.selected_planting.current_height = self.height_input.as_float(self.selected_planting.current_height)
        self.selected_planting.current_diameter = self.diameter_input.as_float(self.selected_planting.current_diameter)
        self._check_overlaps()
        self.mode = MODE_VIEW
        self.selected_planting = None

    def _remove_planting(self):
        self.plantings.remove(self.selected_planting)
        self.selected_planting = None
        self._check_overlaps()
        self.mode = MODE_VIEW

    def _bed_index_at(self, pos):
        # Bounding-box hit test per bed (simple approximation, not exact point-in-polygon).
        for i, bed in enumerate(self.beds):
            xs = [p[0] for p in bed.polygon_points()]
            ys = [p[1] for p in bed.polygon_points()]
            if min(xs) <= pos[0] <= max(xs) and min(ys) <= pos[1] <= max(ys):
                return i
        return -1

    def _save(self):
        self.garden_data["plantings"] = [p.to_dict() for p in self.plantings]
        persistence.save_garden(self.garden_data["name"], self.garden_data)
        self.warning_text = None

    def _to_menu(self):
        from app.scenes.menu_scene import MenuScene
        self.manager.switch_to(MenuScene(self.manager))

    def handle_event(self, event):
        if self.mode == MODE_VIEW:
            self.plant_button.handle_event(event)
            self.library_button.handle_event(event)
            self.save_button.handle_event(event)
            self.menu_button.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for planting in self.plantings:
                    if (planting.position[0] - event.pos[0]) ** 2 + (planting.position[1] - event.pos[1]) ** 2 <= 400:
                        self._select_planting(planting)
                        break
        elif self.mode == MODE_PICK_PLANT:
            for button in self.pick_buttons:
                button.handle_event(event)
        elif self.mode == MODE_PLACING:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                canvas_rect = pygame.Rect(CANVAS_RECT)
                if canvas_rect.collidepoint(event.pos):
                    bed_index = self._bed_index_at(event.pos)
                    self._place_at(event.pos, bed_index)
        elif self.mode == MODE_EDIT_PLANTING:
            self.health_selector.handle_event(event)
            self.height_input.handle_event(event)
            self.diameter_input.handle_event(event)
            self.water_button.handle_event(event)
            self.apply_button.handle_event(event)
            self.remove_button.handle_event(event)

    def draw(self, surface):
        surface.fill(theme.GRASS_GREEN)
        if self.garden_shape is not None:
            points = self.garden_shape.polygon_points()
            if len(points) >= 3:
                pygame.draw.polygon(surface, theme.SOIL_BROWN, points, width=3)
        for bed in self.beds:
            points = bed.polygon_points()
            if len(points) >= 3:
                pygame.draw.polygon(surface, (150, 100, 200), points, width=2)

        for planting in self.plantings:
            plant_def = self.plant_defs.get(planting.plant_id)
            if plant_def and plant_def.sprite_paths:
                sprite = self._sprite_for(plant_def)
                surface.blit(sprite, sprite.get_rect(center=planting.position))
            else:
                pygame.draw.circle(surface, theme.WARNING_RED, planting.position, 8)

        name = self.garden_data.get("name", "")
        header = theme.header_font().render(name, True, theme.WHITE)
        surface.blit(header, (CANVAS_RECT[0], 40))

        if self.warning_text:
            warn_surf = theme.small_font().render(self.warning_text, True, theme.WARNING_RED)
            surface.blit(warn_surf, (CANVAS_RECT[0], CANVAS_RECT[1] + CANVAS_RECT[3] + 10))

        if self.mode == MODE_VIEW:
            self.plant_button.draw(surface)
            self.library_button.draw(surface)
            self.save_button.draw(surface)
            self.menu_button.draw(surface)
        elif self.mode == MODE_PICK_PLANT:
            prompt = theme.body_font().render("Choose a plant to place:", True, theme.WHITE)
            surface.blit(prompt, (theme.WINDOW_SIZE[0] // 2 - 150, 110))
            for button in self.pick_buttons:
                button.draw(surface)
        elif self.mode == MODE_PLACING:
            prompt = theme.body_font().render("Click a bed to place the plant", True, theme.WHITE)
            surface.blit(prompt, (CANVAS_RECT[0], 60))
        elif self.mode == MODE_EDIT_PLANTING:
            plant_def = self.plant_defs.get(self.selected_planting.plant_id)
            title = theme.body_font().render(f"Editing: {plant_def.species if plant_def else '?'}", True, theme.WHITE)
            surface.blit(title, (300, 160))
            for label_text, y in (("Health", 200), ("Current height", 260), ("Current diameter", 320)):
                label = theme.small_font().render(label_text, True, theme.WHITE)
                surface.blit(label, (540, y + 10))
            self.health_selector.draw(surface)
            self.height_input.draw(surface)
            self.diameter_input.draw(surface)
            self.water_button.draw(surface)
            if self.selected_planting.last_watered:
                watered_label = theme.small_font().render(
                    f"Last watered: {self.selected_planting.last_watered[:19]}", True, theme.WHITE
                )
                surface.blit(watered_label, (300, 425))
            self.apply_button.draw(surface)
            self.remove_button.draw(surface)
