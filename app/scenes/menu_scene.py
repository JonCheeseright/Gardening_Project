"""Main menu: New Garden / Open Garden / Exit, as three oval buttons."""
import sys

import pygame

from app import theme
from app.scene import Scene
from app.widgets import OvalButton


class MenuScene(Scene):
    def on_enter(self):
        center_x = theme.WINDOW_SIZE[0] // 2
        button_w, button_h, gap = 260, 60, 24
        start_y = 260
        self.buttons = [
            OvalButton(
                (center_x - button_w // 2, start_y, button_w, button_h),
                "New Garden", self._new_garden,
            ),
            OvalButton(
                (center_x - button_w // 2, start_y + (button_h + gap), button_w, button_h),
                "Open Garden", self._open_garden,
            ),
            OvalButton(
                (center_x - button_w // 2, start_y + 2 * (button_h + gap), button_w, button_h),
                "Exit", self._exit,
            ),
        ]

    def _new_garden(self):
        from app.scenes.garden_create_scene import GardenCreateScene
        self.manager.switch_to(GardenCreateScene(self.manager))

    def _open_garden(self):
        from app.scenes.garden_open_scene import GardenOpenScene
        self.manager.switch_to(GardenOpenScene(self.manager))

    def _exit(self):
        pygame.quit()
        sys.exit(0)

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface):
        surface.fill(theme.SKY_BLUE)
        title_surf = theme.header_font().render("Gardening Project", True, theme.BLACK)
        title_rect = title_surf.get_rect(center=(theme.WINDOW_SIZE[0] // 2, 150))
        surface.blit(title_surf, title_rect)
        for button in self.buttons:
            button.draw(surface)
