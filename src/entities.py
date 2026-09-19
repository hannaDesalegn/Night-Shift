"""Interactive props placed in the facility."""

from dataclasses import dataclass, field

import pygame

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
