from collections import deque
from typing import Generic, Optional, Protocol, TypeVar

T = TypeVar("T")


class UndoControllerProtocol(Protocol, Generic[T]):
    @property
    def state(self) -> T:
        ...

    def do(self, new_state: T) -> T:
        ...

    @property
    def can_undo(self) -> bool:
        ...

    def undo(self) -> T:
        ...

    @property
    def can_redo(self) -> bool:
        ...

    def redo(self) -> T:
        ...


class UndoController(Generic[T]):
    """
    A controller for handling both undo and redo

    Parameters
    ----------
    Generic : T
        The state being stored by the UndoController.
    """

    def __init__(self, initial_state: T, undo_stack: Optional[deque[T]] = None, redo_stack: Optional[deque[T]] = None):
        self._state: T = initial_state
        self.undo_stack: deque[T] = undo_stack if undo_stack is not None else deque()
        self.redo_stack: deque[T] = redo_stack if redo_stack is not None else deque()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.state}, {self.undo_stack}, {self.redo_stack})"

    @property
    def state(self) -> T:
        return self._state

    def do(self, new_state: T) -> T:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : T
            The new state to be stored.

        Returns
        -------
        T
            The new state that has been stored.
        """
        self.undo_stack.append(self.state)
        self.redo_stack = deque()
        self._state = new_state
        return self.state

    @property
    def can_undo(self) -> bool:
        """
        Determines if there is any states inside the undo stack.

        Returns
        -------
        bool
            If there is an undo state available.
        """
        return bool(len(self.undo_stack))

    def undo(self) -> T:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        T
            The new state that has been stored.
        """
        self.redo_stack.append(self.state)
        self._state = self.undo_stack.pop()
        return self.state

    @property
    def can_redo(self) -> bool:
        """
        Determines if there is any states inside the redo stack.

        Returns
        -------
        bool
            If there is an redo state available.
        """
        return bool(len(self.redo_stack))

    def redo(self) -> T:
        """
        Redoes the previously undone state.

        Returns
        -------
        T
            The new state that has been stored.
        """
        self.undo_stack.append(self.state)
        self._state = self.redo_stack.pop()
        return self.state
