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


def tiles_rect(tiles):
    cols = [c for c, _ in tiles]
    rows = [r for _, r in tiles]
    width = max(cols) - min(cols) + 1
    height = max(rows) - min(rows) + 1
    return pygame.Rect(min(cols) * TILE, min(rows) * TILE, width * TILE, height * TILE)


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
        self.rect = tiles_rect(tiles)
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


class Generator:
    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"

    def __init__(self, tiles):
        self.rect = tiles_rect(tiles)
        self.state = self.OFFLINE
        self.progress = 0.0

    @property
    def center(self):
        return pygame.Vector2(self.rect.center)

    def start(self):
        self.state = self.STARTING

    def update(self, dt):
        """Advance the start-up sequence; returns True on the frame power comes online."""
        if self.state != self.STARTING:
            return False
        self.progress = min(1.0, self.progress + dt / settings.GENERATOR_START_TIME)
        if self.progress >= 1.0:
            self.state = self.ONLINE
            return True
        return False
