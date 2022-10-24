from gc import collect
from itertools import count

from pytest import raises

from foundry.core.gui import (
    Signal,
    SignalBlocker,
    SignalInstance,
    SignalTester,
    _SignalElement,
)


class SimpleObject:
    class_signal = Signal()
    counter = count()

    def __init__(self) -> None:
        self.count = next(self.counter)
        self.test_value = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(0x{self.count:02X})"

    def test(self, v: int) -> None:
        self.test_value = v

    @property
    def signal_instance(self) -> SignalInstance:
        return SignalInstance(self, self.class_signal)


class TestSignal:
    __test_class__: type[Signal] = Signal

    def test_creation_simple(self):
        self.__test_class__()

    def test_creation_complex(self):
        self.__test_class__(_SignalElement(0, lambda _: None), _SignalElement(1, lambda _: None))

    def test_str_no_name(self):
        str(self.__test_class__(_SignalElement(0, lambda _: None), _SignalElement(1, lambda _: None)))

    def test_str_name(self):
        str(self.__test_class__(_SignalElement(0, lambda _: None), _SignalElement(1, lambda _: None), name="test"))

    def test_missing(self):
        with raises(KeyError):
            self.__test_class__()[4]

    def test_get_subscriber(self):
        element = _SignalElement(0, lambda _: None)
        signal = self.__test_class__(element, _SignalElement(1, lambda _: None))
        assert element in signal
        assert element is signal[element]

    def test_len(self):
        assert 0 == len(self.__test_class__())
        assert 2 == len(self.__test_class__(_SignalElement(0, lambda _: None), _SignalElement(1, lambda _: None)))

    def test_bool(self):
        assert not bool(self.__test_class__())
        assert bool(self.__test_class__(_SignalElement(0, lambda _: None), _SignalElement(1, lambda _: None)))

    def test_class_connection(self):
        SimpleObject.class_signal.clear()
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        SimpleObject.class_signal.connect(change_value, obj)
        SimpleObject.class_signal.emit(5, obj)
        assert value == 5
        SimpleObject.class_signal.emit(3, obj2)
        assert value == 5
        SimpleObject.class_signal.connect(change_value, obj2)
        SimpleObject.class_signal.emit(1, obj2)
        assert value == 1
        SimpleObject.class_signal.disconnect(change_value, obj)
        SimpleObject.class_signal.emit(5, obj)
        assert value == 1
        SimpleObject.class_signal.disconnect(change_value, obj2)
        SimpleObject.class_signal.clear()
        assert 0 == len(SimpleObject.class_signal)

    def test_class_connection_methods(self):
        SimpleObject.class_signal.clear()
        obj, obj2 = SimpleObject(), SimpleObject()

        SimpleObject.class_signal.connect(obj.test, obj)
        SimpleObject.class_signal.emit(5, obj)
        assert obj.test_value == 5
        SimpleObject.class_signal.emit(3, obj2)
        assert obj.test_value == 5
        SimpleObject.class_signal.connect(obj2.test, obj2)
        SimpleObject.class_signal.emit(1, obj2)
        assert obj.test_value == 5
        assert obj2.test_value == 1
        del obj
        del obj2
        collect()
        SimpleObject.class_signal.emit(0, None)
        assert 0 == len(SimpleObject.class_signal)

    def test_class_connection_max_uses(self):
        SimpleObject.class_signal.clear()
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        SimpleObject.class_signal.connect(change_value, obj, max_uses=1)
        SimpleObject.class_signal.emit(5, obj)
        assert value == 5
        SimpleObject.class_signal.emit(3, obj2)
        assert value == 5
        SimpleObject.class_signal.connect(change_value, obj2, max_uses=1)
        SimpleObject.class_signal.emit(1, obj2)
        assert value == 1
        SimpleObject.class_signal.emit(5, obj)
        assert value == 1
        SimpleObject.class_signal.emit(3, obj)
        assert value == 1
        assert 0 == len(SimpleObject.class_signal)

    def test_silence(self):
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        SimpleObject.class_signal.connect(change_value, obj)
        SimpleObject.class_signal.emit(5, obj)
        assert value == 5
        assert not SimpleObject.class_signal.is_silenced(obj)
        SimpleObject.class_signal.silence(obj, True)
        assert SimpleObject.class_signal.is_silenced(obj)
        SimpleObject.class_signal.emit(3, obj)
        assert value == 5
        SimpleObject.class_signal.connect(change_value, obj2)
        SimpleObject.class_signal.emit(1, obj2)
        assert value == 1
        SimpleObject.class_signal.silence(obj, False)
        assert not SimpleObject.class_signal.is_silenced(obj)
        SimpleObject.class_signal.disconnect(change_value, obj)
        SimpleObject.class_signal.emit(5, obj)
        assert value == 1
        SimpleObject.class_signal.disconnect(change_value, obj2)


