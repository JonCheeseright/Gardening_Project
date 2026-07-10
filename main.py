"""Entry point for the Gardening Project application."""
import pygame

WINDOW_SIZE = (800, 600)
BACKGROUND_COLOR = (135, 206, 235)  # sky blue placeholder
FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Gardening Project")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BACKGROUND_COLOR)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
