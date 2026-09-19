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
