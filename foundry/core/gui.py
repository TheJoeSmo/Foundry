from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from inspect import get_annotations
from itertools import chain
from logging import DEBUG, Logger, NullHandler, getLogger
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    NoReturn,
    ParamSpec,
    TypeVar,
    final,
    get_type_hints,
    overload,
)
from weakref import ReferenceType, finalize, ref

from attr import Factory, attrs, evolve
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDialog, QMainWindow, QWidget

_T = TypeVar("_T")
_U = TypeVar("_U")
_P = ParamSpec("_P")


LOGGER_NAME: Literal["GUI"] = "GUI"

log: Logger = getLogger(LOGGER_NAME)
log.addHandler(NullHandler())


def _remove_garbage(func: Callable[_P, _T]) -> Callable[_P, _T]:
    """
    A decorator for a method that needs to remove garbage subscribers.

    Parameters
    ----------
    func : Callable[_P, _T]
        The method to be decorated.

    Returns
    -------
    Callable[_P, _T]
        The decorated method.

    Notes
    -----
        `func` must be a method of `Signal` or a subclass.
    """

    def remove_garbage(*args: _P.args, **kwargs: _P.kwargs):
        args[0]._remove_garbage_subscribers()  # type: ignore
        return func(*args, **kwargs)

    return remove_garbage


@attrs(slots=True, auto_attribs=True)
class _Connection(Generic[_T, _U]):
    parent_signal_instance: SignalInstance[_T]
    signal_instance: SignalInstance[_U]
    converter: Callable[[_U], _T] | None = None
    condition: Callable[[_U], bool] | None = None

    def __str__(self) -> str:
        return (
            f"link<{self.signal_instance.instance}::{self.signal_instance.signal.name}, "
            + f"{self.parent_signal_instance.instance}::{self.parent_signal_instance.signal.name}>"
        )

    def __call__(self, value: _U) -> None:
        if self.condition is None or self.condition(value):
            with SignalBlocker(self.signal_instance):
                if not self.parent_signal_instance.is_silenced:
                    log.info(f"{self.signal_instance} is forwarding {value} to {self.parent_signal_instance}")
                self.parent_signal_instance.emit(
                    value if self.converter is None else self.converter(value)  # type: ignore
                )


@attrs(slots=True, auto_attribs=True, eq=False, repr=False)
class _SignalElement(Generic[_T]):
    """
    A representation of a subscriber for a signal.

    Parameters
    ----------
    Generic : _T
        The type that the subscriber will receive from the signal.

    Attributes
    ----------
    uid: int
        The identity associated with the object which is subscribing.
    subscriber: Callable[[_T], None]
        The method to be called when the signal emits an event.
    is_silenced: bool = False
        If the subscriber should accept the incoming signal.
    """

    uid: int
    subscriber: Callable[[_T], None] | ref
    is_silenced: bool = False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({hex(self.uid)}, {self._get_callable_name(self.subscriber_callable)},"
            + f" {self.is_silenced})"
        )

    def __str__(self) -> str:
        return self._get_callable_name(self.subscriber_callable)

    def __eq__(self, other) -> bool:
        return (
            self.uid == other.uid and self.subscriber_callable is other.subscriber_callable
            if isinstance(other, _SignalElement)
            else NotImplemented
        )

    def __call__(self, value: _T) -> None:
        return self.subscriber_callable(value)

    @property
    def subscriber_callable(self) -> Callable[[_T], None]:
        if isinstance(self.subscriber, ref):
            return self.subscriber()  # type: ignore
        return self.subscriber

    @staticmethod
    def _get_callable_name(callable_) -> str:
        if isinstance(callable_, (_SignalElement, _Connection)):
            return f"{callable_}"
        try:
            return f"{callable_.__name__}"
        except AttributeError:
            return f"{callable_}"


