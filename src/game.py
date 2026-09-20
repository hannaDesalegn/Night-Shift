"""Application shell: window, main loop and top-level state machine."""

import math
from enum import Enum, auto

import pygame

from src import controls, settings
from src.audio import Audio
from src.effects import Dust, Fade, FloatingText, Overlays, Particles, ScreenShake
from src.entities import Generator
from src.hud import HUD
from src.renderer import PICKUP_COLORS, Camera, Scene
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
        self.hud = HUD(self.fonts, size)
        self.audio = Audio()
        self.particles = Particles()
        self.shake = ScreenShake()
        self.popups = FloatingText()
        self.dust = Dust()
        self.fade = Fade(size)
        self.pending = None
        self.pending_delay = 0.0
        self.overlays = Overlays(size)
        self.main_menu = Menu([("start", "Start Game"), ("controls", "Controls"), ("quit", "Quit")])
        self.pause_menu = Menu(
            [("resume", "Resume"), ("restart", "Restart"), ("menu", "Main Menu")]
        )
        self.result_menu = Menu([("restart", "Restart"), ("menu", "Main Menu")])
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

    def transition_to(self, action, delay=0.0):
        """Fade out, run action, then fade back in."""
        self.pending = action
        self.pending_delay = delay

    def _update_transition(self, dt):
        if self.pending is not None:
            if self.pending_delay > 0:
                self.pending_delay -= dt
            else:
                self.fade.cover()
        self.fade.update(dt)
        if self.pending is not None and self.fade.covered:
            action, self.pending = self.pending, None
            action()
            self.fade.reveal()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(settings.FPS) / 1000, settings.MAX_FRAME_TIME)
            self.handle_events()
            self.update(dt)
            self.draw()
        self.audio.shutdown()
        pygame.quit()

    # --- state transitions ------------------------------------------------

    def start_run(self):
        self.session = Session()
        self.hud.clear()
        self.particles.clear()
        self.shake.reset()
        self.popups.clear()
        self.overlays.reset()
        self.scene.attach(self.session)
        self.camera.snap(self.session.player.pos)
        self.audio.start_ambience()
        self.state = State.PLAYING

    def pause(self):
        self.pause_menu.reset()
        self.state = State.PAUSED

    def resume(self):
        self.state = State.PLAYING

    def finish_run(self):
        self.result_menu.reset()
        self.state = State.VICTORY if self.session.outcome == "escaped" else State.GAME_OVER

    def open_menu(self):
        self.audio.stop_ambience()
        self.main_menu.reset()
        self.result_menu = Menu([("restart", "Restart"), ("menu", "Main Menu")])
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
            State.GAME_OVER: self._result_event,
            State.VICTORY: self._result_event,
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
            self.transition_to(self.start_run)
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
            self.transition_to(self.start_run)
            return
        choice = self.pause_menu.handle(event)
        if choice == "resume":
            self.resume()
        elif choice == "restart":
            self.transition_to(self.start_run)
        elif choice == "menu":
            self.transition_to(self.open_menu)

    def _result_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in controls.RESTART:
                self.transition_to(self.start_run)
                return
            if event.key in controls.PAUSE:
                self.transition_to(self.open_menu)
                return
        choice = self.result_menu.handle(event)
        if choice == "restart":
            self.transition_to(self.start_run)
        elif choice == "menu":
            self.transition_to(self.open_menu)

    # --- update -----------------------------------------------------------

    def update(self, dt):
        self.time += dt
        self._update_transition(dt)
        if self.state is State.PLAYING:
            snapshot = controls.read_input(pygame.key.get_pressed(), self.key_events)
            events = self.session.update(dt, snapshot)
            self.handle_session_events(events)
            self.hud.update(dt)
            self.particles.update(dt)
            self.popups.update(dt)
            self.dust.update(dt, pygame.Rect(self.camera.offset, self.screen.get_size()))
            self.shake.update(dt)
            self.overlays.update(dt)
            self.camera.shake = self.shake.offset(self.time)
            self._generator_sparks(dt)
            self._dread_wisps(dt)
            self.camera.follow(self.session.player.pos, dt)
            if self.session.outcome and self.pending is None:
                self.transition_to(self.finish_run, delay=settings.END_OF_RUN_DELAY)
        elif self.state is State.MENU:
            self._drift_camera(dt)

    def handle_session_events(self, events):
        """Turn gameplay events into presentation: messages, particles and audio."""
        for event in events:
            if event.kind == "score":
                self._score_popup(event)
                continue
            self.hud.notify(event.text)
            self._spawn_effect(event)

    SOUNDS = {
        "pickup": "pickup",
        "door_open": "door_open",
        "door_locked": "door_locked",
        "generator_start": "generator_start",
        "generator_denied": "door_locked",
        "power_on": "power_on",
        "damage": "damage",
        "enemy_spotted": "spotted",
        "escaped": "escape",
        "flashlight_on": "click",
        "flashlight_off": "click",
        "flashlight_dead": "empty",
        "flashlight_empty": "empty",
        "caught": "damage",
    }

    def _score_popup(self, event):
        pos = event.pos if event.pos.length_squared() else self.session.player.pos
        positive = not event.text.startswith("-")
        color = (150, 230, 170) if positive else (235, 100, 90)
        self.popups.add(pos + (0, -26), event.text, color)

    def _spawn_effect(self, event):
        particles, pos = self.particles, event.pos
        if event.kind == "pickup" and event.item == "battery":
            self.audio.play("battery")
        elif event.kind in self.SOUNDS:
            self.audio.play(self.SOUNDS[event.kind])
        if event.kind == "pickup":
            particles.burst(pos, 22, PICKUP_COLORS[event.item], speed=150, life=0.7, size=4)
        elif event.kind == "door_open":
            particles.burst(pos, 16, (150, 152, 160), speed=120, life=0.8, size=3)
        elif event.kind == "door_locked":
            particles.burst(pos, 10, (235, 80, 60), speed=90, life=0.4, size=3)
            self.shake.add(0.15)
        elif event.kind == "enemy_spotted":
            self.shake.add(0.3)
        elif event.kind == "generator_start":
            particles.burst(pos, 18, (255, 200, 90), speed=170, life=0.5, size=3)
        elif event.kind == "power_on":
            particles.burst(pos, 60, (120, 225, 240), speed=280, life=1.1, size=5)
            self.shake.add(0.45)
            self.overlays.hit(0.6, color=(120, 210, 235))
        elif event.kind == "damage":
            particles.burst(pos, 26, (220, 60, 50), speed=190, life=0.6, size=4)
            self.shake.add(0.7)
            self.overlays.hit(0.9)
        elif event.kind == "escaped":
            particles.burst(pos, 40, (140, 230, 170), speed=200, life=1.0, size=4)

    def _dread_wisps(self, dt):
        """Wisps drift off the watcher when it is close, hinting at it through walls."""
        enemy, player = self.session.enemy, self.session.player
        distance = enemy.pos.distance_to(player.pos)
        if distance > settings.DREAD_RADIUS:
            return
        nearness = 1 - distance / settings.DREAD_RADIUS
        if self.particles.rng.random() > dt * 14 * nearness:
            return
        toward_player = (player.pos - enemy.pos).angle_to(pygame.Vector2(1, 0))
        self.particles.burst(
            enemy.pos,
            1,
            (120, 60, 150),
            speed=40 + 60 * nearness,
            life=0.9,
            size=4,
            direction=-math.radians(toward_player),
            spread=0.8,
        )

    def _generator_sparks(self, dt):
        """Occasional sparks while the generator is spinning up."""
        generator = self.session.generator
        if generator.state != Generator.STARTING:
            return
        if self.particles.rng.random() < dt * 22:
            edge = generator.rect.center + pygame.Vector2(
                self.particles.rng.uniform(-40, 40), self.particles.rng.uniform(-30, 30)
            )
            self.particles.burst(edge, 3, (255, 190, 80), speed=90, life=0.35, size=3)

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
        underlay = self.dust.draw if self.state is not State.MENU else None
        self.scene.draw(self.screen, self.session, self.camera, self.time, underlay)
        self.particles.draw(self.screen, self.camera)
        self.popups.draw(self.screen, self.camera, self.fonts.label)
        if self.state in (State.PLAYING, State.PAUSED):
            self.overlays.draw(self.screen, self.session, self.time)
            self.hud.draw(self.screen, self.session, self.time)
        if self.state is State.MENU:
            self.screens.dim(self.screen)
            self.screens.draw_menu(self.screen, self.main_menu, self.time, self.show_controls)
        elif self.state is State.PAUSED:
            self.screens.dim(self.screen)
            self.screens.draw_pause(self.screen, self.pause_menu, self.time)
        elif self.state in (State.GAME_OVER, State.VICTORY):
            self.screens.dim(self.screen)
            self.screens.draw_result(self.screen, self.session, self.result_menu, self.time)
        self.fade.draw(self.screen)
        pygame.display.flip()
