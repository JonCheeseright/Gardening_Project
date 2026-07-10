"""Garden/bed outline editor: an always-editable polygon that starts as a
rectangle. Left-click an edge to insert a vertex there; left-click (without
dragging) an existing vertex to remove it; drag a vertex to reshape.

The outline's true geometry is stored in meters, anchored to a fixed screen
point (self._anchor_screen) that never moves once the tool is created.
Screen-pixel positions are derived from that by multiplying by
pixels_per_meter. The "+" button grows the real-world area represented (the
outline appears smaller on screen); the "-" button shrinks that area (the
outline appears larger on screen). Both buttons re-center the outline's
bounding box on its anchor afterwards.

Every edit (drag, insert, remove, zoom) is only committed if the resulting
polygon stays fully inside its container (the garden outline when drawing a
bed, or the drawing canvas when drawing the garden itself) and doesn't
overlap any obstacle polygon (other flowerbeds, when drawing a bed) —
otherwise the edit is silently discarded. Shrinking ("-") flashes the button
red 3 times when refused, since that's the direction most likely to be
pushed too far by a user zooming in.
"""
import math

import pygame

from app import geometry, theme
from app.shapes import Polygon
from app.widgets import OvalButton

HANDLE_RADIUS = 7
VERTEX_HIT_RADIUS_SQ = (HANDLE_RADIUS * 2) ** 2
EDGE_CLICK_TOLERANCE = 8
DRAG_THRESHOLD_SQ = 5 ** 2
DRAG_BISECTION_ITERS = 20

DEFAULT_PIXELS_PER_METER = 20.0
MIN_PIXELS_PER_METER = 2.0
MAX_PIXELS_PER_METER = 200.0
ZOOM_FACTOR = 1.25

ZOOM_BUTTON_DIAMETER = 40

FLASH_INTERVAL = 0.15
FLASH_TOGGLES = 6  # 3 full red/normal flashes

# Candidate sizes/positions tried (largest first) when auto-fitting a new
# bed's initial rectangle into the available space of its garden. The grid
# is fine enough to reliably find a free spot even when existing beds
# already cover a large fraction of the garden.
_FIT_SCALES = (0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.07, 0.05, 0.03, 0.02)
_FIT_GRID_FRACTIONS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
_FIT_CENTER_FRACTIONS = tuple(sorted(
    ((fx, fy) for fx in _FIT_GRID_FRACTIONS for fy in _FIT_GRID_FRACTIONS),
    key=lambda f: (f[0] - 0.5) ** 2 + (f[1] - 0.5) ** 2,
))


def _closest_point_on_segment(pos, a, b):
    ax, ay = a
    bx, by = b
    px, py = pos
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return a
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return (ax + t * dx, ay + t * dy)


