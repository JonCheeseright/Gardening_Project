"""Reusable UI widgets: oval buttons, text input boxes, cycling value selectors."""
import pygame

from app import theme


class OvalButton:
    """A clickable oval (or, with equal width/height, circular) button with
    a text label. Fill/hover/border colors default to the standard button
    theme but can be overridden, e.g. for the grey round zoom buttons."""

    def __init__(self, rect, label, on_click, font=None,
                 fill_color=None, hover_color=None, border_color=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.font = font or theme.body_font()
        self.hovered = False
        self.fill_color = fill_color or theme.BUTTON_FILL
        self.hover_color = hover_color or theme.BUTTON_HOVER
        self.border_color = border_color or theme.BUTTON_BORDER

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def draw(self, surface):
        fill = self.hover_color if self.hovered else self.fill_color
        pygame.draw.ellipse(surface, fill, self.rect)
        pygame.draw.ellipse(surface, self.border_color, self.rect, width=3)
        text_surf = self.font.render(self.label, True, theme.BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class TextInputBox:
    """A single-line text input box. Click to focus, type to edit."""

    def __init__(self, rect, initial_text="", font=None, numeric=False):
        self.rect = pygame.Rect(rect)
        self.text = initial_text
        self.font = font or theme.body_font()
        self.numeric = numeric
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                self.active = False
            elif event.unicode:
                if self.numeric:
                    if event.unicode.isdigit() or (event.unicode == "." and "." not in self.text):
                        self.text += event.unicode
                else:
                    self.text += event.unicode

    def draw(self, surface):
        pygame.draw.rect(surface, theme.TEXT_INPUT_FILL, self.rect)
        border_color = theme.BUTTON_HOVER if self.active else theme.TEXT_INPUT_BORDER
        pygame.draw.rect(surface, border_color, self.rect, width=2)
        text_surf = self.font.render(self.text, True, theme.BLACK)
        surface.blit(text_surf, (self.rect.x + 6, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))

    def as_float(self, default=0.0):
        try:
            return float(self.text)
        except ValueError:
            return default


class CycleSelector:
    """A label with left/right arrow buttons to cycle through a fixed set of options."""

    def __init__(self, rect, options, initial_index=0, font=None):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.index = initial_index
        self.font = font or theme.body_font()
        arrow_w = 30
        self.left_rect = pygame.Rect(self.rect.x, self.rect.y, arrow_w, self.rect.height)
        self.right_rect = pygame.Rect(self.rect.right - arrow_w, self.rect.y, arrow_w, self.rect.height)

    @property
    def value(self):
        return self.options[self.index]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_rect.collidepoint(event.pos):
                self.index = (self.index - 1) % len(self.options)
            elif self.right_rect.collidepoint(event.pos):
                self.index = (self.index + 1) % len(self.options)

    def draw(self, surface):
        pygame.draw.rect(surface, theme.TEXT_INPUT_FILL, self.rect)
        pygame.draw.rect(surface, theme.TEXT_INPUT_BORDER, self.rect, width=2)
        for arrow_rect, symbol in ((self.left_rect, "<"), (self.right_rect, ">")):
            arrow_surf = self.font.render(symbol, True, theme.BLACK)
            surface.blit(arrow_surf, arrow_surf.get_rect(center=arrow_rect.center))
        label_surf = self.font.render(str(self.value), True, theme.BLACK)
        label_rect = label_surf.get_rect(center=self.rect.center)
        surface.blit(label_surf, label_rect)
