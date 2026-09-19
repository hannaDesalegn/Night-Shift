import math

from src.enemy import Enemy, EnemyState
from src.player import Player
from src.settings import TILE
from src.world import World

DT = 1 / 60


def simulate(enemy, world, seconds, **kwargs):
    for _ in range(int(seconds / DT)):
        enemy.update(DT, world, **kwargs)


def test_enemy_starts_patrolling_at_its_post():
    world = World()
    enemy = Enemy(world.layout.patrol_points, start_index=2)
    assert enemy.state is EnemyState.PATROL
    assert enemy.pos == world.layout.patrol_points[2]


def test_patrol_visits_posts_in_order():
    world = World()
    enemy = Enemy(world.layout.patrol_points)
    visited = []
    for _ in range(int(90 / DT)):
        enemy.update(DT, world)
        if enemy.wait > 0 and (not visited or visited[-1] != enemy.patrol_index):
            visited.append(enemy.patrol_index)
    assert visited[:3] == [1, 2, 3]


def test_patrol_skips_posts_behind_locked_doors():
    world = World()
    world.set_closed(world.layout.door_tiles["D"], True)
    points = world.layout.patrol_points
    maintenance = len(points) - 1
    enemy = Enemy(points, start_index=maintenance - 1)
    enemy.wait = 0
    enemy.patrol_index = maintenance
    assert enemy._plan_patrol(world)
    assert enemy.patrol_index == 0


def test_patrolling_enemy_never_enters_solid_tiles():
    world = World()
    enemy = Enemy(world.layout.patrol_points)
    for _ in range(int(60 / DT)):
        enemy.update(DT, world)
        x, y, w, h = enemy.box
        assert not world.box_blocked(x, y, w, h)


def corridor_setup(distance, facing_player=True):
    """Enemy in the open corridor with the player straight east of it."""
    world = World()
    enemy = Enemy(world.layout.patrol_points)
    enemy.pos.update(10 * TILE, 12.5 * TILE)
    enemy.facing = 0.0 if facing_player else math.pi
    enemy.wait = 100  # hold position while perception is tested
    player = Player((enemy.pos.x + distance, enemy.pos.y))
    return world, enemy, player


def test_enemy_sees_player_in_front():
    world, enemy, player = corridor_setup(200)
    assert enemy.can_detect(player, world)


def test_enemy_ignores_quiet_player_behind_it():
    world, enemy, player = corridor_setup(200, facing_player=False)
    assert not enemy.can_detect(player, world)


def test_enemy_hears_moving_player_close_behind():
    world, enemy, player = corridor_setup(60, facing_player=False)
    player.velocity.update(150, 0)
    assert enemy.can_detect(player, world)


def test_flashlight_extends_detection_range():
    world, enemy, player = corridor_setup(400)
    assert not enemy.can_detect(player, world)
    player.flashlight_on = True
    assert enemy.can_detect(player, world)


def test_walls_block_sight():
    world = World()
    enemy = Enemy(world.layout.patrol_points)
    enemy.pos.update(5.5 * TILE, 11.5 * TILE)
    enemy.facing = -math.pi / 2
    player = Player((5.5 * TILE, 7.5 * TILE))  # inside the office, behind its wall
    assert not enemy.can_detect(player, world)


def test_brief_glimpse_does_not_trigger_chase():
    world, enemy, player = corridor_setup(200)
    enemy.update(DT, world, player)
    assert enemy.state is EnemyState.PATROL


def test_sustained_sight_starts_chase():
    world, enemy, player = corridor_setup(200)
    alerts = [enemy.update(DT, world, player) for _ in range(int(0.5 / DT))]
    assert "spotted" in alerts
    assert enemy.state is EnemyState.CHASE


def test_chasing_enemy_closes_distance():
    world, enemy, player = corridor_setup(250)
    simulate(enemy, world, 0.5, player=player)
    start = enemy.pos.distance_to(player.pos)
    simulate(enemy, world, 0.8, player=player)
    assert enemy.pos.distance_to(player.pos) < start - 80
