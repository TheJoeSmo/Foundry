from attr import attrs
from pytest import raises

from foundry.core.gui import (
    Action,
    SignalTester,
    UndoRedo,
    UndoRedoActor,
    UndoRedoForwarder,
    UndoRedoRoot,
)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class SimpleModel:
    child: int = 0


class SimpleUndoRedoActor(UndoRedoActor):
    def __init__(self, model: SimpleModel | None = None):
        if model is None:
            model = SimpleModel()
        self.model = model
        super().__init__()


class SimpleUndoRedoForwarder(UndoRedoForwarder):
    def __init__(self, model: SimpleModel | None = None):
        if model is None:
            model = SimpleModel()
        self.model = model
        super().__init__()


class TestUndoRedo:
    __test_class__: type[UndoRedo] = UndoRedo

    def _do_undo_redo2(self, undo_redo2, undo_redo):
        undo_redo2.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo.undo()
        undo_redo2.undo()

    def test_initialization_simple(self):
        self.__test_class__(1)

    def test_equality_simple(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        assert undo_redo == undo_redo2

    def test_inequality_simple(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(1)
        assert undo_redo != undo_redo2

    def test_equality_with_undo(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        self._do_undo_redo2(undo_redo2, undo_redo)
        assert undo_redo == undo_redo2

    def test_inequality_with_undo(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo2.do(Action(None, lambda: 2, lambda: 0, "2"))
        undo_redo.undo()
        undo_redo2.undo()
        assert undo_redo != undo_redo2

    def test_inequality_with_undo_and_normal(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo.undo()
        assert undo_redo != undo_redo2

    def test_equality_with_redo(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        self._do_undo_redo2(undo_redo2, undo_redo)
        undo_redo.redo()
        undo_redo2.redo()
        assert undo_redo == undo_redo2

    def test_inequality_with_redo(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo2.do(Action(None, lambda: 2, lambda: 0, "2"))
        undo_redo.undo()
        undo_redo2.undo()
        undo_redo.redo()
        undo_redo2.redo()
        assert undo_redo != undo_redo2

    def test_equality_with_redo_and_normal(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo2: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo2.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo.undo()
        undo_redo.redo()
        assert undo_redo == undo_redo2

    def test_do(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        assert len(undo_redo.undo_stack)

    def test_undo(self):
        undo_redo: UndoRedo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        assert undo_redo.can_undo
        assert 0 == undo_redo.undo()()

    def test_redo(self):
        undo_redo = self.__test_class__(0)
        undo_redo.do(Action(None, lambda: 1, lambda: 0, "1"))
        undo_redo.undo()
        assert undo_redo.can_redo
        assert 1 == undo_redo.redo()()


class TestUndoRedoActor:
    __test_class__: type[SimpleUndoRedoActor] = SimpleUndoRedoActor

    def test_get_child_attribute(self):
        obj: UndoRedoActor = self.__test_class__()
        child = SimpleModel(1)
        obj.__children__ = {id(child): "child"}
        assert "child" == obj.get_child_attribute(child)  # type: ignore

    def test_compose_child_action_actor_provided(self):
        obj: UndoRedoActor = self.__test_class__()
        obj2: UndoRedoActor = self.__test_class__()
        obj.__children__ = {id(obj2): "child"}
        obj.child = obj2  # type: ignore
        obj.compose_child_action(Action(obj2, lambda: 1, lambda: 0, "set obj2 to 1"))

    def test_compose_child_action_actor_not_provided(self):
        obj: UndoRedoActor = self.__test_class__()
        with raises(ValueError):
            obj.compose_child_action(Action(None, lambda: 1, lambda: 0, "invalid"))


class TestUndoRedoForwarder(TestUndoRedoActor):
    __test_class__: type[SimpleUndoRedoForwarder] = SimpleUndoRedoForwarder

    def test_link_child(self):
        obj: UndoRedoForwarder = self.__test_class__()
        obj2: UndoRedoForwarder = self.__test_class__()
        obj.__children__ = {id(obj2): "child"}
        obj.child = obj2  # type: ignore
        obj.link_child(obj2)
        with SignalTester(obj.action_performed) as tester:
            obj2.action_performed.emit(Action(obj2, lambda: SimpleModel(1), lambda: SimpleModel(0), "set obj2 to 1"))
            assert 1 == tester.count

    def test_change_state(self):
        obj: UndoRedoForwarder = self.__test_class__()
        with SignalTester(obj.action_performed) as tester:
            obj.change_state(1)
            assert 1 == tester.count
            obj.change_state(0)
            assert 2 == tester.count

    def test_do(self):
        obj: UndoRedoForwarder = self.__test_class__()
        with SignalTester(obj.action_performed) as tester:
            obj.do(SimpleModel(0), SimpleModel(1))
            assert 1 == tester.count
            obj.do(SimpleModel(1), SimpleModel(0))
            assert 2 == tester.count


class SimpleUndoRedoRoot(UndoRedoRoot):
    def __init__(self, model: SimpleModel | None = None):
        self.model = model if model is not None else SimpleModel()
        self.initialize_state(model)

    def __eq__(self, other):
        return self.model == other.model if isinstance(other, UndoRedoRoot) else False

    @property
    def undo_stack(self):
        return self.__undo_redo__.undo_stack

    @property
    def redo_stack(self):
        return self.__undo_redo__.redo_stack


class TestUndoRedoRoot(TestUndoRedoActor, TestUndoRedo):
    __test_class__: type[SimpleUndoRedoRoot] = SimpleUndoRedoRoot

    def test_undo(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(undo_redo, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        assert undo_redo.can_undo
        undo_redo.undo()
        assert SimpleModel(0) == undo_redo.model

    def test_redo(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(undo_redo, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        assert SimpleModel(1) == undo_redo.model
        undo_redo.undo()
        assert undo_redo.can_redo
        assert SimpleModel(0) == undo_redo.model
        undo_redo.redo()
        assert SimpleModel(1) == undo_redo.model

    def test_equality_with_undo(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo2: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo2.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo.undo()
        undo_redo2.undo()
        assert undo_redo == undo_redo2

    def test_inequality_with_undo(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo2: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo2.do(Action(None, lambda: SimpleModel(2), lambda: SimpleModel(0), "2"), apply_action=True)
        undo_redo.undo()
        undo_redo2.undo()
        assert undo_redo.__undo_redo__ != undo_redo2.__undo_redo__
        assert undo_redo.model == undo_redo2.model

    def test_equality_with_redo(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo2: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo2.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo.undo()
        undo_redo2.undo()
        undo_redo.redo()
        undo_redo2.redo()
        assert undo_redo == undo_redo2

    def test_inequality_with_redo(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo2: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo2.do(Action(None, lambda: SimpleModel(2), lambda: SimpleModel(0), "2"), apply_action=True)
        undo_redo.undo()
        undo_redo2.undo()
        undo_redo.redo()
        undo_redo2.redo()
        assert undo_redo != undo_redo2

    def test_inequality_with_undo_and_normal(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo2: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo.undo()
        assert undo_redo.__undo_redo__ != undo_redo2.__undo_redo__
        assert undo_redo.model == undo_redo2.model

    def test_equality_with_redo_and_normal(self):
        undo_redo: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo2: SimpleUndoRedoRoot = self.__test_class__()
        undo_redo.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo2.do(Action(None, lambda: SimpleModel(1), lambda: SimpleModel(0), "1"), apply_action=True)
        undo_redo.undo()
        undo_redo.redo()
        assert undo_redo == undo_redo2
