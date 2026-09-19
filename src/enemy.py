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

    @property
    def box(self):
        half = self.size / 2
        return self.pos.x - half, self.pos.y - half, self.size, self.size

    def update(self, dt, world):
        if self.state is EnemyState.PATROL:
            self._patrol(dt, world)

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
