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
        self.invulnerable = 0.0
        self.flashlight_on = True
        self.energy = settings.FLASHLIGHT_MAX_ENERGY
        self.depleted = False
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
        self.invulnerable = max(0.0, self.invulnerable - dt)
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

    # --- flashlight ------------------------------------------------------

    @property
    def energy_fraction(self):
        return self.energy / settings.FLASHLIGHT_MAX_ENERGY

    @property
    def flashlight_low(self):
        return self.energy <= settings.FLASHLIGHT_LOW

    def toggle_flashlight(self):
        """Returns True if the flashlight changed state."""
        if self.flashlight_on:
            self.flashlight_on = False
            return True
        if self.depleted:
            return False
        self.flashlight_on = True
        return True

    def update_flashlight(self, dt):
        """Drain or recharge; returns "empty" or "low" on the frame a threshold is crossed."""
        before = self.energy
        if self.flashlight_on:
            self.energy = max(0.0, self.energy - settings.FLASHLIGHT_DRAIN * dt)
        else:
            self.energy = min(
                settings.FLASHLIGHT_MAX_ENERGY, self.energy + settings.FLASHLIGHT_RECHARGE * dt
            )
        if self.depleted and self.energy >= settings.FLASHLIGHT_RESTART_ENERGY:
            self.depleted = False
        if self.flashlight_on and self.energy <= 0:
            self.flashlight_on = False
            self.depleted = True
            return "empty"
        if before > settings.FLASHLIGHT_LOW >= self.energy:
            return "low"
        return None

    def recharge(self, amount):
        self.energy = min(settings.FLASHLIGHT_MAX_ENERGY, self.energy + amount)
        if self.energy >= settings.FLASHLIGHT_RESTART_ENERGY:
            self.depleted = False

    def beam_intensity(self, t):
        """0..1 light output; sputters irregularly once the battery is low."""
        if not self.flashlight_on:
            return 0.0
        level = 0.6 + 0.4 * self.energy_fraction
        if self.flashlight_low:
            noise = math.sin(t * 37.0) + math.sin(t * 23.3 + 1.7) + math.sin(t * 5.1)
            if noise > 1.6:
                level *= 0.2
        return level

    def take_damage(self, amount, source=None):
        """Apply a hit unless still recovering from the last one; returns True if it landed."""
        if self.invulnerable > 0 or not self.alive:
            return False
        self.health = max(0, self.health - amount)
        self.invulnerable = settings.PLAYER_INVULNERABLE_TIME
        if source is not None:
            push = self.pos - pygame.Vector2(source)
            if push.length_squared() < 1:
                push = pygame.Vector2(0, -1)
            self.velocity = push.normalize() * settings.PLAYER_KNOCKBACK
        return True

    def has(self, item):
        return item in self.inventory
