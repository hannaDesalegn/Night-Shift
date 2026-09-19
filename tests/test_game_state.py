from src.entities import Generator
from src.session import Session
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
