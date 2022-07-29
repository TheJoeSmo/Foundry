from attr import evolve
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QWidget

from foundry.core.UndoController import UndoController
from foundry.game.level.util import Level as LevelData

LevelDataState = tuple[str, str, int, int]


class LevelInformationEditor(QWidget):
    """
    A widget which controls the GUI associated with editing information for a given level.

    Signals
    -------
    name_changed: SignalInstance[str]
        A signal which is activated on name change.
    description_changed: SignalInstance[str]
        A signal which is activated on description change.
    generator_space_changed: SignalInstance[int]
        A signal which is activated on generation space change.
    enemy_space_changed: SignalInstance[int]
        A signal which is activated on enemy space change.
    state_changed: SignalInstance[LevelDataState]
        A signal which is activated on any state change.

    Attributes
    ----------
    level: LevelData
        The model of current level information.
    undo_controller: UndoController[LevelDataState]
        The undo controller, which is responsible for undoing and redoing any action.
    """

    name_changed: SignalInstance = Signal(str)  # type: ignore
    description_changed: SignalInstance = Signal(str)  # type: ignore
    generator_space_changed: SignalInstance = Signal(int)  # type: ignore
    enemy_space_changed: SignalInstance = Signal(int)  # type: ignore
    state_changed: SignalInstance = Signal(object)  # type: ignore

    level: LevelData
    undo_controller: UndoController[LevelDataState]

    def __init__(
        self,
        parent: QWidget | None,
        level: LevelData,
        undo_controller: UndoController[LevelDataState] | None = None,
    ):
        super().__init__(parent)
        self.level = level
        self.undo_controller = undo_controller or UndoController(self.state)

        # Set up the display
        self._display = LevelInformationEditorDisplay(
            self, self.name, self.description, self.generator_space, self.enemy_space
        )

        # Connect signals accordingly
        self._display.name_editor.textChanged.connect(lambda *_: self._name_update())  # type: ignore
        self._display.description_editor.textChanged.connect(lambda *_: self._description_update())  # type: ignore
        self._display.generator_space_editor.valueChanged.connect(  # type: ignore
            lambda *_: self._generator_space_update()
        )
        self._display.enemy_space_editor.valueChanged.connect(lambda *_: self._enemy_space_update())  # type: ignore

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.level}, {self.undo_controller})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelInformationEditor)
            and self.level == other.level
            and self.undo_controller == other.undo_controller
        )

    @property
    def name(self) -> str:
        """
        Provides the name of the level.

        Returns
        -------
        str
            The name of the level.
        """
        return self.level.display_information.name or ""

    @name.setter
    def name(self, name: str):
        if self.name != name:
            self.level = evolve(self.level, display_information=evolve(self.level.display_information, name=name))
            self.do(self.state)

    @property
    def description(self) -> str:
        """
        Provides the description of the level.

        Returns
        -------
        str
            The description of the level.
        """
        return self.level.display_information.description or ""

    @description.setter
    def description(self, description: str):
        if self.description != description:
            self.level = evolve(
                self.level, display_information=evolve(self.level.display_information, description=description)
            )
            self.do(self.state)

    @property
    def generator_space(self) -> int:
        """
        Provides the space for generators inside of the level.

        Returns
        -------
        int
            The space for generators inside of the level.
        """
        return self.level.generator_size

    @generator_space.setter
    def generator_space(self, generator_space: int):
        if self.generator_space != generator_space:
            self.level = evolve(self.level, generator_size=generator_space)
            self.do(self.state)

    @property
    def enemy_space(self) -> int:
        """
        Provides the space for enemies inside of the level.

        Returns
        -------
        int
            The space for enemies inside of the level.
        """
        return self.level.enemy_size

    @enemy_space.setter
    def enemy_space(self, enemy_space: int):
        if self.level.enemy_size != enemy_space:
            self.level = evolve(self.level, enemy_size=enemy_space)
            self.do(self.state)

    @property
    def state(self) -> LevelDataState:
        """
        Provides the current state of the instance.

        Returns
        -------
        LevelDataState
            A tuple of the name, description, generator size, and enemy size for the current instance's level.
        """
        return (self.name, self.description, self.generator_space, self.enemy_space)

    @state.setter
    def state(self, state: LevelDataState | LevelData):
        # Convert it to a level data state
        if isinstance(state, LevelData):
            state = (
                state.display_information.name or "",
                state.display_information.description or "",
                state.generator_size,
                state.enemy_size,
            )
        if self.state != state:
            self._update_state(state)
            self.do(state)

    def do(self, new_state: LevelDataState) -> LevelDataState:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : LevelDataState
            The new state to be stored.

        Returns
        -------
        LevelDataState
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

    def undo(self) -> LevelDataState:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        LevelDataState
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

    def redo(self) -> LevelDataState:
        """
        Redoes the previously undone state.

        Returns
        -------
        LevelDataState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.redo())
        return self.state

    def _update_state(self, state: LevelDataState):
        """
        Handles all updating of the state, sending any signals and updates to the display if needed.

        Parameters
        ----------
        state : LevelDataState
            The new state of the editor.
        """

        name, desc, gen_space, enemy_space = state

        if self.undo_controller.state[0] != name or self.name != name:
            self.name_changed.emit(name)
            self.level = evolve(self.level, display_information=evolve(self.level.display_information, name=name))
            self._display.name = name

        if self.undo_controller.state[1] != desc or self.description != desc:
            self.description_changed.emit(desc)
            self.level = evolve(
                self.level, display_information=evolve(self.level.display_information, description=desc)
            )
            self._display.description = desc

        if self.undo_controller.state[2] != gen_space or self.generator_space != gen_space:
            self.generator_space_changed.emit(gen_space)
            self.level = evolve(self.level, generator_size=gen_space)
            self._display.generator_space = gen_space

        if self.undo_controller.state[3] != enemy_space or self.enemy_space != enemy_space:
            self.enemy_space_changed.emit(enemy_space)
            self.level = evolve(self.level, enemy_size=enemy_space)
            self._display.enemy_space = enemy_space

        self.state_changed.emit(state)

    # Updates from display

    def _name_update(self):
        self.name = self._display.name

    def _description_update(self):
        self.description = self._display.description

    def _generator_space_update(self):
        self.generator_space = self._display.generator_space

    def _enemy_space_update(self):
        self.enemy_space = self._display.enemy_space


class LevelInformationEditorDisplay(QFormLayout):
    """
    The active display for the level information editor.

    Attributes
    ----------
    name_editor: QLineEdit
        The editor for the level's name.
    description_editor: QLineEdit
        The editor for the level's description.
    generator_space_editor: QSpinBox
        The editor for the amount of space provided to the level's generators.
    enemy_space_editor: QSpinBox
        The editor for the amount of space provided to the level's enemies.
    """

    name_editor: QLineEdit
    description_editor: QLineEdit
    generator_space_editor: QSpinBox
    enemy_space_editor: QSpinBox

    def __init__(self, parent: QWidget | None, name: str, description: str, generator_space: int, enemy_space: int):
        super().__init__(parent)

        self.setFormAlignment(Qt.AlignCenter)  # type: ignore

        self.name_editor = QLineEdit(name)

        self.description_editor = QLineEdit(description)

        self.generator_space_editor = QSpinBox()
        self.generator_space_editor.setMinimum(0)
        self.generator_space_editor.setMaximum(0x2000)
        self.generator_space_editor.setValue(generator_space)

        self.enemy_space_editor = QSpinBox()
        self.enemy_space_editor.setMinimum(0)
        self.enemy_space_editor.setMaximum(0x2000)
        self.enemy_space_editor.setValue(enemy_space)

        self.addRow("Name: ", self.name_editor)
        self.addRow("Description: ", self.description_editor)
        self.addRow("Generator Space: ", self.generator_space_editor)
        self.addRow("Enemy Space: ", self.enemy_space_editor)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.parent}, {self.name}. {self.description},"
            + f" {self.generator_space}, {self.enemy_space})"
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelInformationEditorDisplay)
            and self.name == other.name
            and self.description == other.description
            and self.generator_space == other.generator_space
            and self.enemy_space == other.enemy_space
        )

    @property
    def name(self) -> str:
        """
        Provides the name of the level.

        Returns
        -------
        str
            The name of the level.
        """
        return self.name_editor.text()

    @name.setter
    def name(self, name: str):
        self.name_editor.setText(name)

    @property
    def description(self) -> str:
        """
        Provides the description of the level.

        Returns
        -------
        str
            The description of the level.
        """
        return self.description_editor.text()

    @description.setter
    def description(self, description: str):
        self.description_editor.setText(description)

    @property
    def generator_space(self) -> int:
        """
        Provides the space for generators inside of the level.

        Returns
        -------
        int
            The space for generators inside of the level.
        """
        return self.generator_space_editor.value()

    @generator_space.setter
    def generator_space(self, generator_space: int):
        self.generator_space_editor.setValue(generator_space)

    @property
    def enemy_space(self) -> int:
        """
        Provides the space for enemies inside of the level.

        Returns
        -------
        int
            The space for enemies inside of the level.
        """
        return self.enemy_space_editor.value()

    @enemy_space.setter
    def enemy_space(self, enemy_space: int):
        self.enemy_space_editor.setValue(enemy_space)
