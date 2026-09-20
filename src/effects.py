"""Particles and other short-lived visual feedback."""

import math
import random

import pygame

from src import settings


class Particles:
    """Fixed-budget particle pool; oldest particles are dropped when it is full."""

    def __init__(self, limit=settings.MAX_PARTICLES, seed=None):
        self.limit = limit
        self.items = []
        self.rng = random.Random(seed)

    def __len__(self):
        return len(self.items)

    def clear(self):
        self.items.clear()

    def spawn(self, pos, velocity, life, color, size, drag=2.2, fade=True):
        self.items.append(
            {
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(velocity),
                "life": life,
                "max_life": life,
                "color": color,
                "size": size,
                "drag": drag,
                "fade": fade,
            }
        )
        if len(self.items) > self.limit:
            del self.items[: len(self.items) - self.limit]

    def burst(self, pos, count, color, speed=120, life=0.6, size=3, direction=None, spread=math.pi):
        for _ in range(count):
            angle = (
                self.rng.uniform(0, math.tau)
                if direction is None
                else direction + self.rng.uniform(-spread, spread)
            )
            magnitude = speed * self.rng.uniform(0.35, 1.0)
            velocity = (math.cos(angle) * magnitude, math.sin(angle) * magnitude)
            jitter = self.rng.uniform(0.6, 1.4)
            self.spawn(pos, velocity, life * jitter, color, self.rng.uniform(size * 0.6, size))

    def update(self, dt):
        alive = []
        for p in self.items:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["pos"] += p["vel"] * dt
            p["vel"] *= max(0.0, 1 - p["drag"] * dt)
            alive.append(p)
        self.items = alive

    def draw(self, surface, camera):
        for p in self.items:
            fraction = p["life"] / p["max_life"]
            radius = max(1, p["size"] * (fraction if p["fade"] else 1))
            color = p["color"]
            if p["fade"]:
                color = tuple(int(c * (0.35 + 0.65 * fraction)) for c in color)
            pygame.draw.circle(surface, color, camera.to_screen(p["pos"]), radius)