@attrs(slots=True, auto_attribs=True, init=False)
class Signal(Generic[_T]):
    """
    A representation of an observable action which can be communicated.

    Parameters
    ----------
    Generic : _T
        The result of the action took.

    Attributes
    ----------
    subscribers: list[_SignalElement]
        A list of interested parties which will be called when the action of interest is taken.
    name: str | None
        The user friendly name of this signal, None by default.
    _dead_subscribers: bool
        If there exists a subscriber which needs to be collected by the garbage collector.
    """

    subscribers: list[_SignalElement]
    name: str | None
    _dead_subscribers: bool

    @overload
    def __init__(self, *, subscribers: None = None, name: str | None = None) -> None:
        pass

    @overload
    def __init__(
        self, *args: Sequence[_SignalElement], subscribers: Sequence[_SignalElement], name: str | None = None
    ) -> None:
        pass

    @overload
    def __init__(self, *args: _SignalElement, subscribers: None = None, name: str | None = None) -> None:
        pass

    def __init__(self, *args, subscribers: Sequence[_SignalElement] | None = None, name: str | None = None) -> None:
        self.name = name
        if len(args) > 1 and subscribers is None:
            self.subscribers = list(args)
        elif len(args) == 1:
            self.subscribers = list(chain(args)) + list(subscribers) if subscribers else []
        elif subscribers is not None:
            self.subscribers = list(subscribers)
        else:
            self.subscribers = []
        self._dead_subscribers = False

    def __str__(self) -> str:
        if self.name:
            return f"{self.name}<{', '.join(str(s) for s in self)}>"
        else:
            return f"<{', '.join(str(s) for s in self)}>"

    def __missing__(self, key) -> NoReturn:
        raise KeyError(key)

    def __getitem__(self, key) -> _SignalElement:
        for value in self.subscribers:
            if value == key:
                return value
        return self.__missing__(key)

    def __contains__(self, value: _SignalElement) -> bool:
        return any(v == value for v in self.subscribers)

    def __len__(self) -> int:
        return len(self.subscribers)

    def __iter__(self) -> Iterator[_SignalElement[_T]]:
        return iter(self.subscribers)

    def __bool__(self):
        return bool(self.subscribers)

    @_remove_garbage
    def clear(self, *instances: object) -> None:
        """
        Removes all subscribers for a signal.

        Parameters
        ----------
        instances : object
            The instances to remove subscribers from.
        """
        subscribers: list[_SignalElement[_T]] = []
        if len(instances):
            for element in self.subscribers:
                if any(id(instance) == element.uid for instance in instances):
                    log.debug(f"{self.__class__.__name__} removed {element} from {self}")
                else:
                    subscribers.append(element)
        self.subscribers = subscribers

    @_remove_garbage
    def connect(self, subscriber: Callable[[_T], None], instance: object, weak: bool = True) -> None:
        """
        Associates a subscriber to this signal, to be called when this signal receives an action.

        Parameters
        ----------
        subscriber : Callable[[_T], None]
            The subscriber, which takes the result of the action from this signal.
        instance : object
            The object which is interested in `subscriber`.
        weak : bool, optional
            If the subscriber should automatically be removed when it is no longer required, by default True

        Notes:
            For any given object, it can only be connected to a signal once.  This is done with the intention of
            stopping unknown state, as it is indeterminate which will be called first.  If this is done, the second
            call will be ignored and a warning will be provided.
        """
        if weak:
            finalize(subscriber, self._remove_subscriber)  # type: ignore
            subscriber = ref(subscriber)  # type: ignore
        element: _SignalElement = _SignalElement(id(instance), subscriber)

        if element not in self:
            log.debug(f"{instance.__class__.__name__} adding {element} to {self}")
            self.subscribers.append(element)
        else:
            log.warning(f"{instance.__class__.__name__} failed to add {element} to {self}")

    @_remove_garbage
    def disconnect(self, subscriber: Callable[[_T], None], instance: object | None) -> None:
        """
        Allows for a subscriber with or without respect to a given instance to no longer receive actions from
        this signal.

        Parameters
        ----------
        subscriber : Callable[[_T], None]
            The subscriber, which took the result of the action from this signal.
        instance : object | None
            The object which was interested in `subscriber`.
        """
        element: _SignalElement = _SignalElement(id(instance), subscriber)
        for idx, sub in enumerate(self.subscribers):
            if sub == element:
                del self.subscribers[idx]
                log.debug(f"{self.__class__.__name__} removed {element} from {self}")
                break

    @_remove_garbage
    def emit(self, value: _T, instance: object) -> None:
        """
        Emits an action to `subscribers`.

        Parameters
        ----------
        value : _T
            The result of an action taken.
        instance : object
            The object associated with this action.
        """
        for subscriber in self.subscribers:
            if subscriber.uid == id(instance) and not subscriber.is_silenced:
                log.debug(f"{self.name} notifying {subscriber} of {value}")
                subscriber(value)

    @_remove_garbage
    def is_silenced(self, instance: object) -> bool:
        """
        Determines if `instance` has silenced their subscriber with respect to this signal.

        Parameters
        ----------
        instance : object
            The object which could have silenced their subscriber.

        Returns
        -------
        bool
            If `instance` has silenced their subscriber.
        """
        return not any(sub.uid == id(instance) and not sub.is_silenced for sub in self)

    @_remove_garbage
    def silence(self, instance: object, is_silenced: bool) -> None:
        """
        Sets the silence status for `instance`'s subscriber.

        Parameters
        ----------
        instance : object
            The object which is setting their subscriber's silence status.
        is_silenced : bool
            The new silence status to be set.
        """
        if DEBUG >= log.level:
            _prior_silenced = self.is_silenced(instance)
        for idx, sub in enumerate(self.subscribers):
            if sub.uid == id(instance):
                self.subscribers[idx].is_silenced = is_silenced
        if DEBUG >= log.level and _prior_silenced != is_silenced:  # type: ignore
            log.debug(f"{instance}::{self.name} {'silenced' if is_silenced else 'unsilenced'}")

    def _remove_garbage_subscribers(self) -> None:
        """
        Removes subscribers that need to be garbage collected.
        """
        if self._dead_subscribers:
            self._dead_subscribers = False
            self.subscribers = [
                r for r in self.subscribers if not (isinstance(r.subscriber, ReferenceType) and r.subscriber() is None)
            ]

    def _remove_subscriber(self) -> None:
        """
        Notifies the signal that subscribers need to be cleaned before any action is taken.
        """
        log.debug(f"{self.name} queued garbage collection")
        self._dead_subscribers = True


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class SignalInstance(Generic[_T]):
    """
    A representation of a signal with respect to a specific provided instance.

    Parameters
    ----------
    Generic : _T
        The value provided by the signal.

    Attributes
    ----------
    instance: object
        The instance of interest with respect to `signal`.
    signal: Signal[_T]
        The underlying signal.

    Notes
    -----
    The primary purpose of this class is to encapsulate the signal with respect to the instance.
    By doing this, it makes it much hard to mistakenly override other instance's signal-subscriber relationships.
    It also provides a series of helper methods to ease use with the signal architecture.
    """

    instance: object
    signal: Signal[_T]

    def __str__(self) -> str:
        if self.signal.name is None:
            for name in dir(self.instance):
                if self.signal is getattr(self.instance, name):
                    self.signal.name = name
                    break
            else:
                log.warning(f"{self.__class__.__name__} could not find {self.signal} in {self.instance}")
                return repr(self)
        return f"{self.instance}::{self.signal.name}"

    def __missing__(self, key) -> NoReturn:
        raise KeyError(key)

    def __getitem__(self, key) -> _SignalElement:
        for value in filter(lambda v: v.uid == id(self.instance), self.signal):
            if value == key:
                return value
        return self.__missing__(key)

    def __contains__(self, value: _SignalElement) -> bool:
        return any(v == value and v.uid == id(self.instance) for v in self.signal)

    def __len__(self) -> int:
        return len(list(iter(self)))

    def __iter__(self) -> Iterator[_SignalElement[_T]]:
        return iter(filter(lambda v: v.uid == id(self.instance), self.signal))

    def __bool__(self) -> bool:
        return len(self) > 0

    @property
    def is_silenced(self) -> bool:
        """
        Determines if this has been silenced.

        Returns
        -------
        bool
            If this has been silenced.
        """
        return self.signal.is_silenced(self.instance)

    def clear(self) -> None:
        """
        Removes all subscribers for a signal.
        """
        self.signal.clear(self.instance)

    @overload
    def link(
        self,
        signal_instance: SignalInstance[_T],
        converter: None = None,
        condition: Callable[[_T], bool] | None = None,
    ) -> None:
        ...

    @overload
    def link(
        self,
        signal_instance: SignalInstance[_U],
        converter: Callable[[_T], _U],
        condition: Callable[[_T], bool] | None = None,
    ) -> None:
        ...

    def link(
        self,
        signal_instance: SignalInstance[_U],
        converter: Callable[[_U], _T] | None = None,
        condition: Callable[[_U], bool] | None = None,
    ) -> None:
        """
        Links another signal instance to this signal instance.

        Parameters
        ----------
        signal_instance : SignalInstance[_U]
            The other signal instance which is interested in this signal instance.
        converter : Callable[[_T], _U] | None, optional
            The converter required to understand the actions of this signal in terms of the provided
            signal instance, by default None
        condition : Callable[[_T], bool] | None, optional
            The conditions required to forward_action this signal instance's actions to the provided
            signal instance , by default None
        """
        if not isinstance(signal_instance, SignalInstance):
            log.warning(f"{self} can only link {self.__class__.__name__}, not {signal_instance}")
        connection: _Connection[_T, _U] = _Connection(self, signal_instance, converter, condition)
        log.info(f"{self} linking {connection}")
        signal_instance.connect(connection, False)

    def connect(self, subscriber: Callable[[_T], None], weak: bool = True) -> None:
        """
        Associates a subscriber to this signal, to be called when this signal instance receives an action.

        Parameters
        ----------
        subscriber : Callable[[_T], None]
            The subscriber, which takes the result of the action from this signal instance.
        weak : bool, optional
            If the subscriber should automatically be removed when it is no longer required, by default True
        """
        log.debug(f"{self} adding {_SignalElement._get_callable_name(subscriber)}")
        self.signal.connect(subscriber, self.instance, weak)

    def disconnect(self, subscriber: Callable[[_T], None]) -> None:
        """
        Allows for a subscriber to no longer receive actions from this signal instance.

        Parameters
        ----------
        subscriber : Callable[[_T], None]
            The subscriber, which took the result of the action from this signal instance.
        """
        log.info(f"{self} removing {_SignalElement._get_callable_name(subscriber)}")
        self.signal.disconnect(subscriber, self.instance)

    def emit(self, value: _T) -> None:
        """
        Emits an action to its subscribers.

        Parameters
        ----------
        value : _T
            The result of an action taken.
        """
        if not self.is_silenced:
            log.info(f"{self} emitting {value} to <{', '.join(str(v) for v in iter(self))}>")
            self.signal.emit(value, self.instance)

    def silence(self, silence: bool) -> None:
        """
        Sets the silence status for this signal instance.

        Parameters
        ----------
        is_silenced : bool
            The new silence status to be set.
        """
        self.signal.silence(self.instance, silence)


