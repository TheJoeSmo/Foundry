""" Defines a simple Redux store interface for Python.

This store takes in a default state on initialization rather than generating
one internally.  If it is desired to have one created interally, use a factory
method.

A Generic type state S is used to hold the state data for the module and
actions given to the store are used to transform the state into a new state
through a set of reducers.  The reducers are UI specific and so abstract in
this interface definition.
"""
import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar


class StateNoneError(Exception):
    """Error thrown when Redux default state is None"""


@dataclass
class Action:
    """User action that will be dispatched to the store for processing

    type: str - a unique id that defines what action is happening
    payload: Any - the data payload of the action, can be Any type.
    """

    type: str
    payload: Any


S = TypeVar("S")


class ReduxStore(ABC, Generic[S]):
    """An abstract Redux store for handing system state and user actions.

    Redux is a pattern used for handing system state storage/change based on
    user interaction.  More information can be found here:
    https://redux.js.org/introduction/core-concepts

    The basic principle is that the store hold the system state and accepts
    user actions and creates a new system state based on that action.

    Actions are dispatched to the store and the store will notify all
    subscribers if the state changes.

    In this implementation the state is a generic type 'S' to be defined by
    the developer.
    """

    _subscribers = []

    def __init__(self, state: S):
        """Initialize the store with the default state.

        StateNoneError is raised if a None is provided for the default state
        """
        if not state:
            raise StateNoneError

        self._default_state = state
        self._state = copy.deepcopy(state)

    def get_default_state(self) -> S:
        """Returns the default state."""
        return copy.deepcopy(self._default_state)

    def get_state(self) -> S:
        """Get a copy of the current state."""
        return copy.deepcopy(self._state)

    def dispatch(self, action: Action):
        """Updates the system state based on user action.

        The dispatch() routine takes in a user action and updates the current
        state by sending it to any reducers in the system and then notifies
        any subscribers to the store if the state has changed as a result of
        the action.
        """
        old_state = copy.deepcopy(self._state)
        self._state = self._reduce(copy.deepcopy(self._state), action)

        if self._state != old_state:
            self._notify_subscribers()

    def _notify_subscribers(self):
        """Send a notification to all subscribers."""
        for subscriber in self._subscribers:
            subscriber()

    @abstractmethod
    def _reduce(self, state: S, action: Action) -> S:
        """Creates a new state from the old state and a user action.

        (current state, user action) -> new state

        This method is abstract as must be implemented by the implementing
        class.  The state type is also the Generic type 'S' and must be defined
        by the implementing class.

        This method should not be called directly by the user.  This should
        only be called by the parent class.  If the user wants to update the
        state, it should call store.dispatch(Action()) instead, otherwise the
        actual stored state will not be updated and the associated subscribers
        will not be notified.  DON'T DO IT!
        """

    def subscribe(self, subscriber):
        """Subscribe a function to be called when the state changes."""
        self._subscribers.append(subscriber)
