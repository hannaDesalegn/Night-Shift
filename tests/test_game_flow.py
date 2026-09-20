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


def play_until_outcome(game, outcome):
    game.start_run()
    game.session.finish(outcome)
    game.update(1 / 60)


def test_escaping_shows_the_victory_screen(game):
    play_until_outcome(game, "escaped")
    assert game.state is State.VICTORY
    game.draw()


def test_being_caught_shows_the_game_over_screen(game):
    play_until_outcome(game, "caught")
    assert game.state is State.GAME_OVER
    game.draw()


def test_timeout_shows_the_game_over_screen(game):
    play_until_outcome(game, "timeout")
    assert game.state is State.GAME_OVER


def test_restart_key_starts_a_new_run_from_results(game):
    play_until_outcome(game, "caught")
    game.handle_event(key(pygame.K_r))
    assert game.state is State.PLAYING
    assert game.session.outcome is None


def test_results_screen_returns_to_menu(game):
    play_until_outcome(game, "escaped")
    game.handle_event(key(pygame.K_ESCAPE))
    assert game.state is State.MENU
