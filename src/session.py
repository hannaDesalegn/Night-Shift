"""Rules for a single run: pickups, interactions, objectives and outcome."""

from src import settings
from src.entities import Door, Event, Generator, Pickup
from src.player import Player
from src.utils import distance_to_rect
from src.world import World

OBJECTIVES = (
    "Find the maintenance keycard",
    "Unlock the maintenance door",
    "Find the generator fuse cell",
    "Restore power in the generator room",
    "Open the exit gate in the exit bay",
    "Escape through the loading dock",
)


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
        self.generator = Generator(layout.generator_tiles)
        self.elapsed = 0.0
        self.events = []
        # None while the run is in progress, otherwise the reason it ended.
        self.outcome = None
        self.objective_index = 0

    def update(self, dt, controls):
        self.events = []
        if self.outcome:
            return self.events
        self.elapsed += dt
        self.player.update(dt, controls.move, self.world)
        for door in self.doors:
            door.update(dt)
        if self.generator.update(dt):
            self.emit("power_on", self.generator.center, "Power restored")
        self._collect_pickups()
        if self.world.is_escape(self.player.pos):
            self.finish("escaped")
            return self.events
        if controls.interact:
            target = self.interaction_target()
            if target is not None:
                self._interact(target)
        self._update_objective()
        return self.events

    @property
    def objective(self):
        return OBJECTIVES[self.objective_index]

    def _current_objective_index(self):
        if not self.maintenance_door.is_open:
            return 1 if self.player.has("keycard") else 0
        if not self.power_on:
            started = self.generator.state != Generator.OFFLINE
            return 3 if started or self.player.has("component") else 2
        return 5 if self.exit_gate.is_open else 4

    def _update_objective(self):
        index = self._current_objective_index()
        if index != self.objective_index:
            self.objective_index = index
            self.emit("objective", text=self.objective)

    def finish(self, outcome):
        self.outcome = outcome
        self.emit(outcome)

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

    @property
    def power_on(self):
        return self.generator.state == Generator.ONLINE

    def _interactables(self):
        targets = [door for door in self.doors if not door.is_open]
        if self.generator.state == Generator.OFFLINE:
            targets.append(self.generator)
        return targets

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
        if self.player.has("component"):
            return "Install fuse cell"
        return "Generator — missing fuse cell"

    def _interact(self, target):
        if isinstance(target, Door):
            self._use_door(target)
        elif isinstance(target, Generator):
            self._use_generator()

    def _use_door(self, door):
        if self.requirement_met(door.requirement):
            door.open(self.world)
            self.emit("door_open", door.center, f"{door.name} opened")
        else:
            door.deny()
            reason = "Keycard required" if door.requirement == "keycard" else "No power"
            self.emit("door_locked", door.center, reason)

    def _use_generator(self):
        if self.player.has("component"):
            self.player.inventory.discard("component")
            self.generator.start()
            self.emit("generator_start", self.generator.center, "Fuse cell installed")
        else:
            self.emit("generator_denied", self.generator.center, "It needs a fuse cell")