class TestSignalInstance:
    __test_class__: type[SignalInstance] = SignalInstance

    def test_creation_simple(self):
        SimpleObject.class_signal.clear()
        obj = SimpleObject()
        self.__test_class__(obj, obj.class_signal)

    def test_missing(self):
        SimpleObject.class_signal.clear()
        with raises(KeyError):
            SimpleObject().signal_instance[4]

    def test_get_subscriber(self):
        SimpleObject.class_signal.clear()
        obj = SimpleObject()
        obj.signal_instance.connect(lambda _: None)
        element = obj.class_signal.subscribers[0]
        assert element in obj.signal_instance
        assert element is obj.signal_instance[element]
        obj2 = SimpleObject()
        assert element not in obj2.signal_instance
        with raises(KeyError):
            obj2.signal_instance[element]

    def test_len(self):
        SimpleObject.class_signal.clear()
        obj = SimpleObject()
        assert 0 == len(obj.signal_instance)
        obj.signal_instance.connect(lambda _: None, weak=False)
        assert 1 == len(obj.signal_instance)
        obj.signal_instance.connect(lambda _: None, weak=False)
        assert 2 == len(obj.signal_instance)

    def test_bool(self):
        SimpleObject.class_signal.clear()
        assert not bool(SimpleObject().signal_instance)
        obj = SimpleObject()
        obj.signal_instance.connect(lambda _: None, weak=False)
        assert bool(obj.signal_instance)
        assert not bool(SimpleObject().signal_instance)

    def test_instance_connection(self):
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        obj.signal_instance.connect(change_value)
        obj.signal_instance.emit(5)
        assert value == 5
        obj2.signal_instance.emit(3)
        assert value == 5
        obj2.signal_instance.connect(change_value)
        obj2.signal_instance.emit(1)
        assert value == 1
        obj.signal_instance.disconnect(change_value)
        obj.signal_instance.emit(5)
        assert value == 1
        obj2.signal_instance.disconnect(change_value)

    def test_silence(self):
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        obj.signal_instance.connect(change_value)
        obj.signal_instance.emit(5)
        assert value == 5
        assert not obj.signal_instance.is_silenced
        obj.signal_instance.silence(True)
        assert obj.signal_instance.is_silenced
        obj.signal_instance.emit(3)
        assert value == 5
        obj2.signal_instance.connect(change_value)
        obj2.signal_instance.emit(1)
        assert value == 1
        obj.signal_instance.silence(False)
        assert not obj.signal_instance.is_silenced
        obj.signal_instance.disconnect(change_value)
        obj.signal_instance.emit(5)
        assert value == 1
        obj2.signal_instance.disconnect(change_value)

    def test_link_simple(self):
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        obj.signal_instance.connect(change_value)
        obj.signal_instance.emit(5)
        assert value == 5
        obj2.signal_instance.emit(3)
        assert value == 5
        obj.signal_instance.link(obj2.signal_instance)
        obj2.signal_instance.emit(1)
        assert value == 1
        obj.signal_instance.disconnect(change_value)
        obj.signal_instance.emit(5)
        assert value == 1
        obj2.signal_instance.disconnect(change_value)


class TestSignalBlocker:
    __test_class__: type[SignalBlocker] = SignalBlocker

    def test_silence(self):
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        obj.signal_instance.connect(change_value)
        obj.signal_instance.emit(5)
        assert value == 5
        assert not obj.signal_instance.is_silenced
        with self.__test_class__(obj.signal_instance):
            assert obj.signal_instance.is_silenced
            obj.signal_instance.emit(3)
            assert value == 5
            obj2.signal_instance.connect(change_value)
            obj2.signal_instance.emit(1)
            assert value == 1
        assert not obj.signal_instance.is_silenced
        obj.signal_instance.disconnect(change_value)
        obj.signal_instance.emit(5)
        assert value == 1
        obj2.signal_instance.disconnect(change_value)

    def test_double_silence(self):
        obj, obj2 = SimpleObject(), SimpleObject()
        value = False

        def change_value(v):
            nonlocal value
            value = v

        obj.signal_instance.connect(change_value)
        obj.signal_instance.emit(5)
        assert value == 5
        assert not obj.signal_instance.is_silenced
        with self.__test_class__(obj.signal_instance):
            assert obj.signal_instance.is_silenced
            with self.__test_class__(obj.signal_instance):
                assert obj.signal_instance.is_silenced
                obj.signal_instance.emit(3)
                assert value == 5
                obj2.signal_instance.connect(change_value)
                obj2.signal_instance.emit(1)
                assert value == 1
            assert obj.signal_instance.is_silenced
        assert not obj.signal_instance.is_silenced
        obj.signal_instance.disconnect(change_value)
        obj.signal_instance.emit(5)
        assert value == 1
        obj2.signal_instance.disconnect(change_value)


class TestSignalTester:
    __test_class__: type[SignalTester] = SignalTester

    def test_signal_tester_initialization(self):
        self.__test_class__(SimpleObject().signal_instance)

    def test_signal_tester_context_manager(self):
        with self.__test_class__(SimpleObject().signal_instance) as tester:
            assert 0 == tester.count

    def test_signal_tester_context_manager_simple(self):
        obj = SimpleObject()
        with self.__test_class__(obj.signal_instance) as tester:
            assert 0 == tester.count
            obj.signal_instance.emit(1)
            assert 1 == tester.count
            obj.signal_instance.emit(0)
            assert 2 == tester.count
