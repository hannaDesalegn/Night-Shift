from src.entities import Generator
from src.session import OBJECTIVES, Session
from tests.helpers import step, walk


def test_run_starts_in_progress():
    assert Session().outcome is None


def test_reaching_loading_dock_after_gate_opens_ends_run():
    session = Session()
    session.generator.state = Generator.ONLINE
    session.exit_gate.open(session.world)
    gate = session.exit_gate
    session.player.pos.update(gate.center.x, gate.rect.top - 20)
    events = step(session, walk(0, 1), seconds=1.0)
    assert session.outcome == "escaped"
    assert "escaped" in [e.kind for e in events]


def test_closed_gate_blocks_escape():
    session = Session()
    gate = session.exit_gate
    session.player.pos.update(gate.center.x, gate.rect.top - 20)
    step(session, walk(0, 1), seconds=1.0)
    assert session.outcome is None


def test_finished_session_stops_updating():
    session = Session()
    session.finish("escaped")
    before = session.elapsed
    step(session, seconds=1.0)
    assert session.elapsed == before


def test_objectives_follow_progression():
    session = Session()
    seen = [session.objective_index]

    def advance():
        step(session)
        seen.append(session.objective_index)

    session.player.inventory.add("keycard")
    advance()
    session.maintenance_door.open(session.world)
    advance()
    session.player.inventory.add("component")
    advance()
    session.player.inventory.discard("component")
    session.generator.start()
    advance()
    session.generator.state = Generator.ONLINE
    advance()
    session.exit_gate.open(session.world)
    advance()
    assert seen == [0, 1, 2, 3, 3, 4, 5]
    assert session.objective == OBJECTIVES[-1]


def test_objective_change_emits_event():
    session = Session()
    session.player.inventory.add("keycard")
    events = step(session)
    assert [e.text for e in events if e.kind == "objective"] == [OBJECTIVES[1]]
