from src.session import Session
from tests.helpers import pickup_of, press_interact, step


def test_walking_onto_keycard_collects_it():
    session = Session()
    keycard = pickup_of(session, "keycard")
    session.player.pos.update(keycard.pos)
    events = step(session)
    assert keycard.collected
    assert session.player.has("keycard")
    assert [e.kind for e in events] == ["pickup"]


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