@attrs(auto_attribs=True)
class SignalTester:
    """
    A context manager for testing that a signal is emitted.

    Attributes
    ----------
    signal: SignalInstance
        The signal to under test.
    count: int = 0
        The amount of times the signal was called.
    """

    signal: SignalInstance
    count: int = 0

    def increment_counter(self, *_) -> None:
        self.count += 1

    def __enter__(self) -> SignalTester:
        self.signal.connect(self.increment_counter, weak=False)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.signal.disconnect(self.increment_counter)


@attrs(auto_attribs=True)
class SignalBlocker:
    """
    A context manager for blocking specific signals.

    Attributes
    ----------
    signal: SignalInstance | Sequence[SignalInstance]
        The signals to be blocked temporarily.
    _silenced: bool | Sequence[bool]
        The prior state of the signals.

    Notes
    -----
        This context manager ensures that signals will remain silenced if they were set prior.
    """

    signal: SignalInstance | Sequence[SignalInstance]

    def _signal_names(self) -> str:
        if isinstance(self.signal, SignalInstance):
            return f"<{self.signal}>"
        return f"<{', '.join(str(s) for s in self.signal)}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}{self._signal_names()}"

    def __enter__(self):
        log.debug(f"{self.__class__.__name__} blocking {self._signal_names()}")
        if isinstance(self.signal, SignalInstance):
            self._silenced = self.signal.is_silenced
            self.signal.silence(True)
        else:
            self._silenced = [signal.is_silenced for signal in self.signal]
            for signal in self.signal:
                signal.silence(True)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        log.debug(f"{self.__class__.__name__} stop blocking {self._signal_names()}")
        if isinstance(self.signal, Sequence):
            for signal, silenced in zip(self.signal, self._silenced):  # type: ignore
                signal.silence(silenced)
        else:
            self.signal.silence(self._silenced)  # type: ignore


