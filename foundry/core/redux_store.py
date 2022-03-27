from typing import TypeVar, Generic
import copy
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Action:
    type: str
    payload: any

S = TypeVar('S')

class ReduxStore(ABC, Generic[S]):
    defaultState: S = None
    state: S = None
    subscribers = []

    def __init__(self, state: S):
        self.defaultState = state
        self.state = copy.deepcopy(state)

    def get_default(self) -> S:
        return copy.deepcopy(self.defaultState)

    def get_state(self) -> S:
        return self.state

    def dispatch(self, action: Action):
        oldState = copy.deepcopy(self.state)
        self.state = self.reduce(copy.deepcopy(self.state), action)

        if self.state != oldState:
            self._notify_subscribers()

    def _notify_subscribers(self):
        for subscriber in self.subscribers:
            subscriber()

    @abstractmethod
    def reduce(self, state:S, action: Action) -> S:
        pass

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)
