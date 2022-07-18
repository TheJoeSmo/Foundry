from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import ClassVar, Generic, ParamSpec, TypeVar, final
from weakref import ReferenceType, WeakMethod, finalize, ref

from attr import Factory, attrs

_T = TypeVar("_T")
_P = ParamSpec("_P")


def _remove_garbage(func: Callable[_P, _T]) -> Callable[_P, _T]:
    def remove_garbage(*args: _P.args, **kwargs: _P.kwargs):
        args[0]._remove_garbage_subscribers()  # type: ignore
        return func(*args, **kwargs)

    return remove_garbage


@attrs(slots=True, auto_attribs=True)
class _SignalElement(Generic[_T]):
    uid: int
    subscriber: Callable[[_T], None]
    is_silenced: bool = False

    def __call__(self, value: _T) -> None:
        return self.subscriber(value)


@attrs(slots=True, auto_attribs=True)
class Signal(Generic[_T]):
    subscribers: list[_SignalElement] = Factory(list)
    _dead_subscribers: bool = False

    @_remove_garbage
    def connect(self, subscriber: Callable[[_T], None], instance: object, weak: bool = True) -> None:
        if weak:
            if hasattr(subscriber, "__self__") and hasattr(subscriber, "__func__"):
                subscriber = WeakMethod(subscriber)  # type: ignore
                obj = subscriber.__self__
            else:
                subscriber = ref(subscriber)  # type: ignore
                obj = subscriber
            finalize(obj, self._remove_subscriber)  # type: ignore

        if all(subscriber.uid != id(instance) for subscriber in self.subscribers):
            self.subscribers.append(_SignalElement(id(instance), subscriber))

    @_remove_garbage
    def disconnect(self, subscriber: Callable[[_T], None], instance: object) -> None:
        for idx, sub in enumerate(self.subscribers):
            if sub.subscriber is subscriber and sub.uid == id(instance):
                del self.subscribers[idx]

    @_remove_garbage
    def emit(self, value: _T, instance: object) -> None:
        for subscriber in self.subscribers:
            if subscriber.uid == id(instance):
                subscriber(value)

    @_remove_garbage
    def is_silenced(self, instance: object) -> bool:
        return not any(sub.uid == id(instance) and not sub.is_silenced for sub in self.subscribers)

    @_remove_garbage
    def silence(self, instance: object, is_silenced: bool) -> None:
        for idx, sub in enumerate(self.subscribers):
            if sub.uid == id(instance):
                self.subscribers[idx].is_silenced = is_silenced

    def _remove_garbage_subscribers(self):
        if self._dead_subscribers:
            self._dead_subscribers = False
            self.subscribers = [
                r for r in self.subscribers if not (isinstance(r.subscriber, ReferenceType) and r.subscriber() is None)
            ]

    def _remove_subscriber(self, _):
        self._dead_subscribers = True


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class SignalInstance(Generic[_T]):
    instance: object
    signal: Signal[_T]

    @property
    def is_silenced(self) -> bool:
        return self.signal.is_silenced(self.instance)

    def connect(self, subscriber: Callable[[_T], None]) -> None:
        self.signal.connect(subscriber, self.instance)

    def disconnect(self, subscriber: Callable[[_T], None]) -> None:
        self.signal.disconnect(subscriber, self.instance)

    def emit(self, value: _T) -> None:
        self.signal.emit(value, self.instance)

    def silence(self, silence: bool) -> None:
        self.signal.silence(self.instance, silence)


@attrs(auto_attribs=True)
class SignalBlocker:
    signal: SignalInstance | Sequence[SignalInstance]

    def __enter__(self):
        if isinstance(self.signal, Sequence):
            self._silenced = [signal.is_silenced for signal in self.signal]
            for signal in self.signal:
                signal.silence(True)
        else:
            self._silenced = self.signal.is_silenced
            self.signal.silence(True)

    def __exit__(self):
        if isinstance(self.signal, Sequence):
            for signal, silenced in zip(self.signal, self._silenced):  # type: ignore
                signal.silence(silenced)
        else:
            self.signal.silence(self._silenced)  # type: ignore


signal_blocker = SignalBlocker


class BaseModel:
    setup_signals: ClassVar[bool] = True


class WidgetMeta(type):
    def __new__(cls, name, bases, attrs):
        Model: BaseModel = attrs.get("Model", BaseModel)
        if not isinstance(Model, BaseModel):
            raise TypeError(f"{Model.__name__} must inherit from {BaseModel.__name__}")


class Widget(metaclass=WidgetMeta):
    __signals__: Sequence[SignalInstance]

    updated: SignalInstance[Model]

    class Model(BaseModel):
        pass

    @property
    @final
    def signals(self) -> Sequence[SignalInstance]:
        return self.__signals__

    @property
    @final
    def model(self) -> BaseModel:
        return self._model

    @model.setter
    @final
    def model(self, value: Model):
        with signal_blocker(self.signals):
            self._model = value
        self.updated.emit(value)

    def start(self, model: Model) -> None:
        ...

    def update(self, model: Model) -> None:
        ...
