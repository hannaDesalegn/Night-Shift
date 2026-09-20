"""Particles and other short-lived visual feedback."""

import functools
import math
import random

import pygame

from src import settings
from src.enemy import EnemyState


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


class ScreenShake:
    """Trauma-based shake: events add trauma, the offset scales with its square."""

    def __init__(self, seed=None):
        self.trauma = 0.0
        self.rng = random.Random(seed)
        self.seeds = [self.rng.uniform(0, 100) for _ in range(2)]

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def reset(self):
        self.trauma = 0.0

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - settings.SHAKE_DECAY * dt)

    def offset(self, t):
        if self.trauma <= 0:
            return pygame.Vector2()
        magnitude = settings.SHAKE_MAX * self.trauma**2
        return pygame.Vector2(
            math.sin((t + self.seeds[0]) * 47) * magnitude,
            math.sin((t + self.seeds[1]) * 39) * magnitude,
        )


@functools.lru_cache(maxsize=8)
def vignette(size, color, strength=200):
    """Colored edge glow used for damage and danger feedback."""
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    steps = 26
    for i in range(steps):
        inset = int(i * min(width, height) * 0.30 / steps)
        alpha = int(strength * (1 - i / steps) ** 3.0)
        rect = (inset, inset, width - 2 * inset, height - 2 * inset)
        pygame.draw.rect(surface, (*color, alpha), rect, 14)
    return surface


class Overlays:
    """Full-screen tints: a damage flash plus steady low-health and hunted warnings."""

    def __init__(self, size):
        self.size = size
        self.flash = 0.0
        self.flash_color = (220, 40, 30)

    def hit(self, strength=1.0, color=(220, 40, 30)):
        self.flash = min(1.0, self.flash + strength)
        self.flash_color = color

    def reset(self):
        self.flash = 0.0

    def update(self, dt):
        self.flash = max(0.0, self.flash - dt * 2.0)

    def draw(self, surface, session, t):
        player = session.player
        if player.health <= settings.PLAYER_MAX_HEALTH * 0.34:
            pulse = 0.35 + 0.25 * math.sin(t * 5)
            self._blit(surface, (170, 30, 25), int(120 * pulse))
        elif session.enemy.state is EnemyState.CHASE:
            pulse = 0.4 + 0.2 * math.sin(t * 7)
            self._blit(surface, (110, 30, 120), int(90 * pulse))
        if self.flash > 0:
            self._blit(surface, self.flash_color, int(150 * self.flash))

    def _blit(self, surface, color, alpha):
        layer = vignette(self.size, color)
        layer.set_alpha(alpha)
        surface.blit(layer, (0, 0))


class FloatingText:
    """Score popups that drift upward and fade."""

    LIFE = 1.1

    def __init__(self):
        self.items = []

    def add(self, pos, text, color):
        self.items.append(
            {"pos": pygame.Vector2(pos), "text": text, "life": self.LIFE, "color": color}
        )

    def clear(self):
        self.items.clear()

    def update(self, dt):
        for item in self.items:
            item["life"] -= dt
            item["pos"].y -= 34 * dt
        self.items = [item for item in self.items if item["life"] > 0]

    def draw(self, surface, camera, font):
        for item in self.items:
            image = font.render(item["text"], True, item["color"])
            image.set_alpha(int(255 * min(1.0, item["life"] / 0.4)))
            surface.blit(image, image.get_rect(center=camera.to_screen(item["pos"])))


class Dust:
    """Slow motes that drift through the view; they only show up inside lit areas."""

    def __init__(self, count=70, seed=5):
        self.rng = random.Random(seed)
        self.count = count
        self.motes = []

    def _spawn(self, view):
        return {
            "pos": pygame.Vector2(
                self.rng.uniform(view.left, view.right), self.rng.uniform(view.top, view.bottom)
            ),
            "vel": pygame.Vector2(self.rng.uniform(-9, 9), self.rng.uniform(-14, -3)),
            "size": self.rng.uniform(1.0, 2.2),
        }

    def update(self, dt, view):
        while len(self.motes) < self.count:
            self.motes.append(self._spawn(view))
        for mote in self.motes:
            mote["pos"] += mote["vel"] * dt
            # Recycle motes that drift out of the visible area.
            if not view.inflate(80, 80).collidepoint(mote["pos"]):
                mote.update(self._spawn(view))

    def draw(self, surface, camera):
        for mote in self.motes:
            pygame.draw.circle(
                surface, (150, 150, 160), camera.to_screen(mote["pos"]), mote["size"]
            )
