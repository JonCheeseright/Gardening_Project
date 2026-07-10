"""Entry point for the Gardening Project application."""
import pygame

from app import theme
from app.scene import SceneManager
from app.scenes.menu_scene import MenuScene


def main():
    pygame.init()
    screen = pygame.display.set_mode(theme.WINDOW_SIZE)
    pygame.display.set_caption("Gardening Project")
    clock = pygame.time.Clock()

    manager = SceneManager()
    manager.switch_to(MenuScene(manager))

    running = True
    while running:
        dt = clock.tick(theme.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                manager.handle_event(event)

        manager.update(dt)
        manager.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
