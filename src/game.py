"""Application shell: window, main loop and top-level state machine."""

from enum import Enum, auto

import pygame

from src import settings
from src.controls import read_input
from src.renderer import (
    Camera,
    build_world_surface,
    draw_door,
    draw_pickup,
    draw_player,
)
from src.session import Session
from src.ui import Fonts


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
        self.time = 0.0
        self.key_events = []
        self.running = True
        self.new_session()

    def new_session(self):
        self.session = Session()
        # The static layer never changes between runs, so build it only once.
        if not hasattr(self, "world_surface"):
            self.world_surface = build_world_surface(self.session.world, self.fonts)
        self.camera = Camera(self.session.world.pixel_size)
        self.camera.snap(self.session.player.pos)
        self.state = State.PLAYING

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
        self.key_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                self.key_events.append(event)

    def update(self, dt):
        self.time += dt
        if self.state is State.PLAYING:
            controls = read_input(pygame.key.get_pressed(), self.key_events)
            self.session.update(dt, controls)
            self.camera.follow(self.session.player.pos, dt)

    def draw(self):
        self.screen.fill(settings.BG_COLOR)
        view = pygame.Rect(self.camera.offset, self.screen.get_size())
        self.screen.blit(self.world_surface, (0, 0), view)
        session = self.session
        target = session.interaction_target()
        for door in session.doors:
            can_open = session.requirement_met(door.requirement)
            draw_door(self.screen, door, self.camera, self.time, can_open, door is target)
        for pickup in self.session.pickups:
            if not pickup.collected:
                draw_pickup(self.screen, pickup, self.camera, self.time)
        draw_player(self.screen, self.session.player, self.camera)
        pygame.display.flip()