def _rect_points(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
            (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def _fits(rect, container, obstacles):
    if not geometry.polygon_fully_inside(rect, container):
        return False
    return not any(geometry.polygons_overlap(rect, obstacle) for obstacle in obstacles)


def _find_default_rect(container, obstacles):
    """Largest centered rectangle (tried largest-first) that fits inside
    `container` without overlapping any polygon in `obstacles`."""
    xs = [p[0] for p in container]
    ys = [p[1] for p in container]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    bbox_w, bbox_h = max_x - min_x, max_y - min_y

    for scale in _FIT_SCALES:
        w, h = bbox_w * scale, bbox_h * scale
        for fx, fy in _FIT_CENTER_FRACTIONS:
            cx, cy = min_x + bbox_w * fx, min_y + bbox_h * fy
            rect = _rect_points(cx, cy, w, h)
            if _fits(rect, container, obstacles):
                return rect

    # Nothing fit (garden essentially full) — fall back to a tiny rectangle
    # at the garden's center; the user can still nudge it from there.
    cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
    return _rect_points(cx, cy, bbox_w * 0.05, bbox_h * 0.05)


class GardenOutlineTool:
    def __init__(self, canvas_rect, on_confirm, pixels_per_meter=DEFAULT_PIXELS_PER_METER,
                 container_polygon=None, obstacle_polygons=None):
        self.canvas_rect = pygame.Rect(canvas_rect)
        self.on_confirm = on_confirm
        self.pixels_per_meter = pixels_per_meter
        self.container_polygon = container_polygon
        self.obstacle_polygons = list(obstacle_polygons) if obstacle_polygons else []

        canvas_corners = [
            self.canvas_rect.topleft, self.canvas_rect.topright,
            self.canvas_rect.bottomright, self.canvas_rect.bottomleft,
        ]
        self._effective_container = container_polygon if container_polygon is not None else canvas_corners

        if container_polygon is not None:
            initial_screen_vertices = _find_default_rect(container_polygon, self.obstacle_polygons)
        else:
            margin_x = self.canvas_rect.width * 0.15
            margin_y = self.canvas_rect.height * 0.15
            initial_screen_vertices = [
                (self.canvas_rect.left + margin_x, self.canvas_rect.top + margin_y),
                (self.canvas_rect.right - margin_x, self.canvas_rect.top + margin_y),
                (self.canvas_rect.right - margin_x, self.canvas_rect.bottom - margin_y),
                (self.canvas_rect.left + margin_x, self.canvas_rect.bottom - margin_y),
            ]

        xs = [v[0] for v in initial_screen_vertices]
        ys = [v[1] for v in initial_screen_vertices]
        self._anchor_screen = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
        self._model_vertices = [self._to_model(v) for v in initial_screen_vertices]

        self._drag_index = None
        self._drag_start_pos = None
        self._dragged = False

        self._shrink_flash_toggles_remaining = 0
        self._shrink_flash_timer = 0.0
        self._shrink_flash_on = False

        button_y = self.canvas_rect.bottom + 10
        self.grow_area_button = OvalButton(
            (self.canvas_rect.x, button_y, ZOOM_BUTTON_DIAMETER, ZOOM_BUTTON_DIAMETER), "+", self._grow_area,
            fill_color=theme.ZOOM_BUTTON_FILL, hover_color=theme.ZOOM_BUTTON_HOVER,
            border_color=theme.ZOOM_BUTTON_BORDER,
        )
        self.shrink_area_button = OvalButton(
            (self.canvas_rect.x + ZOOM_BUTTON_DIAMETER + 10, button_y, ZOOM_BUTTON_DIAMETER, ZOOM_BUTTON_DIAMETER),
            "-", self._shrink_area,
            fill_color=theme.ZOOM_BUTTON_FILL, hover_color=theme.ZOOM_BUTTON_HOVER,
            border_color=theme.ZOOM_BUTTON_BORDER,
        )
        self.confirm_button = OvalButton((self.canvas_rect.right - 150, button_y, 150, 40), "Confirm", self._confirm)

    def _to_screen(self, model_point):
        ax, ay = self._anchor_screen
        mx, my = model_point
        return (ax + mx * self.pixels_per_meter, ay + my * self.pixels_per_meter)

    def _to_model(self, screen_point):
        ax, ay = self._anchor_screen
        sx, sy = screen_point
        return ((sx - ax) / self.pixels_per_meter, (sy - ay) / self.pixels_per_meter)

    def _screen_vertices(self, model_vertices=None):
        return [self._to_screen(v) for v in (model_vertices if model_vertices is not None else self._model_vertices)]

    def _is_valid(self, model_vertices):
        screen = self._screen_vertices(model_vertices)
        if not geometry.polygon_fully_inside(screen, self._effective_container):
            return False
        return not any(geometry.polygons_overlap(screen, obstacle) for obstacle in self.obstacle_polygons)

    def _recentered(self, model_vertices):
        xs = [v[0] for v in model_vertices]
        ys = [v[1] for v in model_vertices]
        offset_x = (max(xs) + min(xs)) / 2
        offset_y = (max(ys) + min(ys)) / 2
        return [(x - offset_x, y - offset_y) for x, y in model_vertices]

    def _try_zoom(self, new_ppm, flash_on_failure):
        old_ppm = self.pixels_per_meter
        self.pixels_per_meter = new_ppm
        candidate = self._recentered(self._model_vertices)
        if self._is_valid(candidate):
            self._model_vertices = candidate
            return True
        self.pixels_per_meter = old_ppm
        if flash_on_failure:
            self._shrink_flash_toggles_remaining = FLASH_TOGGLES
            self._shrink_flash_timer = 0.0
            self._shrink_flash_on = True
        return False

    def _grow_area(self):
        self._try_zoom(max(MIN_PIXELS_PER_METER, self.pixels_per_meter / ZOOM_FACTOR), flash_on_failure=False)

    def _shrink_area(self):
        self._try_zoom(min(MAX_PIXELS_PER_METER, self.pixels_per_meter * ZOOM_FACTOR), flash_on_failure=True)

    def _confirm(self):
        if len(self._model_vertices) >= 3:
            self.on_confirm(Polygon(self._screen_vertices()), self.pixels_per_meter)

    def _vertex_move_is_valid(self, index, screen_pos):
        candidate = list(self._model_vertices)
        candidate[index] = self._to_model(screen_pos)
        return self._is_valid(candidate)

    def _furthest_valid_drag_pos(self, index, from_screen_pos, to_screen_pos):
        """Slide from a known-valid position towards the target, stopping at
        the boundary of whatever forbidden region blocks the way, so a drag
        keeps tracking the mouse in any direction that's still allowed
        instead of freezing outright."""
        if self._vertex_move_is_valid(index, to_screen_pos):
            return to_screen_pos
        lo, hi = from_screen_pos, to_screen_pos
        for _ in range(DRAG_BISECTION_ITERS):
            mid = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
            if self._vertex_move_is_valid(index, mid):
                lo = mid
            else:
                hi = mid
        return lo

    def _vertex_at(self, pos, screen_vertices):
        for i, vertex in enumerate(screen_vertices):
            if (vertex[0] - pos[0]) ** 2 + (vertex[1] - pos[1]) ** 2 <= VERTEX_HIT_RADIUS_SQ:
                return i
        return None

    def _edge_at(self, pos, screen_vertices):
        n = len(screen_vertices)
        for i in range(n):
            a, b = screen_vertices[i], screen_vertices[(i + 1) % n]
            closest = _closest_point_on_segment(pos, a, b)
            if math.hypot(closest[0] - pos[0], closest[1] - pos[1]) <= EDGE_CLICK_TOLERANCE:
                return i, closest
        return None, None

    def handle_event(self, event):
        self.grow_area_button.handle_event(event)
        self.shrink_area_button.handle_event(event)
        self.confirm_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.canvas_rect.collidepoint(event.pos):
                return
            screen_vertices = self._screen_vertices()
            vertex_index = self._vertex_at(event.pos, screen_vertices)
            if vertex_index is not None:
                self._drag_index = vertex_index
                self._drag_start_pos = event.pos
                self._dragged = False
                return
            edge_index, closest_point = self._edge_at(event.pos, screen_vertices)
            if edge_index is not None:
                candidate = list(self._model_vertices)
                candidate.insert(edge_index + 1, self._to_model(closest_point))
                if self._is_valid(candidate):
                    self._model_vertices = candidate

        elif event.type == pygame.MOUSEMOTION and self._drag_index is not None:
            if not self._dragged:
                dx = event.pos[0] - self._drag_start_pos[0]
                dy = event.pos[1] - self._drag_start_pos[1]
                if dx * dx + dy * dy > DRAG_THRESHOLD_SQ:
                    self._dragged = True
            if self._dragged:
                current_screen_pos = self._to_screen(self._model_vertices[self._drag_index])
                resolved_pos = self._furthest_valid_drag_pos(self._drag_index, current_screen_pos, event.pos)
                candidate = list(self._model_vertices)
                candidate[self._drag_index] = self._to_model(resolved_pos)
                if self._is_valid(candidate):
                    self._model_vertices = candidate

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._drag_index is not None:
            if not self._dragged and len(self._model_vertices) > 3:
                candidate = list(self._model_vertices)
                del candidate[self._drag_index]
                if self._is_valid(candidate):
                    self._model_vertices = candidate
            self._drag_index = None
            self._drag_start_pos = None
            self._dragged = False

    def update(self, dt):
        if self._shrink_flash_toggles_remaining <= 0:
            self._shrink_flash_on = False
            return
        self._shrink_flash_timer += dt
        while self._shrink_flash_timer >= FLASH_INTERVAL and self._shrink_flash_toggles_remaining > 0:
            self._shrink_flash_timer -= FLASH_INTERVAL
            self._shrink_flash_on = not self._shrink_flash_on
            self._shrink_flash_toggles_remaining -= 1

    def _bounding_size_meters(self):
        xs = [v[0] for v in self._model_vertices]
        ys = [v[1] for v in self._model_vertices]
        return max(xs) - min(xs), max(ys) - min(ys)

    def _area_sq_meters(self):
        return Polygon(self._model_vertices).area()

    def draw(self, surface):
        pygame.draw.rect(surface, theme.WHITE, self.canvas_rect, width=2)

        screen_vertices = self._screen_vertices()
        if len(screen_vertices) >= 3:
            pygame.draw.polygon(surface, theme.SOIL_BROWN, screen_vertices, width=0)
            pygame.draw.polygon(surface, theme.BLACK, screen_vertices, width=2)
        for vertex in screen_vertices:
            pygame.draw.circle(surface, theme.WARNING_ORANGE, vertex, HANDLE_RADIUS)

        width_m, height_m = self._bounding_size_meters()
        label = (
            f"{width_m:.1f} x {height_m:.1f} m (bounding box)  |  "
            f"Area: {self._area_sq_meters():.1f} sq m  |  {self.pixels_per_meter:.0f} px/m"
        )
        label_surf = theme.small_font().render(label, True, theme.WHITE)
        surface.blit(label_surf, (self.canvas_rect.x, self.canvas_rect.y - 24))

        self.shrink_area_button.fill_color = theme.WARNING_RED if self._shrink_flash_on else theme.ZOOM_BUTTON_FILL
        self.grow_area_button.draw(surface)
        self.shrink_area_button.draw(surface)
        self.confirm_button.draw(surface)
