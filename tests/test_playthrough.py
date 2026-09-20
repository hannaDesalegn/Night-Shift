"""End-to-end run: every objective completed in order by a scripted player."""

import pygame

from src import settings
from src.session import OBJECTIVES, Session
from tests.helpers import ScriptedPlayer, approach_spot


def test_full_run_can_be_completed():
    session = Session()
    bot = ScriptedPlayer(session)
    player = session.player
    pickups = {p.kind: p for p in session.pickups}

    assert bot.travel(pickups["keycard"].pos)
    assert player.has("keycard")

    door = session.maintenance_door
    assert bot.travel(approach_spot(door.rect, player.pos))
    bot.use()
    assert door.is_open

    assert bot.travel(pickups["component"].pos)
    assert player.has("component")

    generator = session.generator
    assert bot.travel(approach_spot(generator.rect, player.pos))
    bot.use()
    bot.wait(settings.GENERATOR_START_TIME + 0.5)
    assert session.power_on
    assert session.objective == OBJECTIVES[4]

    gate = session.exit_gate
    assert bot.travel(approach_spot(gate.rect, player.pos))
    bot.use()
    assert gate.is_open

    dock_tile = min(session.world.layout.escape_tiles, key=lambda t: abs(t[0] * 48 - gate.center.x))
    dock = pygame.Vector2(dock_tile[0] * 48 + 24, dock_tile[1] * 48 + 24)
    bot.travel(dock)

    assert session.outcome == "escaped"
    assert session.score > settings.SCORE_ESCAPE
    assert session.time_left > 0


def test_run_is_comfortably_within_the_time_limit():
    """A player who knows the route should finish with most of the clock to spare."""
    session = Session()
    bot = ScriptedPlayer(session)
    pickups = {p.kind: p for p in session.pickups}
    bot.travel(pickups["keycard"].pos)
    assert session.elapsed < settings.TIME_LIMIT * 0.25
