"""Application shell: window, main loop and top-level state machine."""

import math
from enum import Enum, auto

import pygame

from src import controls, settings
from src.renderer import Camera, Scene
from src.session import Session
from src.ui import Fonts, Menu, Screens


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
        size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()
        self.screens = Screens(self.fonts, size)
        self.main_menu = Menu([("start", "Start Game"), ("controls", "Controls"), ("quit", "Quit")])
        self.pause_menu = Menu(
            [("resume", "Resume"), ("restart", "Restart"), ("menu", "Main Menu")]
        )
        self.show_controls = False
        self.time = 0.0
        self.key_events = []
        self.running = True
        self.session = Session()
        self.scene = Scene(self.session.world, self.fonts)
        self.scene.attach(self.session)
        self.camera = Camera(self.session.world.pixel_size)
        self.camera.snap(self.session.player.pos)
        self.state = State.MENU

    def run(self):
        while self.running:
            dt = min(self.clock.tick(settings.FPS) / 1000, settings.MAX_FRAME_TIME)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    # --- state transitions ------------------------------------------------

    def start_run(self):
        self.session = Session()
        self.scene.attach(self.session)
        self.camera.snap(self.session.player.pos)
        self.state = State.PLAYING

    def pause(self):
        self.pause_menu.reset()
        self.state = State.PAUSED

    def resume(self):
        self.state = State.PLAYING

    def open_menu(self):
        self.main_menu.reset()
        self.show_controls = False
        self.state = State.MENU

    # --- input ------------------------------------------------------------

    def handle_events(self):
        self.key_events = []
        for event in pygame.event.get():
            self.handle_event(event)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        handlers = {
            State.MENU: self._menu_event,
            State.PLAYING: self._playing_event,
            State.PAUSED: self._pause_event,
        }
        handlers[self.state](event)

    def _menu_event(self, event):
        if self.show_controls:
            closing_key = (
                event.type == pygame.KEYDOWN and event.key in controls.PAUSE + controls.CONFIRM
            )
            if closing_key or event.type == pygame.MOUSEBUTTONDOWN:
                self.show_controls = False
            return
        choice = self.main_menu.handle(event)
        if choice == "start":
            self.start_run()
        elif choice == "controls":
            self.show_controls = True
        elif choice == "quit":
            self.running = False

    def _playing_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in controls.PAUSE:
            self.pause()
        else:
            self.key_events.append(event)

    def _pause_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in controls.PAUSE:
            self.resume()
            return
        if event.type == pygame.KEYDOWN and event.key in controls.RESTART:
            self.start_run()
            return
        choice = self.pause_menu.handle(event)
        if choice == "resume":
            self.resume()
        elif choice == "restart":
            self.start_run()
        elif choice == "menu":
            self.open_menu()

    # --- update -----------------------------------------------------------

    def update(self, dt):
        self.time += dt
        if self.state is State.PLAYING:
            snapshot = controls.read_input(pygame.key.get_pressed(), self.key_events)
            self.session.update(dt, snapshot)
            self.camera.follow(self.session.player.pos, dt)
            if self.session.outcome:
                self.open_menu()
        elif self.state is State.MENU:
            self._drift_camera(dt)

    def _drift_camera(self, dt):
        """Slow pan across the facility behind the title screen."""
        width, height = self.session.world.pixel_size
        target = pygame.Vector2(
            width / 2 + math.sin(self.time * 0.05) * width * 0.35,
            height / 2 + math.sin(self.time * 0.035) * height * 0.3,
        )
        self.camera.follow(target, dt * 0.2)

    # --- draw -------------------------------------------------------------

    def draw(self):
        self.screen.fill(settings.BG_COLOR)
        self.scene.draw(self.screen, self.session, self.camera, self.time)
        if self.state is State.MENU:
            self.screens.dim(self.screen)
            self.screens.draw_menu(self.screen, self.main_menu, self.time, self.show_controls)
        elif self.state is State.PAUSED:
            self.screens.dim(self.screen)
            self.screens.draw_pause(self.screen, self.pause_menu, self.time)
        pygame.display.flip()
