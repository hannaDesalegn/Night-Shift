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


def test_damage_reduces_health_and_grants_invulnerability():
    player = Player((100, 100))
    assert player.take_damage(25)
    assert player.health == settings.PLAYER_MAX_HEALTH - 25
    assert player.invulnerable > 0


def test_invulnerability_blocks_repeated_hits():
    player = Player((100, 100))
    player.take_damage(25)
    assert not player.take_damage(25)
    assert player.health == settings.PLAYER_MAX_HEALTH - 25


def test_invulnerability_expires():
    world = World()
    player = Player(world.layout.player_start)
    player.take_damage(25)
    run(player, world, (0, 0), settings.PLAYER_INVULNERABLE_TIME + 0.1)
    assert player.take_damage(25)
    assert player.health == settings.PLAYER_MAX_HEALTH - 50


def test_damage_knocks_player_away_from_source():
    player = Player((100, 100))
    player.take_damage(10, source=(80, 100))
    assert player.velocity.x > 0


def test_health_never_goes_negative():
    player = Player((100, 100))
    player.take_damage(settings.PLAYER_MAX_HEALTH * 3)
    assert player.health == 0 and not player.alive


def drain(player, seconds):
    for _ in range(int(seconds / DT)):
        status = player.update_flashlight(DT)
        if status:
            yield status


def test_flashlight_drains_while_on_and_recharges_while_off():
    player = Player((0, 0))
    list(drain(player, 10))
    drained = player.energy
    assert drained < settings.FLASHLIGHT_MAX_ENERGY
    player.toggle_flashlight()
    list(drain(player, 10))
    assert player.energy > drained


def test_flashlight_warns_once_when_low():
    player = Player((0, 0))
    player.energy = settings.FLASHLIGHT_LOW + 1
    assert list(drain(player, 3)) == ["low"]


def test_empty_flashlight_switches_off_and_cannot_restart_immediately():
    player = Player((0, 0))
    player.energy = 0.5
    assert list(drain(player, 1)) == ["empty"]
    assert not player.flashlight_on
    assert not player.toggle_flashlight()
    assert not player.flashlight_on


def test_flashlight_restarts_after_recovering():
    player = Player((0, 0))
    player.energy = 0.1
    list(drain(player, 0.5))
    player.recharge(settings.FLASHLIGHT_RESTART_ENERGY)
    assert player.toggle_flashlight()
    assert player.flashlight_on


def test_beam_weakens_with_energy():
    full, weak = Player((0, 0)), Player((0, 0))
    weak.energy = settings.FLASHLIGHT_LOW + 5
    assert weak.beam_intensity(0.0) < full.beam_intensity(0.0)


def test_beam_is_dark_when_off():
    player = Player((0, 0))
    player.toggle_flashlight()
    assert player.beam_intensity(1.0) == 0.0
