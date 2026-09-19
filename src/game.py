"""Application shell: window, main loop and top-level state machine."""

from enum import Enum, auto

import pygame

from src import settings
from src.renderer import Camera, build_world_surface
from src.ui import Fonts
from src.world import World


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
        self.fonts = Fonts()
        self.world = World()
        self.world_surface = build_world_surface(self.world, self.fonts)
        self.camera = Camera(self.world.pixel_size)
        self.camera.snap(self.world.layout.player_start)
        self.state = State.PLAYING
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
        view = pygame.Rect(self.camera.offset, self.screen.get_size())
        self.screen.blit(self.world_surface, (0, 0), view)
        pygame.display.flip()
