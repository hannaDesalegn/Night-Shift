"""Rules for a single run: pickups, interactions, objectives and outcome."""

from src import settings
from src.entities import Event, Pickup
from src.player import Player
from src.world import World


class Session:
    def __init__(self):
        self.world = World()
        layout = self.world.layout
        self.player = Player(layout.player_start)
        self.pickups = [Pickup(kind, pos) for kind, pos in layout.pickups]
        self.elapsed = 0.0
        self.events = []

    def update(self, dt, controls):
        self.events = []
        self.elapsed += dt
        self.player.update(dt, controls.move, self.world)
        self._collect_pickups()
        return self.events

    def emit(self, kind, pos=None, text="", item=""):
        pos = self.player.pos.copy() if pos is None else pos.copy()
        self.events.append(Event(kind, pos, text, item))

    def _collect_pickups(self):
        for pickup in self.pickups:
            if pickup.collected or not pickup.touches(self.player.pos, settings.PICKUP_RADIUS):
                continue
            pickup.collected = True
            if pickup.kind != "battery":
                self.player.inventory.add(pickup.kind)
            self.emit("pickup", pickup.pos, f"{pickup.name} acquired", pickup.kind)
