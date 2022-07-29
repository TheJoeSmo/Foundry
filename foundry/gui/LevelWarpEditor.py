from attr import attrs, field
from attr.validators import instance_of
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from foundry.core.UndoController import UndoController
from foundry.core.validators import range_validator
from foundry.gui.LevelSelector import OBJECT_SET_ITEMS, LevelSelector
from foundry.gui.settings import FileSettings
from foundry.gui.Spinner import Spinner

SPINNER_MAX_VALUE = 0x0F_FF_FF


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class LevelWarpState:
    """
    The next level for a level to warp to.

    generator_pointer: int
        The generator pointer for the next level.
    enemy_pointer: int
        The enemy pointer for the next level.
    tileset: int
        The tileset for the next level.
    """

    generator_pointer: int = field(validator=[instance_of(int), range_validator(0, 0xFFFFFF)])
    enemy_pointer: int = field(validator=[instance_of(int), range_validator(0, 0xFFFFFF)])
    tileset: int = field(validator=[instance_of(int), range_validator(0, 15)])


class LevelWarpEditor(QWidget):
    """
    A widget which controls the GUI associated with editing warp destination for a given level.

    Signals
    -------
    generator_pointer_changed: SignalInstance[int]
        A signal which is activated on generator pointer change.
    enemy_pointer_changed: SignalInstance[int]
        A signal which is activated on enemy pointer change.
    tileset_changed: SignalInstance[int]
        A signal which is activated on tileset change.
    state_changed: SignalInstance[LevelWarpState]
        A signal which is activated on any state change.

    Attributes
    ----------
    level: LevelWarpState
        The model of current warp destination.
    undo_controller: UndoController[LevelWarpState]
        The undo controller, which is responsible for undoing and redoing any action.
    file_settings: FileSettings
        The settings for determining levels to automatically select the warp state from.
    """

    generator_pointer_changed: SignalInstance = Signal(int)  # type: ignore
    enemy_pointer_changed: SignalInstance = Signal(int)  # type: ignore
    tileset_changed: SignalInstance = Signal(int)  # type: ignore
    state_changed: SignalInstance = Signal(object)  # type: ignore

    undo_controller: UndoController[LevelWarpState]

    def __init__(
        self,
        parent: QWidget | None,
        state: LevelWarpState,
        undo_controller: UndoController[LevelWarpState] | None = None,
        file_settings: FileSettings | None = None,
    ):
        super().__init__(parent)
        self._state = state
        self.undo_controller = undo_controller or UndoController(self.state)
        self.file_settings = file_settings or FileSettings(levels=[])

        # Set up the display
        self._display = LevelWarpDisplay(self, self.generator_pointer, self.enemy_pointer, self.tileset)

        # Connect signals accordingly
        self._display.generator_pointer_editor.valueChanged.connect(  # type: ignore
            lambda *_: self._generator_pointer_update()
        )
        self._display.enemy_pointer_editor.valueChanged.connect(lambda *_: self._enemy_pointer_update())  # type: ignore
        self._display.tileset_editor.currentIndexChanged.connect(lambda *_: self._tileset_update())  # type: ignore
        self._display.select_from_level_button.pressed.connect(  # type: ignore
            lambda *_: self._set_warp_state_from_level()
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.state}, {self.undo_controller})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelWarpEditor)
            and self.state == other.state
            and self.undo_controller == other.undo_controller
        )

    @property
    def generator_pointer(self) -> int:
        """
        Provides the generator pointer of the level that it will be warped to.

        Returns
        -------
        int
            The generator pointer of the next level.
        """
        return self.state.generator_pointer

    @generator_pointer.setter
    def generator_pointer(self, generator_pointer: int):
        if self.generator_pointer != generator_pointer:
            self.do(LevelWarpState(generator_pointer, self.enemy_pointer, self.tileset))

    @property
    def enemy_pointer(self) -> int:
        """
        Provides the enemy pointer of the level that it will be warped to.

        Returns
        -------
        int
            The enemy pointer of the next level.
        """
        return self.state.enemy_pointer

    @enemy_pointer.setter
    def enemy_pointer(self, enemy_pointer: int):
        if self.enemy_pointer != enemy_pointer:
            self.do(LevelWarpState(self.generator_pointer, enemy_pointer, self.tileset))

    @property
    def tileset(self) -> int:
        """
        Provides the tileset of the level that it will be warped to.

        Returns
        -------
        int
            The tileset of the next level.
        """
        return self.state.tileset

    @tileset.setter
    def tileset(self, tileset: int):
        if self.tileset != tileset:
            self.do(LevelWarpState(self.generator_pointer, self.enemy_pointer, tileset))

    @property
    def state(self) -> LevelWarpState:
        """
        Provides the current state of the instance.

        Returns
        -------
        LevelWarpState
            A tuple of the name, description, generator size, and enemy size for the current instance's level.
        """
        return self._state

    @state.setter
    def state(self, state: LevelWarpState):
        if self.state != state:
            self.do(state)

    def do(self, new_state: LevelWarpState) -> LevelWarpState:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : LevelWarpState
            The new state to be stored.

        Returns
        -------
        LevelWarpState
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

    def undo(self) -> LevelWarpState:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        LevelWarpState
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

    def redo(self) -> LevelWarpState:
        """
        Redoes the previously undone state.

        Returns
        -------
        LevelWarpState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.redo())
        return self.state

    def _update_state(self, state: LevelWarpState):
        """
        Handles all updating of the state, sending any signals and updates to the display if needed.

        Parameters
        ----------
        state : LevelWarpState
            The new state of the editor.
        """

        generator_pointer = state.generator_pointer
        enemy_pointer = state.enemy_pointer
        tileset = state.tileset

        if (
            self.undo_controller.state.generator_pointer != generator_pointer
            or self.generator_pointer != generator_pointer
        ):
            self.generator_pointer_changed.emit(generator_pointer)
            self._state = LevelWarpState(state.generator_pointer, self.enemy_pointer, self.tileset)
            self._display.generator_pointer = generator_pointer

        if self.undo_controller.state.enemy_pointer != enemy_pointer or self.enemy_pointer != enemy_pointer:
            self.enemy_pointer_changed.emit(enemy_pointer)
            self._state = LevelWarpState(self.generator_pointer, state.enemy_pointer, self.tileset)
            self._display.enemy_pointer = enemy_pointer

        if self.undo_controller.state.tileset != tileset or self.tileset != tileset:
            self.tileset_changed.emit(tileset)
            self._state = LevelWarpState(self.generator_pointer, self.enemy_pointer, state.tileset)
            self._display.tileset = tileset

        self.state_changed.emit(state)

    # Updates from display

    def _generator_pointer_update(self):
        self.generator_pointer = self._display.generator_pointer

    def _enemy_pointer_update(self):
        self.enemy_pointer = self._display.enemy_pointer

    def _tileset_update(self):
        self.tileset = self._display.tileset

    def _set_warp_state_from_level(self):
        level_selector = LevelSelector(self, self.file_settings)
        level_was_selected = level_selector.exec_() == QDialog.Accepted

        if level_was_selected:
            self.state = LevelWarpState(
                level_selector.object_data_offset, level_selector.enemy_data_offset, level_selector.object_set
            )


class LevelWarpDisplay(QFormLayout):
    """
    The active display for the level warp editor.

    Attributes
    ----------
    generator_pointer_editor: Spinner
        The editor for the next area's generator pointer.
    enemy_pointer_editor: Spinner
        The editor for the next area's enemy pointer.
    tileset_editor: QComboBox
        The editor for the next area's tileset.
    """

    generator_pointer_editor: Spinner
    enemy_pointer_editor: Spinner
    tileset_editor: QComboBox

    def __init__(self, parent: QWidget | None, generator_pointer: int, enemy_pointer: int, tileset: int):
        super().__init__(parent)

        self.setFormAlignment(Qt.AlignCenter)  # type: ignore

        self.generator_pointer_editor = Spinner(None, maximum=SPINNER_MAX_VALUE)
        self.enemy_pointer_editor = Spinner(None, maximum=SPINNER_MAX_VALUE)
        self.tileset_editor = QComboBox()
        self.tileset_editor.addItems(OBJECT_SET_ITEMS)
        self.select_from_level_button = QPushButton("Set from Level")

        self.generator_pointer = generator_pointer
        self.enemy_pointer = enemy_pointer
        self.tileset = tileset

        self.addRow("Generator Address: ", self.generator_pointer_editor)
        self.addRow("Enemy Address: ", self.enemy_pointer_editor)
        self.addRow("Tileset: ", self.tileset_editor)
        self.addRow(QLabel(""))
        self.addRow(self.select_from_level_button)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.parent}, {self.generator_pointer}, {self.enemy_pointer}, {self.tileset})"
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelWarpDisplay)
            and self.generator_pointer == other.generator_pointer
            and self.enemy_pointer == other.enemy_pointer
            and self.tileset == other.tileset
        )

    @property
    def generator_pointer(self) -> int:
        """
        Provides the generator pointer of the level that it will be warped to.

        Returns
        -------
        int
            The generator pointer of the next level.
        """
        return self.generator_pointer_editor.value()

    @generator_pointer.setter
    def generator_pointer(self, generator_pointer: int):
        self.generator_pointer_editor.setValue(generator_pointer)

    @property
    def enemy_pointer(self) -> int:
        """
        Provides the enemy pointer of the level that it will be warped to.

        Returns
        -------
        int
            The enemy pointer of the next level.
        """
        return self.enemy_pointer_editor.value()

    @enemy_pointer.setter
    def enemy_pointer(self, enemy_pointer: int):
        self.enemy_pointer_editor.setValue(enemy_pointer)

    @property
    def tileset(self) -> int:
        """
        Provides the tileset of the level that it will be warped to.

        Returns
        -------
        int
            The tileset of the next level.
        """
        return self.tileset_editor.currentIndex()

    @tileset.setter
    def tileset(self, tileset: int):
        self.tileset_editor.setCurrentIndex(tileset)
