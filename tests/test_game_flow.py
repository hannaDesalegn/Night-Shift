import pygame
import pytest

from src.game import Game, State


@pytest.fixture
def game():
    instance = Game()
    yield instance
    pygame.quit()


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def test_game_opens_on_main_menu(game):
    assert game.state is State.MENU


def test_start_game_from_menu(game):
    game.handle_event(key(pygame.K_RETURN))
    assert game.state is State.PLAYING


def test_controls_screen_opens_and_closes(game):
    game.handle_event(key(pygame.K_DOWN))
    game.handle_event(key(pygame.K_RETURN))
    assert game.show_controls
    game.handle_event(key(pygame.K_ESCAPE))
    assert not game.show_controls and game.state is State.MENU


def test_quit_from_menu(game):
    game.handle_event(key(pygame.K_UP))
    game.handle_event(key(pygame.K_RETURN))
    assert not game.running


def test_pause_and_resume(game):
    game.start_run()
    game.handle_event(key(pygame.K_ESCAPE))
    assert game.state is State.PAUSED
    before = game.session.time_left
    game.update(0.5)
    assert game.session.time_left == before
    game.handle_event(key(pygame.K_ESCAPE))
    assert game.state is State.PLAYING


def test_restart_from_pause_creates_fresh_run(game):
    game.start_run()
    old = game.session
    game.update(0.5)
    game.handle_event(key(pygame.K_ESCAPE))
    game.handle_event(key(pygame.K_r))
    assert game.state is State.PLAYING
    assert game.session is not old
    assert game.session.elapsed == 0


def test_pause_menu_returns_to_main_menu(game):
    game.start_run()
    game.handle_event(key(pygame.K_ESCAPE))
    game.handle_event(key(pygame.K_UP))
    game.handle_event(key(pygame.K_RETURN))
    assert game.state is State.MENU


def test_every_state_draws_without_error(game):
    game.start_run()
    for state in (State.MENU, State.PLAYING, State.PAUSED):
        game.state = state
        game.draw()
