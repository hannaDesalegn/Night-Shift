"""Interactive props placed in the facility."""

from dataclasses import dataclass, field

import pygame

from src import settings
from src.settings import TILE
from src.utils import approach

PICKUP_NAMES = {
    "keycard": "Maintenance keycard",
    "component": "Generator fuse cell",
    "battery": "Flashlight battery",
}


@dataclass
class Event:
    """Something gameplay-relevant happened; the presentation layer decides how to show it."""

    kind: str
    pos: pygame.Vector2 = field(default_factory=pygame.Vector2)
    text: str = ""
    item: str = ""


class Pickup:
    def __init__(self, kind, pos):
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.collected = False

    @property
    def name(self):
        return PICKUP_NAMES[self.kind]

    def touches(self, point, radius):
        return self.pos.distance_squared_to(point) <= radius * radius


class Door:
    def __init__(self, tiles, requirement, name, world):
        self.tiles = tiles
        self.requirement = requirement
        self.name = name
        cols = [c for c, _ in tiles]
        rows = [r for _, r in tiles]
        self.rect = pygame.Rect(
            min(cols) * TILE,
            min(rows) * TILE,
            (max(cols) - min(cols) + 1) * TILE,
            (max(rows) - min(rows) + 1) * TILE,
        )
        self.open_amount = 0.0
        self.is_open = False
        self.rattle = 0.0
        world.set_closed(tiles, True)

    @property
    def center(self):
        return pygame.Vector2(self.rect.center)

    def open(self, world):
        self.is_open = True
        world.set_closed(self.tiles, False)

    def deny(self):
        self.rattle = settings.DOOR_RATTLE_TIME

    def update(self, dt):
        if self.is_open:
            self.open_amount = approach(self.open_amount, 1.0, dt / settings.DOOR_OPEN_TIME)
        self.rattle = max(0.0, self.rattle - dt)