@attrs(slots=True, auto_attribs=True, frozen=True, eq=False, hash=True)
class Action(Generic[_T]):
    """
    A representation of an action.

    Parameters
    ----------
    Generic : _T
        The type of actions that are applied.

    Attributes
    ----------
    actor: UndoRedoActor | None
        The object that is responsible for this action.
    action: Callable[[], _T]
        The action taken.
    reverse_action: Callable[[], _T]
        The action required to undo `action`.
    name: str
        A name, purely for easier debugging.
    """

    actor: UndoRedoActor | None
    action: Callable[[], _T]
    reverse_action: Callable[[], _T]
    name: str = ""

    def __str__(self) -> str:
        return self.name or self.action.__name__

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.actor == other.actor if isinstance(other, Action) else NotImplemented


class _Object(Generic[_T]):
    _model: _T
    _model_prior: _T

    def link_child(self, child: Object) -> None:
        """
        A function which permits extension for linking children.

        Parameters
        ----------
        child: Object
            The child to be linked into the system.
        """

    def initialize_state(self, model: _T, *args, **kwargs) -> None:
        """
        The initialization of this widget and its children.

        Parameters
        ----------
        model : _T
            The initial state of the system.
        """

    def change_state(self, model: _T) -> None:
        """
        Provides an change_state to this widget's components with respect to a new model.

        Parameters
        ----------
        model : _T
            The new model that this instance must change_state to represent.
        """


@attrs(slots=True, auto_attribs=True)
class UndoRedo(Generic[_T]):
    """
    The concrete implementation of undoing and redoing actions.

    Parameters
    ----------
    Generic : _T
        The type of actions that are applied.

    Attributes
    ----------
    model: _T
        The starting state of the controller.
    undo_stack: deque[Action[_T]] = Factory(lambda: deque(maxlen=1000000000))
        A sequence of actions taken, which can be undone.
    redo_stack: deque[Action[_T]] = Factory(deque)
        A sequence of undone actions, which can be reapplied.
    """

    model: _T
    undo_stack: deque[Action[_T]] = Factory(lambda: deque(maxlen=1000000000))
    redo_stack: deque[Action[_T]] = Factory(deque)

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(starting_value={self.model}, "
            + f"actions=<{', '.join(str(a) for a in self.undo_stack)}>, "
            + f"undone_actions=<{', '.join(str(a) for a in self.redo_stack)}>)"
        )

    def do(self, action: Action[_T]) -> None:
        """
        Adds an action to the undo stack.

        Parameters
        ----------
        action : Action[_T]
            The action performed.
        """
        self.undo_stack.append(action)
        self.redo_stack.clear()
        log.debug(f"{self.__class__.__name__}<{self.model}> has done {action}")

    @property
    def can_undo(self) -> bool:
        """
        If `model` composed with `undo_stack` is equal to `model`.

        Returns
        -------
        bool
            If any actions exist that can be undone.
        """
        return bool(len(self.undo_stack))

    def undo(self) -> Callable[[], _T]:
        """
        Undoes the last action.

        Returns
        -------
        Callable[[], _T]
            The required action to be performed.
        """
        action: Action[_T] = self.undo_stack.pop()
        self.redo_stack.append(action)
        log.debug(f"{self.__class__.__name__}<{self.model}> has undone {action}")
        return action.reverse_action

    @property
    def can_redo(self) -> bool:
        """
        If there exists any actions that have been undone.

        Returns
        -------
        bool
            If any actions exist that can be redone.
        """
        return bool(len(self.redo_stack))

    def redo(self) -> Callable[[], _T]:
        """
        Redoes the last action.

        Returns
        -------
        Callable[[], _T]
            The required action to be performed.
        """
        action: Action[_T] = self.redo_stack.pop()
        self.undo_stack.append(action)
        log.debug(f"{self.__class__.__name__}<{self.model}> has redone {action}")
        return action.action


