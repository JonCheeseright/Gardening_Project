"""Open Garden: list saved gardens/*.json, pick one, load it."""
import pygame

from app import persistence, theme
from app.scene import Scene
from app.widgets import OvalButton


class GardenOpenScene(Scene):
    def on_enter(self):
        names = persistence.list_garden_names()
        self.buttons = []
        start_y = 160
        for i, name in enumerate(names):
            rect = (theme.WINDOW_SIZE[0] // 2 - 150, start_y + i * 64, 300, 50)
            self.buttons.append(OvalButton(rect, name, lambda n=name: self._open(n)))
        self.back_button = OvalButton(
            (30, theme.WINDOW_SIZE[1] - 80, 140, 44), "Back", self._back
        )
        self.empty = not names

    def _open(self, name):
        garden_data = persistence.load_garden(name)
        from app.scenes.garden_view_scene import GardenViewScene
        self.manager.switch_to(GardenViewScene(self.manager, garden_data))

    def _back(self):
        from app.scenes.menu_scene import MenuScene
        self.manager.switch_to(MenuScene(self.manager))

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)
        self.back_button.handle_event(event)

    def draw(self, surface):
        surface.fill(theme.SKY_BLUE)
        header = theme.header_font().render("Open Garden", True, theme.BLACK)
        surface.blit(header, header.get_rect(center=(theme.WINDOW_SIZE[0] // 2, 90)))
        if self.empty:
            msg = theme.body_font().render("No saved gardens yet.", True, theme.BLACK)
            surface.blit(msg, msg.get_rect(center=(theme.WINDOW_SIZE[0] // 2, 200)))
        for button in self.buttons:
            button.draw(surface)
        self.back_button.draw(surface)
