"""The night guard: movement, health and inventory."""

import math

import pygame

from src import settings


def _approach_angle(current, target, rate):
    diff = (target - current + math.pi) % math.tau - math.pi
    return current + diff * rate


class Player:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2()
        self.size = settings.PLAYER_SIZE
        self.facing = -math.pi / 2
        self.health = settings.PLAYER_MAX_HEALTH
        self.inventory = set()
        # Accumulated distance, drives the walk animation.
        self.stride = 0.0

    @property
    def box(self):
        half = self.size / 2
        return self.pos.x - half, self.pos.y - half, self.size, self.size

    @property
    def rect(self):
        return pygame.Rect(*self.box)

    @property
    def alive(self):
        return self.health > 0

    @property
    def moving(self):
        return self.velocity.length_squared() > 400

    def update(self, dt, move, world):
        target = move * settings.PLAYER_SPEED
        self.velocity += (target - self.velocity) * min(1.0, settings.PLAYER_ACCEL * dt)
        if not move and self.velocity.length_squared() < 4:
            self.velocity.update(0, 0)

        x, y, w, h = self.box
        before = self.pos.copy()
        nx, ny = world.move_box(x, y, w, h, self.velocity.x * dt, self.velocity.y * dt)
        self.pos.update(nx + w / 2, ny + h / 2)
        moved = self.pos - before
        if dt:
            # Drop velocity into walls so the player does not "stick" when turning away.
            self.velocity.update(moved.x / dt, moved.y / dt)
        self.stride += moved.length()

        if move:
            goal = math.atan2(move.y, move.x)
            rate = min(1.0, settings.PLAYER_TURN_RATE * dt)
            self.facing = _approach_angle(self.facing, goal, rate)

    def has(self, item):
        return item in self.inventory
