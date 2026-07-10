"""Scene base class and a small stack-based scene manager."""


class Scene:
    """Base class for all app scenes (Menu, Garden Creation, Garden View, ...)."""

    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        """Handle a single pygame event."""

    def update(self, dt):
        """Advance any time-based state. dt is seconds since last frame."""

    def draw(self, surface):
        """Draw this scene onto the given surface."""

    def on_enter(self):
        """Called when this scene becomes the active/top scene."""

    def on_resume(self):
        """Called when a pushed scene above this one is popped, returning focus here."""


class SceneManager:
    """Stack-based scene switcher driven by main.py's game loop."""

    def __init__(self):
        self._stack = []

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def switch_to(self, scene):
        """Replace the entire stack with a single new scene."""
        self._stack = [scene]
        scene.on_enter()

    def push(self, scene):
        """Push a scene on top (e.g. a modal dialog), keeping the one below."""
        self._stack.append(scene)
        scene.on_enter()

    def pop(self):
        """Pop the top scene and resume the one beneath it."""
        if len(self._stack) > 1:
            self._stack.pop()
            self.current.on_resume()

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, surface):
        if self.current:
            self.current.draw(surface)
