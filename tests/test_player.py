import math

import pygame

from src import settings
from src.controls import movement_vector
from src.player import Player
from src.settings import TILE
from src.world import World

DT = 1 / 60


def run(player, world, move, seconds):
    for _ in range(int(seconds / DT)):
        player.update(DT, pygame.Vector2(move), world)


class FakePressed:
    def __init__(self, *keys):
        self.keys = set(keys)

    def __getitem__(self, key):
        return key in self.keys


def test_diagonal_movement_is_normalized():
    move = movement_vector(FakePressed(pygame.K_w, pygame.K_d))
    assert math.isclose(move.length(), 1.0)


def test_arrow_keys_and_wasd_are_equivalent():
    assert movement_vector(FakePressed(pygame.K_LEFT)) == movement_vector(FakePressed(pygame.K_a))


def test_player_reaches_top_speed_on_open_floor():
    world = World()
    player = Player(world.layout.player_start)
    run(player, world, (1, 0), 0.4)
    assert player.velocity.x > settings.PLAYER_SPEED * 0.95


def test_player_cannot_pass_through_walls():
    world = World()
    player = Player(world.layout.player_start)
    run(player, world, (0, 1), 3)
    # The lobby's south wall starts at row 29.
    assert player.rect.bottom <= 29 * TILE
    run(player, world, (-1, 0), 3)
    assert player.rect.left >= TILE


def test_player_slides_along_wall_when_moving_diagonally():
    world = World()
    player = Player(world.layout.player_start)
    run(player, world, (0, 1), 3)
    x_before = player.pos.x
    run(player, world, pygame.Vector2(1, 1).normalize(), 0.5)
    assert player.pos.x > x_before + 40


def test_movement_is_frame_rate_independent():
    world = World()
    fast, slow = Player(world.layout.player_start), Player(world.layout.player_start)
    for _ in range(120):
        fast.update(1 / 120, pygame.Vector2(1, 0), world)
    for _ in range(30):
        slow.update(1 / 30, pygame.Vector2(1, 0), world)
    assert abs(fast.pos.x - slow.pos.x) < 12


def test_player_stops_when_input_released():
    world = World()
    player = Player(world.layout.player_start)
    run(player, world, (1, 0), 0.3)
    run(player, world, (0, 0), 1)
    assert player.velocity.length() == 0


def test_facing_turns_toward_movement():
    world = World()
    player = Player(world.layout.player_start)
    run(player, world, (1, 0), 1)
    assert abs(math.remainder(player.facing, math.tau)) < 0.05
