from src.session import Session
from tests.helpers import pickup_of, step


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
