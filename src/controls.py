"""Keyboard bindings and per-frame input snapshot."""

from dataclasses import dataclass

import pygame

MOVE_UP = (pygame.K_w, pygame.K_UP)
MOVE_DOWN = (pygame.K_s, pygame.K_DOWN)
MOVE_LEFT = (pygame.K_a, pygame.K_LEFT)
MOVE_RIGHT = (pygame.K_d, pygame.K_RIGHT)
INTERACT = (pygame.K_e,)
FLASHLIGHT = (pygame.K_f,)
PAUSE = (pygame.K_ESCAPE, pygame.K_p)
RESTART = (pygame.K_r,)
CONFIRM = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


@dataclass
class InputState:
    move: pygame.Vector2
    interact: bool = False
    toggle_flashlight: bool = False


def _held(pressed, keys):
    return any(pressed[k] for k in keys)


def movement_vector(pressed):
    """Normalized movement direction so diagonals are not faster than straight lines."""
    move = pygame.Vector2(
        _held(pressed, MOVE_RIGHT) - _held(pressed, MOVE_LEFT),
        _held(pressed, MOVE_DOWN) - _held(pressed, MOVE_UP),
    )
    if move.length_squared():
        move.normalize_ip()
    return move


def read_input(pressed, key_events):
    keys = {event.key for event in key_events}
    return InputState(
        move=movement_vector(pressed),
        interact=bool(keys & set(INTERACT)),
        toggle_flashlight=bool(keys & set(FLASHLIGHT)),
    )
