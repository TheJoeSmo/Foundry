from attr import attrs, field
from attr.validators import instance_of
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QWidget

from foundry.core.UndoController import UndoController
from foundry.core.validators import range_validator
from foundry.smb3parse.levels.level_header import MARIO_X_POSITIONS, MARIO_Y_POSITIONS

STR_X_POSITIONS = [f"{position >> 4}. Block ({position:0=#4X})".replace("X", "x") for position in MARIO_X_POSITIONS]
STR_Y_POSITIONS = [f"{position}. Block ({position:0=#4X})".replace("X", "x") for position in MARIO_Y_POSITIONS]
ACTIONS = [
    "None",
    "Sliding",
    "Out of pipe ↑",
    "Out of pipe ↓",
    "Out of pipe ←",
    "Out of pipe →",
    "Running and climbing up ship",
    "Ship auto scrolling",
]


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class LevelStartState:
    """
    The representation of the start parameters for the player for a given level.

    x_position: int
        The start position for the player.
    y_position: int
        The start position for the player.
    action: int
        The action the player starts the level doing.
    """

    x_position: int = field(validator=[instance_of(int), range_validator(0, 3)])
    y_position: int = field(validator=[instance_of(int), range_validator(0, 7)])
    action: int = field(validator=[instance_of(int), range_validator(0, 7)])


class LevelStartEditor(QWidget):
    """
    A widget which controls the GUI associated with editing start of this level.

    Signals
    -------
    x_position_changed: SignalInstance[int]
        A signal which is activated on x position change.
    y_position_changed: SignalInstance[int]
        A signal which is activated on y position change.
    action_changed: SignalInstance[int]
        A signal which is activated on action change.
    state_changed: SignalInstance[LevelStartState]
        A signal which is activated on any state change.

    Attributes
    ----------
    level: LevelStartState
        The model of current graphics.
    undo_controller: UndoController[LevelStartState]
        The undo controller, which is responsible for undoing and redoing any action.
    """

    x_position_changed: SignalInstance = Signal(int)  # type: ignore
    y_position_changed: SignalInstance = Signal(int)  # type: ignore
    action_changed: SignalInstance = Signal(int)  # type: ignore
    state_changed: SignalInstance = Signal(object)  # type: ignore

    undo_controller: UndoController[LevelStartState]

    def __init__(
        self,
        parent: QWidget | None,
        state: LevelStartState,
        undo_controller: UndoController[LevelStartState] | None = None,
    ):
        super().__init__(parent)
        self._state = state
        self.undo_controller = undo_controller or UndoController(self.state)

        # Set up the display
        self._display = LevelStartDisplay(self, self.x_position, self.y_position, self.action)

        # Connect signals accordingly
        self._display.x_position_editor.currentIndexChanged.connect(  # type: ignore
            lambda *_: self._x_position_update()
        )
        self._display.y_position_editor.currentIndexChanged.connect(  # type: ignore
            lambda *_: self._y_position_update()
        )
        self._display.action_editor.currentIndexChanged.connect(lambda *_: self._action_update())  # type: ignore

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.state}, {self.undo_controller})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelStartEditor)
            and self.state == other.state
            and self.undo_controller == other.undo_controller
        )

    @property
    def x_position(self) -> int:
        """
        Provides the x position the player starts at.

        Returns
        -------
        int
            The x position for the player starts at.
        """
        return self.state.x_position

    @x_position.setter
    def x_position(self, x_position: int):
        if self.x_position != x_position:
            self.do(LevelStartState(x_position, self.y_position, self.action))

    @property
    def y_position(self) -> int:
        """
        Provides the y position the player starts at.

        Returns
        -------
        int
            The y position the player starts at.
        """
        return self.state.y_position

    @y_position.setter
    def y_position(self, y_position: int):
        if self.y_position != y_position:
            self.do(LevelStartState(self.x_position, y_position, self.action))

    @property
    def action(self) -> int:
        """
        Provides the action the player starts at.

        Returns
        -------
        int
            The action the player starts at.
        """
        return self.state.action

    @action.setter
    def action(self, action: int):
        if self.action != action:
            self.do(LevelStartState(self.x_position, self.y_position, action))

    @property
    def state(self) -> LevelStartState:
        """
        Provides the current state of the instance.

        Returns
        -------
        LevelStartState
            A tuple of the x position, y position, and action for the current instance's level.
        """
        return self._state

    @state.setter
    def state(self, state: LevelStartState):
        if self.state != state:
            self.do(state)

    def do(self, new_state: LevelStartState) -> LevelStartState:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : LevelStartState
            The new state to be stored.

        Returns
        -------
        LevelStartState
            The new state that has been stored.
        """
        self._update_state(new_state)
        return self.undo_controller.do(new_state)

    @property
    def can_undo(self) -> bool:
        """
        Determines if there is any states inside the undo stack.

        Returns
        -------
        bool
            If there is an undo state available.
        """
        return self.undo_controller.can_undo

    def undo(self) -> LevelStartState:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        LevelStartState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.undo())
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
        return self.undo_controller.can_redo

    def redo(self) -> LevelStartState:
        """
        Redoes the previously undone state.

        Returns
        -------
        LevelStartState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.redo())
        return self.state

    def _update_state(self, state: LevelStartState):
        """
        Handles all updating of the state, sending any signals and updates to the display if needed.

        Parameters
        ----------
        state : LevelStartState
            The new state of the editor.
        """

        x_position = state.x_position
        y_position = state.y_position
        action = state.action

        if self.undo_controller.state.x_position != x_position or self.x_position != x_position:
            self.x_position_changed.emit(x_position)
            self._state = LevelStartState(state.x_position, self.y_position, self.action)
            self._display.x_position = x_position

        if self.undo_controller.state.y_position != y_position or self.y_position != y_position:
            self.y_position_changed.emit(y_position)
            self._state = LevelStartState(self.x_position, state.y_position, self.action)
            self._display.y_position = y_position

        if self.undo_controller.state.action != action or self.action != action:
            self.action_changed.emit(action)
            self._state = LevelStartState(self.x_position, self.y_position, state.action)
            self._display.action = action

        self.state_changed.emit(state)

    # Updates from display

    def _x_position_update(self):
        self.x_position = self._display.x_position

    def _y_position_update(self):
        self.y_position = self._display.y_position

    def _action_update(self):
        self.action = self._display.action


