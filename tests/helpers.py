import pygame

from src.controls import InputState

DT = 1 / 60


def idle():
    return InputState(move=pygame.Vector2())


def press_interact():
    return InputState(move=pygame.Vector2(), interact=True)


def pickup_of(session, kind):
    return next(p for p in session.pickups if p.kind == kind)


def step(session, controls=None, seconds=DT):
    events = []
    for _ in range(max(1, round(seconds / DT))):
        events += session.update(DT, controls or idle())
    return events


def walk(x, y):
    return InputState(move=pygame.Vector2(x, y).normalize())


class ScriptedPlayer:
    """Walks the player to a goal using the world's own pathfinding."""

    def __init__(self, session):
        self.session = session
        self.path = []
        self.repath = 0.0

    def tick(self, goal, interact=False):
        player = self.session.player
        self.repath -= DT
        if self.repath <= 0 or not self.path:
            self.path = self.session.world.find_path(player.pos, goal) or []
            self.repath = 0.25
        move = pygame.Vector2()
        if self.path:
            offset = self.path[0] - player.pos
            if offset.length() < 8:
                self.path.pop(0)
            elif offset.length_squared():
                move = offset.normalize()
        controls = InputState(move=move, interact=interact)
        return self.session.update(DT, controls)

    def travel(self, goal, limit=90.0):
        """Walk toward goal until it is reached, the run ends, or the limit expires."""
        deadline = self.session.elapsed + limit
        while self.session.elapsed < deadline and not self.session.outcome:
            self.tick(goal)
            if self.session.player.pos.distance_to(goal) < 26:
                return True
        return False

    def use(self, repeats=5):
        for _ in range(repeats):
            self.tick(self.session.player.pos, interact=True)
            for _ in range(8):
                self.tick(self.session.player.pos)

    def wait(self, seconds):
        for _ in range(int(seconds / DT)):
            self.tick(self.session.player.pos)


def approach_spot(rect, player_pos):
    """A standing spot just outside a prop, on whichever side the player is already on."""
    above = pygame.Vector2(rect.centerx, rect.top - 34)
    below = pygame.Vector2(rect.centerx, rect.bottom + 34)
    return above if player_pos.distance_to(above) <= player_pos.distance_to(below) else below
