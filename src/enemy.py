"""The facility's night watcher: a single enemy with a small state machine."""

import math
from enum import Enum

import pygame

from src import settings


class EnemyState(Enum):
    PATROL = "patrol"
    CHASE = "chase"
    SEARCH = "search"


def _turn_toward(current, target, rate):
    diff = (target - current + math.pi) % math.tau - math.pi
    return current + diff * rate


class Enemy:
    def __init__(self, patrol_points, start_index=0):
        self.patrol_points = [pygame.Vector2(p) for p in patrol_points]
        self.patrol_index = start_index
        self.pos = self.patrol_points[start_index].copy()
        self.size = settings.ENEMY_SIZE
        self.facing = math.pi / 2
        self.state = EnemyState.PATROL
        self.path = []
        self.wait = 0.0
        self.velocity = pygame.Vector2()
        self.suspicion = 0.0
        self.last_known = None
        self.lost_time = 0.0
        self.repath = 0.0

    @property
    def box(self):
        half = self.size / 2
        return self.pos.x - half, self.pos.y - half, self.size, self.size

    def update(self, dt, world, player=None):
        """Advance one tick; returns "spotted" or "lost" when the chase starts or ends."""
        sees = player is not None and self.can_detect(player, world)
        if self.state is EnemyState.PATROL:
            if self._notice(dt, sees):
                self._begin_chase(player)
                return "spotted"
            self._patrol(dt, world)
        elif self.state is EnemyState.CHASE:
            if not self._chase(dt, world, player, sees):
                self._begin_patrol()
                return "lost"
        return None

    # --- perception -----------------------------------------------------

    def can_detect(self, player, world):
        offset = player.pos - self.pos
        dist = offset.length()
        chasing = self.state is EnemyState.CHASE
        if chasing:
            reach = settings.ENEMY_CHASE_SIGHT_RANGE
        elif getattr(player, "flashlight_on", False):
            reach = settings.ENEMY_LIT_SIGHT_RANGE
        else:
            reach = settings.ENEMY_SIGHT_RANGE
        if dist > reach:
            return False
        # Footsteps close by are noticed from any direction; otherwise it must be looking.
        heard = player.moving and dist <= settings.ENEMY_HEARING_RADIUS
        if not (chasing or heard) and dist > 1:
            angle = math.atan2(offset.y, offset.x)
            diff = abs((angle - self.facing + math.pi) % math.tau - math.pi)
            if diff > settings.ENEMY_FOV / 2:
                return False
        return world.line_of_sight(self.pos, player.pos)

    def _notice(self, dt, sees):
        if sees:
            self.suspicion += dt
        else:
            self.suspicion = max(0.0, self.suspicion - dt * 0.5)
        return self.suspicion >= settings.ENEMY_NOTICE_TIME

    # --- movement -------------------------------------------------------

    def _follow_path(self, dt, world, speed):
        """Step along the current path; returns True once the final waypoint is reached."""
        if not self.path:
            self.velocity.update(0, 0)
            return True
        target = self.path[0]
        offset = target - self.pos
        if offset.length() <= settings.ENEMY_WAYPOINT_REACHED:
            self.path.pop(0)
            return not self.path
        self._move(dt, world, offset.normalize() * speed)
        return False

    def _move(self, dt, world, velocity):
        x, y, w, h = self.box
        nx, ny = world.move_box(x, y, w, h, velocity.x * dt, velocity.y * dt)
        self.pos.update(nx + w / 2, ny + h / 2)
        self.velocity = velocity
        goal = math.atan2(velocity.y, velocity.x)
        self.facing = _turn_toward(self.facing, goal, min(1.0, settings.ENEMY_TURN_RATE * dt))

    # --- states ---------------------------------------------------------

    def _begin_chase(self, player):
        self.state = EnemyState.CHASE
        self.last_known = player.pos.copy()
        self.lost_time = 0.0
        self.repath = 0.0
        self.path = []
        self.wait = 0.0

    def _begin_patrol(self):
        self.state = EnemyState.PATROL
        self.suspicion = 0.0
        self.path = []

    def _chase(self, dt, world, player, sees):
        """Pursue the player; returns False once the trail has gone cold."""
        if sees:
            self.last_known = player.pos.copy()
            self.lost_time = 0.0
        else:
            self.lost_time += dt
            if self.lost_time >= settings.ENEMY_LOSE_TIME:
                return False
        speed = settings.ENEMY_CHASE_SPEED
        offset = self.last_known - self.pos
        # Close in directly over the last stretch; grid paths look robotic up close.
        if world.tile_of(self.pos) == world.tile_of(self.last_known):
            if offset.length() > 2:
                self._move(dt, world, offset.normalize() * speed)
            return True
        self.repath -= dt
        if self.repath <= 0 or not self.path:
            self.path = world.find_path(self.pos, self.last_known) or []
            self.repath = settings.ENEMY_REPATH_INTERVAL
        self._follow_path(dt, world, speed)
        return True

    def _patrol(self, dt, world):
        if self.wait > 0:
            self.wait -= dt
            self.velocity.update(0, 0)
            # Sweep the view while standing at a post.
            self.facing += math.sin(self.wait * 2.5) * dt * 1.5
            return
        if not self.path and not self._plan_patrol(world):
            return
        if self._follow_path(dt, world, settings.ENEMY_PATROL_SPEED):
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            self.wait = settings.ENEMY_PATROL_PAUSE

    def _plan_patrol(self, world):
        # Posts behind still-locked doors are skipped until they become reachable.
        for _ in range(len(self.patrol_points)):
            goal = self.patrol_points[self.patrol_index]
            path = world.find_path(self.pos, goal)
            if path is not None:
                self.path = path or [goal.copy()]
                return True
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
        return False