class LevelStartDisplay(QFormLayout):
    """
    The active display for the level start editor.

    Attributes
    ----------
    x_position_editor: QComboBox
        The editor for this level's x position.
    y_position_editor: QComboBox
        The editor for this level's y position.
    action_editor: QComboBox
        The editor for this level's starting action.
    """

    x_position_editor: QComboBox
    y_position_editor: QComboBox
    action_editor: QComboBox

    def __init__(self, parent: QWidget | None, x_position: int, y_position: int, action: int):
        super().__init__(parent)

        self.setFormAlignment(Qt.AlignCenter)  # type: ignore

        self.x_position_editor = QComboBox()
        self.x_position_editor.addItems(STR_X_POSITIONS)

        self.y_position_editor = QComboBox()
        self.y_position_editor.addItems(STR_Y_POSITIONS)

        self.action_editor = QComboBox()
        self.action_editor.addItems(ACTIONS)

        self.x_position = x_position
        self.y_position = y_position
        self.action = action

        self.addRow("Starting X: ", self.x_position_editor)
        self.addRow("Starting Y: ", self.y_position_editor)
        self.addRow("Action: ", self.action_editor)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(" + f"{self.parent}, {self.x_position}, {self.y_position}, {self.action})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelStartDisplay)
            and self.x_position == other.x_position
            and self.y_position == other.y_position
            and self.action == other.action
        )

    @property
    def x_position(self) -> int:
        """
        Provides the x position of this level.

        Returns
        -------
        int
            The x position of for this level.
        """
        return self.x_position_editor.currentIndex()

    @x_position.setter
    def x_position(self, x_position: int):
        self.x_position_editor.setCurrentIndex(x_position)

    @property
    def y_position(self) -> int:
        """
        Provides the y position of this level.

        Returns
        -------
        int
            The y position of for this level.
        """
        return self.y_position_editor.currentIndex()

    @y_position.setter
    def y_position(self, y_position: int):
        self.y_position_editor.setCurrentIndex(y_position)

    @property
    def action(self) -> int:
        """
        Provides the action of this level.

        Returns
        -------
        int
            The action of for this level.
        """
        return self.action_editor.currentIndex()

    @action.setter
    def action(self, action: int):
        self.action_editor.setCurrentIndex(action)
