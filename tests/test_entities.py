from src import settings
from src.entities import Generator
from src.session import Session
from tests.helpers import pickup_of, press_interact, step


def test_walking_onto_keycard_collects_it():
    session = Session()
    keycard = pickup_of(session, "keycard")
    session.player.pos.update(keycard.pos)
    events = step(session)
    assert keycard.collected
    assert session.player.has("keycard")
    assert [e.kind for e in events] == ["pickup", "objective"]


def test_pickup_is_only_collected_once():
    session = Session()
    keycard = pickup_of(session, "keycard")
    session.player.pos.update(keycard.pos)
    step(session)
    assert step(session) == []


def test_distant_pickups_are_ignored():
    session = Session()
    step(session)
    assert not any(p.collected for p in session.pickups)


def stand_at_door(session, door):
    session.player.pos.update(door.center.x, door.rect.top - 30)


def test_locked_door_denies_without_keycard():
    session = Session()
    door = session.maintenance_door
    stand_at_door(session, door)
    events = step(session, press_interact())
    assert not door.is_open
    assert door.rattle > 0
    assert [e.kind for e in events] == ["door_locked"]
    assert session.world.is_solid(*door.tiles[0])


def test_keycard_opens_maintenance_door():
    session = Session()
    session.player.inventory.add("keycard")
    door = session.maintenance_door
    stand_at_door(session, door)
    events = step(session, press_interact())
    assert door.is_open
    assert "door_open" in [e.kind for e in events]
    assert not session.world.is_solid(*door.tiles[0])


def test_door_animation_completes():
    session = Session()
    session.player.inventory.add("keycard")
    stand_at_door(session, session.maintenance_door)
    step(session, press_interact())
    step(session, seconds=1.0)
    assert session.maintenance_door.open_amount == 1.0


def test_interaction_requires_proximity():
    session = Session()
    assert session.interaction_target() is None
    stand_at_door(session, session.maintenance_door)
    assert session.interaction_target() is session.maintenance_door


def test_exit_gate_stays_shut_without_power():
    session = Session()
    gate = session.exit_gate
    session.player.pos.update(gate.center.x, gate.rect.top - 30)
    step(session, press_interact())
    assert not gate.is_open


def stand_at_generator(session):
    gen = session.generator
    session.player.pos.update(gen.rect.centerx, gen.rect.bottom + 20)


def test_generator_refuses_without_component():
    session = Session()
    stand_at_generator(session)
    events = step(session, press_interact())
    assert session.generator.state == Generator.OFFLINE
    assert [e.kind for e in events] == ["generator_denied"]


def test_generator_consumes_component_and_restores_power():
    session = Session()
    session.player.inventory.add("component")
    stand_at_generator(session)
    step(session, press_interact())
    assert session.generator.state == Generator.STARTING
    assert not session.player.has("component")
    assert not session.power_on
    events = step(session, seconds=settings.GENERATOR_START_TIME + 0.1)
    assert session.power_on
    assert "power_on" in [e.kind for e in events]


def test_power_allows_exit_gate_to_open():
    session = Session()
    session.generator.state = Generator.ONLINE
    gate = session.exit_gate
    session.player.pos.update(gate.center.x, gate.rect.top - 30)
    step(session, press_interact())
    assert gate.is_open
