"""Shared visual constants: colors, fonts, window sizing.

Font choice: pygame's own bundled default font (no external files to
download). Retro pixelation of the font/UI chrome is deferred polish.
"""
import pygame

WINDOW_SIZE = (960, 640)
FPS = 60

SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (86, 176, 90)
SOIL_BROWN = (121, 85, 58)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
BUTTON_FILL = (250, 226, 120)
BUTTON_BORDER = (60, 60, 60)
BUTTON_HOVER = (255, 240, 170)
ZOOM_BUTTON_FILL = (170, 170, 170)
ZOOM_BUTTON_HOVER = (200, 200, 200)
ZOOM_BUTTON_BORDER = (90, 90, 90)
WARNING_RED = (200, 60, 60)
WARNING_ORANGE = (230, 150, 40)
TEXT_INPUT_FILL = (255, 255, 255)
TEXT_INPUT_BORDER = (60, 60, 60)

_HEADER_SIZE = 36
_BODY_SIZE = 22
_SMALL_SIZE = 18

_font_cache = {}


def _get_font(size, bold):
    key = (size, bold)
    if key not in _font_cache:
        font = pygame.font.Font(pygame.font.get_default_font(), size)
        font.set_bold(bold)
        _font_cache[key] = font
    return _font_cache[key]


def header_font():
    return _get_font(_HEADER_SIZE, bold=True)


def body_font():
    return _get_font(_BODY_SIZE, bold=False)


def small_font():
    return _get_font(_SMALL_SIZE, bold=False)
