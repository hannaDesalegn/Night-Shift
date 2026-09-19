"""Application shell: window, main loop and top-level state machine."""

from enum import Enum, auto

import pygame

from src import settings


class State(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(settings.TITLE)
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 64)
        self.state = State.MENU
        self.running = True

    def run(self):
        while self.running:
            dt = min(self.clock.tick(settings.FPS) / 1000, settings.MAX_FRAME_TIME)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def change_state(self, state):
        self.state = state

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def update(self, dt):
        pass

    def draw(self):
        self.screen.fill(settings.BG_COLOR)
        label = self.font.render(settings.TITLE.upper(), True, settings.TEXT_COLOR)
        self.screen.blit(label, label.get_rect(center=self.screen.get_rect().center))
        pygame.display.flip()
