"""Rules for a single run: pickups, interactions, objectives and outcome."""

from src import settings
from src.entities import Door, Event, Pickup
from src.player import Player
from src.utils import distance_to_rect
from src.world import World


class Session:
    def __init__(self):
        self.world = World()
        layout = self.world.layout
        self.player = Player(layout.player_start)
        self.pickups = [Pickup(kind, pos) for kind, pos in layout.pickups]
        self.maintenance_door = Door(
            layout.door_tiles["D"], "keycard", "Maintenance door", self.world
        )
        self.exit_gate = Door(layout.door_tiles["X"], "power", "Exit gate", self.world)
        self.doors = [self.maintenance_door, self.exit_gate]
        self.power_on = False
        self.elapsed = 0.0
        self.events = []

    def update(self, dt, controls):
        self.events = []
        self.elapsed += dt
        self.player.update(dt, controls.move, self.world)
        for door in self.doors:
            door.update(dt)
        self._collect_pickups()
        if controls.interact:
            target = self.interaction_target()
            if target is not None:
                self._interact(target)
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

    # --- interaction ----------------------------------------------------

    def _interactables(self):
        return [door for door in self.doors if not door.is_open]

    def interaction_target(self):
        """Nearest interactable within reach, measured to its edge rather than its center."""
        best, best_dist = None, settings.INTERACT_RADIUS
        for target in self._interactables():
            dist = distance_to_rect(self.player.pos, target.rect)
            if dist <= best_dist:
                best, best_dist = target, dist
        return best

    def requirement_met(self, requirement):
        if requirement == "power":
            return self.power_on
        return self.player.has(requirement)

    def prompt_for(self, target):
        if isinstance(target, Door):
            if self.requirement_met(target.requirement):
                return f"Open {target.name.lower()}"
            return f"{target.name} — locked"
        return ""

    def _interact(self, target):
        if isinstance(target, Door):
            self._use_door(target)

    def _use_door(self, door):
        if self.requirement_met(door.requirement):
            door.open(self.world)
            self.emit("door_open", door.center, f"{door.name} opened")
        else:
            door.deny()
            reason = "Keycard required" if door.requirement == "keycard" else "No power"
            self.emit("door_locked", door.center, reason)
