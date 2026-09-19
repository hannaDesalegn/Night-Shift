"""Rules for a single run: pickups, interactions, objectives and outcome."""

from src import settings
from src.enemy import Enemy
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
        self.enemy = Enemy(layout.patrol_points, start_index=settings.ENEMY_START_POST)
        self.elapsed = 0.0
        self.time_left = settings.TIME_LIMIT
        self.score = 0
        self.time_bonus = 0
        self.events = []
        # None while the run is in progress, otherwise the reason it ended.
        self.outcome = None
        self.objective_index = 0

    def update(self, dt, controls):
        self.events = []
        if self.outcome:
            return self.events
        self.elapsed += dt
        if self._tick_clock(dt):
            return self.events
        self.player.update(dt, controls.move, self.world)
        self._update_flashlight(dt, controls.toggle_flashlight)
        alert = self.enemy.update(dt, self.world, self.player)
        if alert == "spotted":
            self.emit("enemy_spotted", self.enemy.pos, "It has seen you")
        elif alert == "lost":
            self.emit("enemy_searching", self.enemy.pos)
        self._check_contact()
        if self.outcome:
            return self.events
        for door in self.doors:
            door.update(dt)
        if self.generator.update(dt):
            self.emit("power_on", self.generator.center, "Power restored")
            self.add_score(settings.SCORE_POWER, self.generator.center)
        self._collect_pickups()
        if self.world.is_escape(self.player.pos):
            self.add_score(settings.SCORE_ESCAPE)
            self.time_bonus = int(self.time_left) * settings.SCORE_PER_SECOND_LEFT
            self.add_score(self.time_bonus)
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

    def add_score(self, points, pos=None):
        self.score = max(0, self.score + points)
        self.emit("score", pos, f"{points:+d}")

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
            if pickup.kind == "battery":
                self.player.recharge(settings.BATTERY_CHARGE)
            else:
                self.player.inventory.add(pickup.kind)
            self.emit("pickup", pickup.pos, f"{pickup.name} acquired", pickup.kind)
            self.add_score(settings.SCORE_PICKUP[pickup.kind], pickup.pos)

    def _tick_clock(self, dt):
        """Count down the shift; returns True if time ran out this frame."""
        before = self.time_left
        self.time_left = max(0.0, self.time_left - dt)
        if before > settings.TIME_WARNING >= self.time_left:
            self.emit("time_low", text="One minute left")
        if self.time_left <= 0:
            self.finish("timeout")
            return True
        return False

    def _update_flashlight(self, dt, toggle):
        player = self.player
        if toggle:
            if player.toggle_flashlight():
                self.emit("flashlight_on" if player.flashlight_on else "flashlight_off")
            else:
                self.emit("flashlight_dead", text="Flashlight is recharging")
        status = player.update_flashlight(dt)
        if status == "empty":
            self.emit("flashlight_empty", text="Flashlight battery died")
        elif status == "low":
            self.emit("flashlight_low", text="Flashlight battery low")

    def _check_contact(self):
        if not self.enemy.touches(self.player):
            return
        if self.player.take_damage(settings.ENEMY_DAMAGE, source=self.enemy.pos):
            self.enemy.stagger()
            self.emit("damage")
            self.add_score(-settings.SCORE_DAMAGE_PENALTY)
            if not self.player.alive:
                self.finish("caught")

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
