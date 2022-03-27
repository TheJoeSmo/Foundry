from typing import TypeVar, Generic
import copy
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Action:
    """ User action that will be dispatched to the store for processing
    
    type: str - a unique id that defines what action is happening
    payload: any - the data payload of the action, can be any type.
    """
    type: str
    payload: any

S = TypeVar('S')

class ReduxStore(ABC, Generic[S]):
    """ An abstract Redux store for handing system state and user actions.

    Redux is a pattern used for handing system state storage/change based on
    user interation.  More information can be found here:
    https://redux.js.org/introduction/core-concepts

    The basic principle is that the store hold the system state and accepts
    user actions and creates a new system state based on that action.

    Actions are dispatched to the store and the store will notify all
    subscribers if the state changes.

    In this implementation the state is a generic type 'S' to be defined by
    the developer.
    """
    _defaultState: S = None
    _state: S = None
    _subscribers = []

    def __init__(self, state: S):
        """ Initialize the store with the default state. """
        self._defaultState = state
        self._state = copy.deepcopy(state)

    def get_default(self) -> S:
        """ Returns the default state. """
        return copy.deepcopy(self._defaultState)

    def get_state(self) -> S:
        """ Get a copy of the current state. """
        return copy.deepcopy(self._state)

    def dispatch(self, action: Action):
        """ Updates the system state based on user action.
        
        The dispatch() routine takes in a user action and updates the current 
        state by sending it to any reducers in the system and then notifies 
        any subscribers to the store if the state has changed as a result of
        the action. 
        """
        oldState = copy.deepcopy(self._state)
        self._state = self.reduce(copy.deepcopy(self._state), action)

        if self._state != oldState:
            self._notify_subscribers()

    def _notify_subscribers(self):
        """ Send a notification to all subscribers. """
        for subscriber in self._subscribers:
            subscriber()

    @abstractmethod
    def reduce(self, state:S, action: Action) -> S:
        """ Creates a new state from the old state and a user action. 
        
        (current state, user action) -> new state

        This method is abstract as must be implemented by the implementing 
        class.  The state type is also the Generic type 'S' and must be defined
        by the implementing class.
        """
        pass

    def subscribe(self, subscriber):
        """ Subscribe a function to be called when the state changes. """
        self._subscribers.append(subscriber)
