from hypothesis import given
from hypothesis.strategies import composite, integers, lists

from foundry.core.UndoController import UndoController


@composite
def undo_controller(draw, min_size: int = 0, max_size: int | None = None):
    events = draw(lists(integers(), min_size=min_size, max_size=max_size))
    controller = UndoController(0)
    for event in events:
        controller.do(event)
    return controller


def test_equality_simple():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    assert controller1 == controller2


def test_inequality_simple():
    controller1 = UndoController(0)
    controller2 = UndoController(1)
    assert controller1 != controller2


def test_equality_with_undo():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    controller1.do(1)
    controller2.do(1)
    controller1.undo()
    controller2.undo()
    assert controller1 == controller2


def test_inequality_with_undo():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    controller1.do(1)
    controller2.do(2)
    controller1.undo()
    controller2.undo()
    assert controller1 != controller2


def test_inequality_with_undo_and_normal():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    controller1.do(1)
    controller1.undo()
    assert controller1 != controller2


def test_equality_with_redo():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    controller1.do(1)
    controller2.do(1)
    controller1.undo()
    controller2.undo()
    controller1.redo()
    controller2.redo()
    assert controller1 == controller2


def test_inequality_with_redo():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    controller1.do(1)
    controller2.do(2)
    controller1.undo()
    controller2.undo()
    controller1.redo()
    controller2.redo()
    assert controller1 != controller2


def test_equality_with_redo_and_normal():
    controller1 = UndoController(0)
    controller2 = UndoController(0)
    controller1.do(1)
    controller2.do(1)
    controller1.undo()
    controller1.redo()
    assert controller1 == controller2


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
