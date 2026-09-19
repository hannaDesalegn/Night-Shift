"""Application shell: window, main loop and top-level state machine."""

from enum import Enum, auto

import pygame

from src import settings
from src.controls import read_input
from src.lighting import Lighting, scale_color
from src.renderer import (
    LIGHT_LOCKED,
    LIGHT_OPEN,
    PICKUP_COLORS,
    Camera,
    build_world_surface,
    door_lamp_pos,
    draw_door,
    draw_door_lamp,
    draw_emergency_light,
    draw_enemy,
    draw_enemy_eyes,
    draw_generator,
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
        self.lighting = Lighting(self.session.world)
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
        self.draw_world()
        pygame.display.flip()

    def draw_world(self):
        session, camera, t = self.session, self.camera, self.time
        view = pygame.Rect(camera.offset, self.screen.get_size())
        self.screen.blit(self.world_surface, (0, 0), view)
        for door in session.doors:
            draw_door(self.screen, door, camera, t)
        draw_generator(self.screen, session.generator, camera, t)
        for pickup in session.pickups:
            if not pickup.collected:
                draw_pickup(self.screen, pickup, camera, t)
        draw_player(self.screen, session.player, camera)
        draw_enemy(self.screen, session.enemy, camera, t)

        self.lighting.render(self.screen, camera, session.power_on, self._lights(), self._beam())

        # Emissive details stay readable through the darkness.
        target = session.interaction_target()
        for door in session.doors:
            can_open = session.requirement_met(door.requirement)
            draw_door_lamp(self.screen, door, camera, t, can_open, door is target)
        if not session.power_on:
            for pos in session.world.layout.emergency_lights:
                draw_emergency_light(self.screen, pos, camera, t)
        draw_enemy_eyes(self.screen, session.enemy, camera)

    def _lights(self):
        session = self.session
        lights = [(session.player.pos, settings.PLAYER_GLOW_RADIUS, settings.PLAYER_GLOW_COLOR)]
        for pickup in session.pickups:
            if not pickup.collected:
                lights.append((pickup.pos, 60, scale_color(PICKUP_COLORS[pickup.kind], 0.45)))
        for door in session.doors:
            color = LIGHT_OPEN if door.is_open else LIGHT_LOCKED
            lights.append((door_lamp_pos(door), 44, scale_color(color, 0.35)))
        generator = session.generator
        if generator.state == generator.ONLINE:
            lights.append((generator.center, 200, (40, 150, 170)))
        elif generator.state == generator.STARTING:
            lights.append((generator.center, 120, scale_color((60, 160, 180), generator.progress)))
        return lights

    def _beam(self):
        player = self.session.player
        return player.pos, player.facing, settings.FLASHLIGHT_RANGE, settings.FLASHLIGHT_COLOR
