from typing import Optional

from hypothesis import given
from hypothesis.strategies import composite, integers, lists

from foundry.core.UndoController import UndoController


@composite
def undo_controller(draw, min_size: int = 0, max_size: Optional[int] = None):
    events = draw(lists(integers(), min_size=min_size, max_size=max_size))
    controller = UndoController(0)
    for event in events:
        controller.do(event)
    return controller


def test_do():
    controller = UndoController(0)
    controller.do(1)
    assert 1 == controller.state


def test_undo():
    controller = UndoController(0)
    controller.do(1)
    assert controller.can_undo
    assert 0 == controller.undo()


def test_redo():
    controller = UndoController(0)
    controller.do(1)
    controller.undo()
    assert controller.can_redo
    assert 1 == controller.redo()


@given(undo_controller(min_size=1))
def test_undo_redo_same_result(controller: UndoController):
    initial_state = controller.state
    controller.undo()
    controller.redo()
    assert initial_state == controller.state
