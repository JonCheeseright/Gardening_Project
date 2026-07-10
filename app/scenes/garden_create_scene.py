"""New Garden flow: name -> draw garden outline -> draw bed outlines -> save."""
import pygame

from app import persistence, theme
from app.garden_outline_tool import GardenOutlineTool
from app.scene import Scene
from app.widgets import OvalButton, TextInputBox

STATE_NAME = "name"
STATE_GARDEN_OUTLINE = "garden_outline"
STATE_BED_OUTLINE = "bed_outline"

CANVAS_RECT = (40, 90, theme.WINDOW_SIZE[0] - 80, 380)


class GardenCreateScene(Scene):
    def on_enter(self):
        self.state = STATE_NAME
        self.name_input = TextInputBox((theme.WINDOW_SIZE[0] // 2 - 150, 260, 300, 44))
        self.name_input.active = True
        self.confirm_name_button = OvalButton(
            (theme.WINDOW_SIZE[0] // 2 - 90, 330, 180, 44), "Continue", self._confirm_name
        )

        self.garden_shape = None
        self.garden_pixels_per_meter = None
        self.beds = []
        self.bed_pixels_per_meter = []
        self.drawing_tool = None

        self.add_bed_button = OvalButton(
            (theme.WINDOW_SIZE[0] - 360, CANVAS_RECT[1] + CANVAS_RECT[3] + 60, 160, 40),
            "Add Bed", self._start_bed,
        )
        self.finish_button = OvalButton(
            (theme.WINDOW_SIZE[0] - 180, CANVAS_RECT[1] + CANVAS_RECT[3] + 60, 160, 40),
            "Finish & Save", self._save_garden,
        )

    def _confirm_name(self):
        if self.name_input.text.strip():
            self.state = STATE_GARDEN_OUTLINE
            self.drawing_tool = GardenOutlineTool(CANVAS_RECT, self._on_garden_outline_confirmed)

    def _on_garden_outline_confirmed(self, shape, pixels_per_meter):
        self.garden_shape = shape
        self.garden_pixels_per_meter = pixels_per_meter
        self.state = STATE_BED_OUTLINE
        self.drawing_tool = None

    def update(self, dt):
        if self.drawing_tool is not None:
            self.drawing_tool.update(dt)

    def _start_bed(self):
        self.drawing_tool = GardenOutlineTool(
            CANVAS_RECT, self._on_bed_confirmed,
            container_polygon=self.garden_shape.polygon_points(),
            obstacle_polygons=[bed.polygon_points() for bed in self.beds],
        )

    def _on_bed_confirmed(self, shape, pixels_per_meter):
        self.beds.append(shape)
        self.bed_pixels_per_meter.append(pixels_per_meter)
        self.drawing_tool = None

    def _save_garden(self):
        garden_data = {
            "name": self.name_input.text.strip(),
            "outline": self.garden_shape.to_dict() if self.garden_shape else None,
            "outline_pixels_per_meter": self.garden_pixels_per_meter,
            "beds": [bed.to_dict() for bed in self.beds],
            "bed_pixels_per_meter": list(self.bed_pixels_per_meter),
            "plantings": [],
        }
        persistence.save_garden(garden_data["name"], garden_data)
        from app.scenes.garden_view_scene import GardenViewScene
        self.manager.switch_to(GardenViewScene(self.manager, garden_data))

    def handle_event(self, event):
        if self.state == STATE_NAME:
            self.name_input.handle_event(event)
            self.confirm_name_button.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self._confirm_name()
        elif self.state == STATE_GARDEN_OUTLINE:
            self.drawing_tool.handle_event(event)
        elif self.state == STATE_BED_OUTLINE:
            if self.drawing_tool is not None:
                self.drawing_tool.handle_event(event)
            else:
                self.add_bed_button.handle_event(event)
                self.finish_button.handle_event(event)

    def draw(self, surface):
        surface.fill(theme.GRASS_GREEN)
        if self.state == STATE_NAME:
            prompt = theme.header_font().render("Name your garden", True, theme.WHITE)
            surface.blit(prompt, prompt.get_rect(center=(theme.WINDOW_SIZE[0] // 2, 200)))
            self.name_input.draw(surface)
            self.confirm_name_button.draw(surface)
            return

        header_text = "Draw the garden outline" if self.state == STATE_GARDEN_OUTLINE else "Draw flowerbeds"
        header = theme.header_font().render(header_text, True, theme.WHITE)
        surface.blit(header, (CANVAS_RECT[0], 40))

        if self.garden_shape is not None:
            points = self.garden_shape.polygon_points()
            if len(points) >= 3:
                pygame.draw.polygon(surface, theme.SOIL_BROWN, points, width=3)
        for bed in self.beds:
            points = bed.polygon_points()
            if len(points) >= 3:
                pygame.draw.polygon(surface, (150, 100, 200), points, width=2)

        if self.drawing_tool is not None:
            self.drawing_tool.draw(surface)
        elif self.state == STATE_BED_OUTLINE:
            self.add_bed_button.draw(surface)
            self.finish_button.draw(surface)
            count_label = theme.body_font().render(f"{len(self.beds)} bed(s) added", True, theme.WHITE)
            surface.blit(count_label, (CANVAS_RECT[0], CANVAS_RECT[1] + CANVAS_RECT[3] + 20))
