import math

import pygame

from src.settings import TILE
from src.world import FACILITY_MAP, World


def test_map_rows_have_equal_width():
    assert len({len(row) for row in FACILITY_MAP}) == 1


def test_layout_contains_required_markers():
    layout = World().layout
    kinds = [kind for kind, _ in layout.pickups]
    assert layout.player_start is not None
    assert "keycard" in kinds and "component" in kinds
    assert layout.door_tiles["D"] and layout.door_tiles["X"]
    assert len(layout.generator_tiles) == 4
    assert len(layout.patrol_points) >= 3
    assert layout.escape_tiles


def test_move_box_stops_flush_against_wall():
    world = World()
    # Start one tile right of the west wall and push left hard.
    x, y = world.move_box(TILE + 4, TILE * 12, 28, 28, -30, 0)
    assert x == TILE


def test_move_box_slides_along_wall():
    world = World()
    x, y = world.move_box(TILE + 2, TILE * 12, 28, 28, -10, 5)
    assert x == TILE and y == TILE * 12 + 5


def test_closed_tiles_block_movement():
    world = World()
    door = world.layout.door_tiles["D"]
    world.set_closed(door, True)
    assert world.is_solid(*door[0])
    world.set_closed(door, False)
    assert not world.is_solid(*door[0])


def test_line_of_sight_blocked_by_wall():
    world = World()
    office = pygame.Vector2(5.5 * TILE, 4.5 * TILE)
    storage = pygame.Vector2(18.5 * TILE, 4.5 * TILE)
    assert not world.line_of_sight(office, storage)
    corridor_a = pygame.Vector2(2.5 * TILE, 12.5 * TILE)
    corridor_b = pygame.Vector2(40.5 * TILE, 12.5 * TILE)
    assert world.line_of_sight(corridor_a, corridor_b)


def test_cast_ray_hits_wall_at_expected_distance():
    world = World()
    origin = pygame.Vector2(5.5 * TILE, 12.5 * TILE)
    # Straight up from the corridor into the office's south wall.
    dist = world.cast_ray(origin, -math.pi / 2, 1000)
    assert math.isclose(dist, 2.5 * TILE, abs_tol=0.01)


def test_find_path_routes_around_walls():
    world = World()
    start = world.layout.player_start
    goal = pygame.Vector2(5.5 * TILE, 4.5 * TILE)
    path = world.find_path(start, goal)
    assert path is not None
    assert all(not world.is_solid(*world.tile_of(p)) for p in path)
    assert world.tile_of(path[-1]) == world.tile_of(goal)


def test_find_path_respects_closed_doors():
    world = World()
    world.set_closed(world.layout.door_tiles["D"], True)
    component = next(pos for kind, pos in world.layout.pickups if kind == "component")
    assert world.find_path(world.layout.player_start, component) is None


def test_room_lookup():
    world = World()
    assert world.room_at(world.layout.player_start) == "LOBBY"
