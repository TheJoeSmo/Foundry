from attr import attrs, field
from attr.validators import instance_of
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QWidget

from foundry.core.graphics_set.util import GRAPHIC_SET_NAMES
from foundry.core.UndoController import UndoController
from foundry.core.validators import range_validator
from foundry.gui.Spinner import Spinner


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class LevelGraphicsState:
    """
    for this level for a level to warp to.

    generator_palette: int
        The generator palette for for this level.
    enemy_palette: int
        The enemy palette for for this level.
    graphics_set: int
        The graphics_set for for this level.
    """

    generator_palette: int = field(validator=[instance_of(int), range_validator(0, 7)])
    enemy_palette: int = field(validator=[instance_of(int), range_validator(0, 3)])
    graphics_set: int = field(validator=[instance_of(int), range_validator(0, 31)])


class LevelGraphicsEditor(QWidget):
    """
    A widget which controls the GUI associated with editing graphics of this level.

    Signals
    -------
    generator_palette_changed: SignalInstance[int]
        A signal which is activated on generator palette change.
    enemy_palette_changed: SignalInstance[int]
        A signal which is activated on enemy palette change.
    graphics_set_changed: SignalInstance[int]
        A signal which is activated on graphics set change.
    state_changed: SignalInstance[LevelGraphicsState]
        A signal which is activated on any state change.

    Attributes
    ----------
    level: LevelGraphicsState
        The model of current graphics.
    undo_controller: UndoController[LevelGraphicsState]
        The undo controller, which is responsible for undoing and redoing any action.
    """

    generator_palette_changed: SignalInstance = Signal(int)  # type: ignore
    enemy_palette_changed: SignalInstance = Signal(int)  # type: ignore
    graphics_set_changed: SignalInstance = Signal(int)  # type: ignore
    state_changed: SignalInstance = Signal(object)  # type: ignore

    undo_controller: UndoController[LevelGraphicsState]

    def __init__(
        self,
        parent: QWidget | None,
        state: LevelGraphicsState,
        undo_controller: UndoController[LevelGraphicsState] | None = None,
    ):
        super().__init__(parent)
        self._state = state
        self.undo_controller = undo_controller or UndoController(self.state)

        # Set up the display
        self._display = LevelGraphicsDisplay(self, self.generator_palette, self.enemy_palette, self.graphics_set)

        # Connect signals accordingly
        self._display.generator_palette_editor.valueChanged.connect(  # type: ignore
            lambda *_: self._generator_palette_update()
        )
        self._display.enemy_palette_editor.valueChanged.connect(lambda *_: self._enemy_palette_update())  # type: ignore
        self._display.graphics_set_editor.currentIndexChanged.connect(  # type: ignore
            lambda *_: self._graphics_set_update()
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.state}, {self.undo_controller})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelGraphicsEditor)
            and self.state == other.state
            and self.undo_controller == other.undo_controller
        )

    @property
    def generator_palette(self) -> int:
        """
        Provides the generator palette of this level.

        Returns
        -------
        int
            The generator palette of for this level.
        """
        return self.state.generator_palette

    @generator_palette.setter
    def generator_palette(self, generator_palette: int):
        if self.generator_palette != generator_palette:
            self.do(LevelGraphicsState(generator_palette, self.enemy_palette, self.graphics_set))

    @property
    def enemy_palette(self) -> int:
        """
        Provides the enemy palette of this level.

        Returns
        -------
        int
            The enemy palette of for this level.
        """
        return self.state.enemy_palette

    @enemy_palette.setter
    def enemy_palette(self, enemy_palette: int):
        if self.enemy_palette != enemy_palette:
            self.do(LevelGraphicsState(self.generator_palette, enemy_palette, self.graphics_set))

    @property
    def graphics_set(self) -> int:
        """
        Provides the graphics set of this level.

        Returns
        -------
        int
            The graphics set of for this level.
        """
        return self.state.graphics_set

    @graphics_set.setter
    def graphics_set(self, graphics_set: int):
        if self.graphics_set != graphics_set:
            self.do(LevelGraphicsState(self.generator_palette, self.enemy_palette, graphics_set))

    @property
    def state(self) -> LevelGraphicsState:
        """
        Provides the current state of the instance.

        Returns
        -------
        LevelGraphicsState
            A tuple of the name, description, generator size, and enemy size for the current instance's level.
        """
        return self._state

    @state.setter
    def state(self, state: LevelGraphicsState):
        if self.state != state:
            self.do(state)

    def do(self, new_state: LevelGraphicsState) -> LevelGraphicsState:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : LevelGraphicsState
            The new state to be stored.

        Returns
        -------
        LevelGraphicsState
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

    def undo(self) -> LevelGraphicsState:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        LevelGraphicsState
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

    def redo(self) -> LevelGraphicsState:
        """
        Redoes the previously undone state.

        Returns
        -------
        LevelGraphicsState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.redo())
        return self.state

    def _update_state(self, state: LevelGraphicsState):
        """
        Handles all updating of the state, sending any signals and updates to the display if needed.

        Parameters
        ----------
        state : LevelGraphicsState
            The new state of the editor.
        """

        generator_palette = state.generator_palette
        enemy_palette = state.enemy_palette
        graphics_set = state.graphics_set

        if (
            self.undo_controller.state.generator_palette != generator_palette
            or self.generator_palette != generator_palette
        ):
            self.generator_palette_changed.emit(generator_palette)
            self._state = LevelGraphicsState(state.generator_palette, self.enemy_palette, self.graphics_set)
            self._display.generator_palette = generator_palette

        if self.undo_controller.state.enemy_palette != enemy_palette or self.enemy_palette != enemy_palette:
            self.enemy_palette_changed.emit(enemy_palette)
            self._state = LevelGraphicsState(self.generator_palette, state.enemy_palette, self.graphics_set)
            self._display.enemy_palette = enemy_palette

        if self.undo_controller.state.graphics_set != graphics_set or self.graphics_set != graphics_set:
            self.graphics_set_changed.emit(graphics_set)
            self._state = LevelGraphicsState(self.generator_palette, self.enemy_palette, state.graphics_set)
            self._display.graphics_set = graphics_set

        self.state_changed.emit(state)

    # Updates from display

    def _generator_palette_update(self):
        self.generator_palette = self._display.generator_palette

    def _enemy_palette_update(self):
        self.enemy_palette = self._display.enemy_palette

    def _graphics_set_update(self):
        self.graphics_set = self._display.graphics_set


class LevelGraphicsDisplay(QFormLayout):
    """
    The active display for the level warp editor.

    Attributes
    ----------
    generator_palette_editor: Spinner
        The editor for this level's generator palette.
    enemy_palette_editor: Spinner
        The editor for this level's enemy palette.
    graphics_set_editor: QComboBox
        The editor for this level's graphics set.
    """

    generator_palette_editor: Spinner
    enemy_palette_editor: Spinner
    graphics_set_editor: QComboBox

    def __init__(self, parent: QWidget | None, generator_palette: int, enemy_palette: int, graphics_set: int):
        super().__init__(parent)

        self.setFormAlignment(Qt.AlignCenter)  # type: ignore

        self.generator_palette_editor = Spinner(None, maximum=7)
        self.enemy_palette_editor = Spinner(None, maximum=3)
        self.graphics_set_editor = QComboBox()
        self.graphics_set_editor.addItems(GRAPHIC_SET_NAMES)

        self.generator_palette = generator_palette
        self.enemy_palette = enemy_palette
        self.graphics_set = graphics_set

        self.addRow("Generator Palette: ", self.generator_palette_editor)
        self.addRow("Enemy Palette: ", self.enemy_palette_editor)
        self.addRow("Graphic Set: ", self.graphics_set_editor)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            + f"{self.parent}, {self.generator_palette}, {self.enemy_palette}, {self.graphics_set})"
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelGraphicsDisplay)
            and self.generator_palette == other.generator_palette
            and self.enemy_palette == other.enemy_palette
            and self.graphics_set == other.graphics_set
        )

    @property
    def generator_palette(self) -> int:
        """
        Provides the generator palette of this level.

        Returns
        -------
        int
            The generator palette of for this level.
        """
        return self.generator_palette_editor.value()

    @generator_palette.setter
    def generator_palette(self, generator_palette: int):
        self.generator_palette_editor.setValue(generator_palette)

    @property
    def enemy_palette(self) -> int:
        """
        Provides the enemy palette of this level.

        Returns
        -------
        int
            The enemy palette of for this level.
        """
        return self.enemy_palette_editor.value()

    @enemy_palette.setter
    def enemy_palette(self, enemy_palette: int):
        self.enemy_palette_editor.setValue(enemy_palette)

    @property
    def graphics_set(self) -> int:
        """
        Provides the graphics_set of this level.

        Returns
        -------
        int
            The graphics_set of for this level.
        """
        return self.graphics_set_editor.currentIndex()

    @graphics_set.setter
    def graphics_set(self, graphics_set: int):
        self.graphics_set_editor.setCurrentIndex(graphics_set)
