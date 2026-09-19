from src.enemy import Enemy, EnemyState
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