class UndoRedoActor(_Object[_T]):
    """
    The bare bones implementation required for any component which desires to work inside an undo and redo
    system.

    Parameters
    ----------
    _Object : _T
        The type of the actions being performed.

    Attributes
    ----------
    __children__: Mapping[int, str]
        A mapping of children and their associated name with respect to `model`.
    model: _T
        The model of the actions being performed.
    _model_prior: _T
        A hacky work-around to allow finding the prior state of a given system after an action has been performed,
        but before it has been applied to the undo and redo system.
    """

    __children__: Mapping[int, str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<0x{(id(self) % 0xFF):02X}>"

    @final
    def get_child_attribute(self, actor: UndoRedoActor) -> str:
        """
        Determines the associated field of a child actor with respect to `model`.

        Parameters
        ----------
        actor : UndoRedoActor
            The child actor.

        Returns
        -------
        str
            The associated field for `actor`.
        """
        return self.__children__[id(actor)]

    @final
    def compose_child_action(self, action: Action) -> Action[_T]:
        """
        Provides an action for this instance from a child's action.

        Parameters
        ----------
        action : Action
            The child action taken.

        Returns
        -------
        Action[_T]
            This instance's action, which composed the child's action.
        """
        if action.actor is None:
            log.error(f"{self} cannot determine actor of {action}")
            raise ValueError(f"Cannot determine actor of {action}")
        attribute_name: str = self.get_child_attribute(action.actor)
        return Action(
            self,
            lambda: evolve(self._model, **{attribute_name: action.action()}),
            lambda: evolve(self._model, **{attribute_name: action.reverse_action()}),
        )


class UndoRedoForwarder(UndoRedoActor[_T]):
    """
    An object inside an undo and redo system which seeks to forward_action its action and its children's actions
    to another object to handle undo and redo logic.

    Parameters
    ----------
    UndoRedoActor : _T
        The type of the actions being performed.

    Signals
    -------
    action_performed: SignalInstance[Action[_T]]
        A signal that emits the action that was performed for any action of this instance.
    """

    _action_performed: Signal[Action[_T]] = Signal(name="action_performed")

    @property
    def action_performed(self) -> SignalInstance[Action[_T]]:
        return SignalInstance(self, self._action_performed)

    def link_child(self, child: UndoRedoForwarder) -> None:
        """
        Links a child to a parent, such that the parent can forward_action all child actions.

        Parameters
        ----------
        child : UndoRedoForwarder
            The child to be linked.
        """
        child.action_performed.connect(self.forward_action, weak=False)
        super().link_child(child)  # type: ignore

    def change_state(self, model: _T) -> None:
        """
        Applies `model` to this instance.

        Parameters
        ----------
        model : _T
            The model to be applied.
        """
        try:
            self.do(model, self._model_prior)
        except AttributeError:
            log.warning(f"{self} does not define a prior model")
            self.do(model, None)  # type: ignore
        super().change_state(model)

    @final
    def do(self, model_prior: _T, model_after: _T) -> None:
        """
        Emits that an action has been performed.

        Parameters
        ----------
        model_prior : _T
            The prior state of the model.
        model_after : _T
            The new state of the model.
        """
        self.action_performed.emit(Action(self, lambda: model_after, lambda: model_prior, "change_state"))

    @final
    def forward_action(self, action: Action) -> None:
        """
        Forwards a child's action.

        Parameters
        ----------
        action : Action
            The child's action to be forwarded.
        """
        self.action_performed.emit(self.compose_child_action(action))


class UndoRedoRoot(UndoRedoActor[_T]):
    """
    An object inside an undo and redo system which manages their own undo and redo stack.

    Parameters
    ----------
    UndoRedoActor : _T
        The type of the actions being performed.

    Attributes
    ----------
    __undo_redo__: UndoRedo[_T]
        The internal undo and redo controller.
    """

    __undo_redo__: UndoRedo[_T]

    def initialize_state(self, model: _T, *args, **kwargs) -> None:
        """
        Required actions for an undo and redo controller on initialize_state up.

        Notes
        -----
        This does not use __init__ to be compatible with `Object`.
        """
        self._setup_undo_redo()
        super().initialize_state(model, *args, **kwargs)

    def change_state(self, model: _T) -> None:
        """
        Applies `model` to this instance.

        Parameters
        ----------
        model : _T
            The model to be applied.
        """
        try:
            self.do(Action(self, lambda: model, lambda: self._model_prior))
        except AttributeError:
            log.warning(f"{self} does not define a prior model")
            self.do(Action(self, lambda: model, lambda: None))  # type: ignore
        super().change_state(model)

    @final
    def _setup_undo_redo(self, undo_redo: UndoRedo[_T] | None = None) -> None:
        """
        Creates an internal undo and redo controller.

        Parameters
        ----------
        undo_redo : UndoRedo[_T] | None, optional
            The internal undo and redo controller to be used, by default None
        """
        self.__undo_redo__ = UndoRedo(self.model) if undo_redo is None else undo_redo

    def link_child(self, child: UndoRedoForwarder) -> None:
        """
        Links a child to a parent, such that the parent can undo and redo all child actions.

        Parameters
        ----------
        child : UndoRedoForwarder
            The child to be linked.
        """
        child.action_performed.connect(self.process_action)
        super().link_child(child)  # type: ignore

    @final
    def process_action(self, action: Action) -> None:
        """
        Processes an action performed by a child and puts it in terms of how to undo and redo it from this parent.

        Parameters
        ----------
        action : Action
            The action performed.
        """
        self.do(self.compose_child_action(action))

    @final
    def do(self, action: Action[_T], *, apply_action: bool = False) -> None:
        """
        Adds an action to the undo stack.

        Parameters
        ----------
        action : Action[_T]
            The action performed.
        apply_action: bool = False
            If the action should be applied to the model.
        """
        self.__undo_redo__.do(action)
        if apply_action:
            prior = self.model
            self.model = action.action()
            log.info(f"{self} has done {action}: {prior} -> {self.model}")
            if prior == self.model:
                log.warning(f"{action} has not resulted in a difference in model for {self}, {self.model}")

    @property
    @final
    def can_undo(self) -> bool:
        """
        If `model` composed with `undo_stack` is equal to `model`.

        Returns
        -------
        bool
            If any actions exist that can be undone.
        """
        return self.__undo_redo__.can_undo

    @final
    def undo(self) -> None:
        """
        Undoes the last action.

        Returns
        -------
        Callable[[], _T]
            The required action to be performed.
        """
        prior = self.model
        self.model = self.__undo_redo__.undo()()  # type: ignore
        log.info(f"{self} has undone {self.__undo_redo__.redo_stack[-1]} -> {self.model}")
        if prior == self.model:
            log.warning(
                f"{self.__undo_redo__.redo_stack[-1]} undo has not resulted in a difference in model for {self}, "
                + f"{prior} -> {self.model}"
            )

    @property
    @final
    def can_redo(self) -> bool:
        """
        If there exists any actions that have been undone.

        Returns
        -------
        bool
            If any actions exist that can be redone.
        """
        return self.__undo_redo__.can_redo

    @final
    def redo(self) -> None:
        """
        Redoes the last action.

        Returns
        -------
        Callable[[], _T]
            The required action to be performed.
        """
        prior = self.model
        self.model = self.__undo_redo__.redo()()  # type: ignore
        log.info(f"{self} has undone {self.__undo_redo__.undo_stack[-1]} -> {self.model}")
        if prior == self.model:
            log.warning(
                f"{self.__undo_redo__.undo_stack[-1]} redo has not resulted in a difference in model for {self}, "
                + f"{prior} -> {self.model}"
            )


class ConnectionError(ValueError):
    """
    An exception that is raised when a subscriber was failed to be connected to a signal.
    """


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class BaseModel:
    """
    An extendible model that is frozen.
    """

    setup_signals: ClassVar[bool] = True


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _SignalAttribute(Generic[_T]):
    attribute: str
    signal_attribute: str

    def __str__(self) -> str:
        return f"<{self.attribute}>"

    def get_attribute(self, instance) -> _T:
        return getattr(instance, self.attribute)

    def get_signal_instance(self, instance) -> SignalInstance[_T]:
        signal = getattr(instance, self.signal_attribute)
        if not isinstance(signal, SignalInstance):
            log.warning(f"{self}::{signal} should be a signal instance")
        return signal

    def emit(self, instance) -> None:
        signal: SignalInstance = self.get_signal_instance(instance)
        signal.emit(self.get_attribute(instance))

    @classmethod
    def from_attribute(cls, attribute: str):
        return cls(attribute, f"_{attribute}_updated")


class EmittingProperty(Generic[_T]):
    __slots__ = ("name", "attributes", "fget", "fset", "__doc__")

    name: str | None
    attributes: Sequence[_SignalAttribute]
    fget: Callable[[Object], _T] | None
    fset: Callable[[Object, _T], None] | None

    def __init__(
        self,
        attributes: Sequence[str] | Sequence[_SignalAttribute],
        fget: Callable[[Object], _T] | None = None,
        fset: Callable[[Object, _T], None] | None = None,
        name: str | None = None,
        doc: str | None = None,
    ) -> None:
        self.name = name
        if isinstance(next(iter(attributes), None), str):
            self.attributes = [_SignalAttribute.from_attribute(a) for a in attributes]  # type: ignore
        else:
            self.attributes = attributes  # type: ignore
        self.fget = fget
        self.fset = fset
        self.__doc__ = doc

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(<{', '.join(str(a) for a in self.attributes)}>, {self.fget}, "
            f"{self.fset}, {self.name}, {self.__doc__})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(<{', '.join(str(a) for a in self.attributes)}>, "
            f"{self.fget.__name__ if self.fget else None}, {self.fset.__name__ if self.fset else None}, "
            f"{self.name}, {self.__doc__})"
        )

    def __get__(self, instance: Object, owner=None):
        if instance is None:
            return self
        elif self.fget is None:
            log.error(f"{self} was attempted to be read")
            raise AttributeError(f"Cannot read attribute {self.name}")
        return self.fget(instance)

    def __set__(self, instance: Object, value: _T) -> None:
        if self.fset is None:
            log.error(f"{self} was attempted to be set")
            raise AttributeError(f"Cannot set attribute {self.name}")
        self._fset(instance, value)

    def emit(self, instance: Object) -> None:
        if self.name is None:
            log.error(f"{self} did not define a name")
            raise TypeError("Name is None")
        _SignalAttribute.from_attribute(self.name).emit(instance)

    def _fset(self, instance: Object, value: _T) -> None:
        assert self.fset is not None
        if self.name is None:
            log.error(f"{self} did not define a name")
            raise TypeError("Name is None")
        with instance.signal_blocker:
            self.fset(instance, value)
        instance.updated.emit(instance.model)
        self.emit(instance)

    def getter(self, fget: Callable[[Any], _T] | None):
        return type(self)(self.attributes, fget, self.fset, self.name, self.__doc__)

    def setter(self, fset: Callable[[Any, _T], None] | None):
        return type(self)(self.attributes, self.fget, fset, self.name, self.__doc__)


def emitting_property(*args: str):
    """
    Provides a property descriptor that emits for the associated signals provided as `args`.

    Parameters
    ----------
    *args: str
        The attributes composed by this property.
    """

    def emitting_property(fget: Callable[[Any], _T]) -> EmittingProperty[_T]:
        return EmittingProperty(args, fget, name=fget.__name__, doc=fget.__doc__)

    return emitting_property


def _getter(name: str):
    def _getter(self):
        return getattr(getattr(self, "_model"), name)

    return _getter


def _setter(name: str, signal_attributes: Sequence[_SignalAttribute] = []):
    def _setter(self: Object, value) -> None:
        log.debug(f"{self}::{name} -> {value}")
        setattr(self, "model", evolve(getattr(self, "_model"), **{name: value}))

        for signal_attribute in signal_attributes:
            signal = signal_attribute.get_signal_instance(self)
            if not isinstance(signal, SignalInstance):
                log.warning(f"{self}::{signal} should be a signal instance")
            signal.emit(signal_attribute.get_attribute(self))

    return _setter


class ObjectMeta(type(QObject)):
    """
    The meta class responsible for the dynamic generation of GUI objects.

    Model Descriptors
    -----------------
    In a GUI component there exists three key components: a model, a commander, and a series of children components.
    The user communicates through the view, however in itself it cannot interpret the desire of the user.  Instead,
    it is required for the commander to make sense of each action.  To scope each GUI component, it is critical that
    the developer  defines a model, which serves as the invariant of possible state.  Through this interface, every
    possible state of the GUI is required to exist.  To encourage this practice, the model is defined as inner class
    inside the defined object.  Through this definition, we are able to create a series of descriptors which enforce
    this requirement.  Furthermore, the model does not permit mutation.  This ensures that no action can be taken
    without the explicit utilization of descriptors and announcement of action.

    Signal Generation
    -----------------
    Signals are common component of any GUI component.  They are derivative of action into state.  However, by nature,
    a signal is a class variable.  An action an object takes is most commonly defined by the type of object.
    Unfortunately, this distinction is not obvious after the creation of an instance.  This derives from the natural
    fact that action is taken by instances, not types.  To this respect, the common use case does not often take
    advantage of generality of the signal.  Instead, it is common that the developer wishes to almost solely utilize
    the signal instance.  To make GUI more intuitive to create, we've made it so class signals can be defined by
    defining a class variable with an annotation of 'SignalInstance'.

    Private Signals
    ---------------
    By default an object generates signals for the attributes of its model.  These are explicitly made private as
    the implementation of a GUI component is not ensured.  Specifically, allowing a parent component to view its
    child's components would allow the parent component to communicate to its grandchildren.  This creates undesired
    coupling and is to be avoided.  Instead, these components are created to solely aid the commander to define the
    interpretation of a user action as concisely as possible.

    Property Signals
    ----------------
    Many sub-components of a larger components can also change standard throughout time.  To make the internal
    structure of components less brittle, properties are a common interface to compose and hide additional complexity.
    This is also supported by objects.  Through the use of `emitting_property`, a signal is dynamically generated
    for the property in additional to the common property descriptor interface.
    """

    @classmethod
    def _get_user_signal_annotations(cls, name, bases, attrs) -> set[str]:
        user_defined_signals: set[str] = set()
        object_bases: list[ObjectMeta] = [base for base in bases if isinstance(base, cls)]
        for object_base in object_bases:
            for ann_name, annotation in get_type_hints(object_base).items():
                ann_type = getattr(annotation, "__origin__", None)
                if isinstance(ann_type, type) and issubclass(ann_type, SignalInstance):
                    user_defined_signals.add(ann_name)

        for ann_name, annotation in attrs.get("__annotations__", {}).items():
            ann_type = getattr(annotation, "__origin__", None)
            if isinstance(ann_type, type) and issubclass(ann_type, SignalInstance):
                user_defined_signals.add(ann_name)

        log.debug(f"{name} found {', '.join(user_defined_signals)} as user defined signals")
        return user_defined_signals

    def __new__(cls, name, bases, attrs):
        log.debug(f"creating {name}")

        # A model is defined for each object and we enforce that it is a BaseModel.
        # This is to enforce that the Model will always be frozen.
        Model_ = attrs.get("Model", BaseModel)
        if not issubclass(Model_, BaseModel):
            log.warning(f"{Model_.__name__} should inherit from {BaseModel.__name__} to enforce frozen attributes")

        # A user can define a signal by writing 'signal_name: SignalInstance[type]'
        # We view the annotations to get this information
        user_defined_signals: list[str] = list(cls._get_user_signal_annotations(name, bases, attrs))

        # Fields that are defined inside the model provide private signals.
        private_defined_signals: list[str] = (
            [f"_{a}_updated" for a in get_annotations(Model_).keys()] if Model_.setup_signals else []  # type: ignore
        )

        # We allow for properties to also emit signals.  This is to simplify logic of composing child types.
        # To achieve this we enforce that developer must use 'emitting_property'.
        # This defines a private attribute 'attributes' which provides which attributes it composes.
        # When one of the types which it composes emits, it will emit the property of itself.
        # We set up the signal here and provide the listener information to the instance for handling later.
        # We also forward_action the property descriptor into the object, so it can be used properly.
        listeners: Mapping[str, Sequence[_SignalAttribute]] = {}
        for attribute_name, attribute in Model_.__dict__.items():
            if isinstance(attribute, EmittingProperty):
                attrs[attribute_name] = attribute
                private_defined_signals.append(f"_{attribute_name}_updated")
                emitters: Sequence[_SignalAttribute] = attribute.attributes
                listeners |= {attribute_name: emitters}
        attrs["__listeners__"] = listeners
        log.debug(f"{name} found {', '.join(private_defined_signals)} as privately defined signals")

        # We store the signals inside a class variable so we can mute all signals from an object, if desired.
        attrs |= {"__signals__": []}
        for signal_name in user_defined_signals + private_defined_signals:
            log.debug(f"{name} created {signal_name} as a {Signal.__name__}")
            signal = Signal(name=signal_name)
            attrs |= {signal_name: signal}
            attrs["__signals__"].append(signal)

        # We forward_action all attributes from the model as descriptors into the object.
        # This is so the user can modify the model and for it to retain a valid state.
        # We also allow for the model to not set up signals.  If the model does not want signals, the setter
        # will work, but no events will be emitted other than the standard events for updating the model.
        annotations = attrs.get("__annotations__", {})
        for ann_name, annotation in get_annotations(Model_).items():  # type: ignore
            if ann_name in attrs and isinstance(attrs[ann_name], Signal):
                log.warn(f"{name} cannot create property for {ann_name} due to signal naming conflicts")
            if ann_name not in attrs:
                if Model_.setup_signals:
                    attrs[ann_name] = property(
                        _getter(ann_name), _setter(ann_name, [_SignalAttribute(ann_name, f"_{ann_name}_updated")])
                    )
                    log.debug(f"{name} created property {ann_name} -> _{ann_name}_updated")
                else:
                    attrs[ann_name] = property(_getter(ann_name), _setter(ann_name))
                    log.debug(f"{name} created property {ann_name}")
                if ann_name not in annotations:
                    annotations |= {ann_name: annotation}

        # We finally make the class with all the extra attributes added.
        return super().__new__(cls, name, bases, attrs)


class Object(_Object, metaclass=ObjectMeta):
    """
    The heart of any GUI component.  This component bridges the gap between action and state; it provides the
    interface for interpreting events derived from signals and converts them into a function onto its model.

    Attributes
    ----------
    __signals__: Sequence[Signal]
        The list of all signals associated for a given type of object.
    __listeners__: Mapping[str, Sequence[str]]
        The list of all internal subscribers for a given type of object.
    updated: SignalInstance[BaseModel]
        A signal announces a change in state of an instance of an object.
    """

    __signals__: Sequence[Signal]
    __listeners__: Mapping[str, Sequence[_SignalAttribute]]

    updated: SignalInstance[BaseModel]

    class Model(BaseModel):
        pass

    @final
    def __init__(self, model: BaseModel, parent: Object | None = None, *args, **kwargs) -> None:
        self._parent = parent
        self._model = model
        self._setup_listeners__()
        self.initialize_state(model, *args, **kwargs)
        try:
            super().__init__(parent)  # type: ignore
        except TypeError:
            super().__init__()

    def __repr__(self) -> str:
        if self._parent is not None:
            return f"{self.__class__.__name__}({self._model}, {self._parent})"
        else:
            return f"{self.__class__.__name__}({self._model})"

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        return SignalInstance(self, value) if isinstance(value, Signal) else value

    @final
    def _setup_listeners__(self) -> None:
        """
        Creates subscribers for internal signals of properties to facilitate seamless use.
        """
        for listener_name, emitter_names in self.__listeners__.items():

            def get_listener_value(_) -> Any:
                return getattr(self, listener_name)

            listener_signal: SignalInstance = getattr(self, f"_{listener_name}_updated")
            if listener_signal is None:
                log.critical(f"{self.__class__.__name__} could not find {listener_signal}")
                raise AttributeError(f"{self} has no attribute '{listener_signal}'")
            for emitter_attr in emitter_names:
                # two-way connection
                def get_other_listener_value(_) -> Any:
                    return getattr(self, emitter_attr.signal_attribute)

                emitter_attr.get_signal_instance(self).link(listener_signal, get_listener_value)
                listener_signal.link(emitter_attr.get_signal_instance(self), get_other_listener_value)

    @property
    @final
    def signals(self) -> Sequence[SignalInstance]:
        """
        Provides every signal associated with an object.

        Returns
        -------
        Sequence[SignalInstance]
            Every signal associated with an instance.
        """
        return [SignalInstance(self, signal) for signal in self.__signals__]

    @property
    @final
    def signal_blocker(self) -> SignalBlocker:
        """
        Provides a context manager to block all signals of this instance.

        Returns
        -------
        SignalBlocker
            A context manager which can block every signal of this instance.
        """
        return SignalBlocker(self.signals)

    @property
    @final
    def model(self) -> BaseModel:
        """
        The representation of the current state of this instance.

        Returns
        -------
        BaseModel
            The current state of this instance.
        """
        return self._model

    @model.setter
    @final
    def model(self, value: BaseModel) -> None:
        self._model_prior = self.model
        with self.signal_blocker:
            self._model = value
            self.change_state(value)
        self.updated.emit(value)

    @final
    def connect_child(
        self,
        attribute: str,
        child: Object,
        child_signal_name: str = "updated",
        child_attribute: str = "model",
        link_child: bool = True,
    ) -> None:
        if link_child:
            self.link_child(child)

        if not hasattr(self, attribute):
            raise ConnectionError(f"{self} does not have {attribute} inside its model")
        if not hasattr(child, child_signal_name):
            raise ConnectionError(f"{child} does not have {child_signal_name} as a valid signal")
        if not hasattr(child, child_attribute):
            raise ConnectionError(f"{child} does not have {child_attribute} inside its model")
        if getattr(self, attribute) != getattr(child, child_attribute):
            raise ConnectionError(f"{self}::{attribute} must equal {child}::{child_attribute}")

        def forward_value(value) -> None:
            model = getattr(self, attribute)
            setattr(self, attribute, value)
            if model == getattr(self, attribute):
                with getattr(child, "signal_blocker"):
                    setattr(child, child_attribute, model)

        signal: SignalInstance = getattr(self, child_signal_name)
        signal.connect(forward_value)


class Widget(UndoRedoForwarder, Object, QWidget):
    pass


class MainWindow(UndoRedoRoot, Object, QMainWindow):
    pass


class Dialog(UndoRedoRoot, Object, QDialog):
    pass
