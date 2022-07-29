from attr import attrs, evolve, field
from attr.validators import instance_of
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QWidget

from foundry.core.UndoController import UndoController
from foundry.core.validators import range_validator

LEVEL_LENGTHS = [0x10 * (i + 1) for i in range(2**4)]
STR_LEVEL_LENGTHS = [f"{length - 1:0=#4X} / {length} Blocks".replace("X", "x") for length in LEVEL_LENGTHS]


MUSIC_ITEMS = [
    "Plain level",
    "Underground",
    "Water level",
    "Fortress",
    "Boss",
    "Ship",
    "Battle",
    "P-Switch/Mushroom house (1)",
    "Hilly level",
    "Castle room",
    "Clouds/Sky",
    "P-Switch/Mushroom house (2)",
    "No music",
    "P-Switch/Mushroom house (1)",
    "No music",
    "World 7 map",
]

TIMES = ["300", "400", "200", "Unlimited"]

SCROLL_DIRECTIONS = [
    "Locked, unless climbing/flying",
    "Free vertical scrolling",
    "Locked 'by start coordinates'?",
    "Shouldn't appear in game, do not use.",
]


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class LevelDataState:
    """
    The representation of the start parameters for the player for a given level.

    level_length: int
        The length of the level.
    music: int
        The music selected for the level.
    time: int
        The time provided to the player to complete the level.
    scroll: int
        The rules applied to the scroll for the level.
    horizontal: bool
        If the level is horizontal.
    pipe_ends_level: bool
        If entering a pipe ends the level.
    """

    level_length: int = field(validator=[instance_of(int), range_validator(0, 15)])
    music: int = field(validator=[instance_of(int), range_validator(0, 63)])
    time: int = field(validator=[instance_of(int), range_validator(0, 3)])
    scroll: int = field(validator=[instance_of(int), range_validator(0, 3)])
    horizontal: bool
    pipe_ends_level: bool


class LevelDataEditor(QWidget):
    """
    A widget which controls the GUI associated with editing this level's data.

    Signals
    -------
    level_length_changed: SignalInstance[int]
        A signal which is activated on level length change.
    music_changed: SignalInstance[int]
        A signal which is activated on music change.
    time_changed: SignalInstance[int]
        A signal which is activated on time change.
    scroll_changed: SignalInstance[int]
        A signal which is activated on scroll type change.
    horizontal_changed: SignalInstance[bool]
        A signal which is activated on level horizontality change.
    pipe_ends_level_changed: SignalInstance[bool]
        A signal which is activated on if pipe ends level change.
    state_changed: SignalInstance[LevelDataState]
        A signal which is activated on any state change.

    Attributes
    ----------
    undo_controller: UndoController[LevelDataState]
        The undo controller, which is responsible for undoing and redoing any action.
    """

    level_length_changed: SignalInstance = Signal(int)  # type: ignore
    music_changed: SignalInstance = Signal(int)  # type: ignore
    time_changed: SignalInstance = Signal(int)  # type: ignore
    scroll_changed: SignalInstance = Signal(int)  # type: ignore
    horizontal_changed: SignalInstance = Signal(bool)  # type: ignore
    pipe_ends_level_changed: SignalInstance = Signal(bool)  # type: ignore
    state_changed: SignalInstance = Signal(object)  # type: ignore

    undo_controller: UndoController[LevelDataState]

    def __init__(
        self,
        parent: QWidget | None,
        state: LevelDataState,
        undo_controller: UndoController[LevelDataState] | None = None,
    ):
        super().__init__(parent)
        self._state = state
        self.undo_controller = undo_controller or UndoController(self.state)

        # Set up the display
        self._display = LevelDataDisplay(
            self, self.level_length, self.music, self.time, self.scroll, self.horizontal, self.pipe_ends_level
        )

        # Connect signals accordingly
        self._display.level_length_editor.currentIndexChanged.connect(  # type: ignore
            lambda *_: self._level_length_update()
        )
        self._display.music_editor.currentIndexChanged.connect(lambda *_: self._music_update())  # type: ignore
        self._display.time_editor.currentIndexChanged.connect(lambda *_: self._time_update())  # type: ignore
        self._display.scroll_editor.currentIndexChanged.connect(lambda *_: self._scroll_update())  # type: ignore
        self._display.horizontal_editor.stateChanged.connect(lambda *_: self._horizontal_update())  # type: ignore
        self._display.pipe_ends_level_editor.stateChanged.connect(  # type: ignore
            lambda *_: self._pipe_ends_level_update()
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.state}, {self.undo_controller})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelDataEditor)
            and self.state == other.state
            and self.undo_controller == other.undo_controller
        )

    @property
    def level_length(self) -> int:
        """
        Provides the length of the level.

        Returns
        -------
        int
            The length of the level.
        """
        return self.state.level_length

    @level_length.setter
    def level_length(self, level_length: int):
        if self.level_length != level_length:
            self.do(evolve(self.state, level_length=level_length))

    @property
    def music(self) -> int:
        """
        Provides the music of the level.

        Returns
        -------
        int
            The music of the level.
        """
        return self.state.music

    @music.setter
    def music(self, music: int):
        if self.music != music:
            self.do(evolve(self.state, music=music))

    @property
    def time(self) -> int:
        """
        Provides the time of the level.

        Returns
        -------
        int
            The time of the level.
        """
        return self.state.time

    @time.setter
    def time(self, time: int):
        if self.time != time:
            self.do(evolve(self.state, time=time))

    @property
    def scroll(self) -> int:
        """
        Provides the scroll of the level.

        Returns
        -------
        int
            The scroll of the level.
        """
        return self.state.scroll

    @scroll.setter
    def scroll(self, scroll: int):
        if self.scroll != scroll:
            self.do(evolve(self.state, scroll=scroll))

    @property
    def horizontal(self) -> bool:
        """
        Provides if the level is horizontal.

        Returns
        -------
        bool
            If the level is horizontal.
        """
        return self.state.horizontal

    @horizontal.setter
    def horizontal(self, horizontal: bool):
        if self.horizontal != horizontal:
            self.do(evolve(self.state, horizontal=horizontal))

    @property
    def pipe_ends_level(self) -> bool:
        """
        Provides if entering a pipe will end the level.

        Returns
        -------
        bool
            If the entering pipes end the level.
        """
        return self.state.pipe_ends_level

    @pipe_ends_level.setter
    def pipe_ends_level(self, pipe_ends_level: bool):
        if self.pipe_ends_level != pipe_ends_level:
            self.do(evolve(self.state, pipe_ends_level=pipe_ends_level))

    @property
    def state(self) -> LevelDataState:
        """
        Provides the current state of the instance.

        Returns
        -------
        LevelDataState
            A tuple of the level length, music, time, scroll, and other data associated with the current
            instance's level.
        """
        return self._state

    @state.setter
    def state(self, state: LevelDataState):
        if self.state != state:
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

        if self.undo_controller.state.level_length != state.level_length or self.level_length != state.level_length:
            self.level_length_changed.emit(state.level_length)
            self._state = evolve(self.state, level_length=state.level_length)
            self._display.level_length = state.level_length

        if self.undo_controller.state.music != state.music or self.music != state.music:
            self.music_changed.emit(state.music)
            self._state = evolve(self.state, music=state.music)
            self._display.music = state.music

        if self.undo_controller.state.time != state.time or self.time != state.time:
            self.time_changed.emit(state.time)
            self._state = evolve(self.state, time=state.time)
            self._display.time = state.time

        if self.undo_controller.state.scroll != state.scroll or self.scroll != state.scroll:
            self.scroll_changed.emit(state.scroll)
            self._state = evolve(self.state, scroll=state.scroll)
            self._display.scroll = state.scroll

        if self.undo_controller.state.horizontal != state.horizontal or self.horizontal != state.horizontal:
            self.horizontal_changed.emit(state.horizontal)
            self._state = evolve(self.state, horizontal=state.horizontal)
            self._display.horizontal = state.horizontal

        if (
            self.undo_controller.state.pipe_ends_level != state.pipe_ends_level
            or self.pipe_ends_level != state.pipe_ends_level
        ):
            self.pipe_ends_level_changed.emit(state.pipe_ends_level)
            self._state = evolve(self.state, pipe_ends_level=state.pipe_ends_level)
            self._display.pipe_ends_level = state.pipe_ends_level

        self.state_changed.emit(state)

    # Updates from display

    def _level_length_update(self):
        self.level_length = self._display.level_length

    def _music_update(self):
        self.music = self._display.music

    def _time_update(self):
        self.time = self._display.time

    def _scroll_update(self):
        self.scroll = self._display.scroll

    def _horizontal_update(self):
        self.horizontal = self._display.horizontal

    def _pipe_ends_level_update(self):
        self.pipe_ends_level = self._display.pipe_ends_level


class LevelDataDisplay(QFormLayout):
    """
    The active display for the level data editor.

    Attributes
    ----------
    level_length_editor: QComboBox
        The editor for this level's length.
    music_editor: QComboBox
        The editor for this level's music.
    time_editor: QComboBox
        The editor for this level's time.
    scroll_editor: QComboBox
        The editor for this level's scroll.
    horizontal_editor: QCheckBox
        The editor to determine if this level is horizontal or vertical.
    pipe_ends_level_editor: QCheckBox
        The editor to determine if entering a pipe will end the level.
    """

    level_length_editor: QComboBox
    music_editor: QComboBox
    time_editor: QComboBox
    scroll_editor: QComboBox
    horizontal_editor: QCheckBox
    pipe_ends_level_editor: QCheckBox

    def __init__(
        self,
        parent: QWidget | None,
        level_length: int,
        music: int,
        time: int,
        scroll: int,
        horizontal: bool,
        pipe_ends_level: bool,
    ):
        super().__init__(parent)

        self.setFormAlignment(Qt.AlignCenter)  # type: ignore

        self.level_length_editor = QComboBox()
        self.level_length_editor.addItems(STR_LEVEL_LENGTHS[:-1] if horizontal else STR_LEVEL_LENGTHS)

        self.music_editor = QComboBox()
        self.music_editor.addItems(MUSIC_ITEMS)

        self.time_editor = QComboBox()
        self.time_editor.addItems(TIMES)

        self.scroll_editor = QComboBox()
        self.scroll_editor.addItems(SCROLL_DIRECTIONS)

        self.horizontal_editor = QCheckBox("Level is Horizontal")
        self.pipe_ends_level_editor = QCheckBox("Pipe ends Level")

        check_box_layout = QHBoxLayout()
        check_box_layout.setContentsMargins(0, 0, 0, 0)
        check_box_layout.addWidget(self.horizontal_editor)
        check_box_layout.addWidget(self.pipe_ends_level_editor)

        check_box_widget = QWidget()
        check_box_widget.setLayout(check_box_layout)

        self.level_length = level_length
        self.music = music
        self.time = time
        self.scroll = scroll
        self.horizontal = horizontal
        self.pipe_ends_level = pipe_ends_level

        self.addRow("Level Length: ", self.level_length_editor)
        self.addRow("Music: ", self.music_editor)
        self.addRow("Time: ", self.time_editor)
        self.addRow("Scroll Direction: ", self.scroll_editor)
        self.addWidget(check_box_widget)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            + f"{self.parent}, {self.level_length}, {self.music}, {self.time}, "
            + f"{self.scroll}, {self.horizontal}, {self.pipe_ends_level})"
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, LevelDataDisplay)
            and self.level_length == other.level_length
            and self.music == other.music
            and self.time == other.time
            and self.scroll == other.scroll
            and self.horizontal == other.horizontal
            and self.pipe_ends_level == other.pipe_ends_level
        )

    @property
    def level_length(self) -> int:
        """
        Provides the length of this level.

        Returns
        -------
        int
            The length of this level.
        """
        return self.level_length_editor.currentIndex()

    @level_length.setter
    def level_length(self, level_length: int):
        self.level_length_editor.setCurrentIndex(level_length)

    @property
    def music(self) -> int:
        """
        Provides the music of this level.

        Returns
        -------
        int
            The music of this level.
        """
        return self.music_editor.currentIndex()

    @music.setter
    def music(self, music: int):
        self.music_editor.setCurrentIndex(music)

    @property
    def time(self) -> int:
        """
        Provides the time of this level.

        Returns
        -------
        int
            The time of this level.
        """
        return self.time_editor.currentIndex()

    @time.setter
    def time(self, time: int):
        self.time_editor.setCurrentIndex(time)

    @property
    def scroll(self) -> int:
        """
        Provides the scroll of this level.

        Returns
        -------
        int
            The scroll of this level.
        """
        return self.scroll_editor.currentIndex()

    @scroll.setter
    def scroll(self, scroll: int):
        self.scroll_editor.setCurrentIndex(scroll)

    @property
    def horizontal(self) -> bool:
        """
        Provides if the level is horizontal.

        Returns
        -------
        bool
            If the level is horizontal.
        """
        return self.horizontal_editor.isChecked()

    @horizontal.setter
    def horizontal(self, horizontal: bool):
        self.horizontal_editor.setChecked(horizontal)

    @property
    def pipe_ends_level(self) -> bool:
        """
        Provides if entering a pipe will end the level.

        Returns
        -------
        bool
            If entering a pipe will end the level.
        """
        return self.pipe_ends_level_editor.isChecked()

    @pipe_ends_level.setter
    def pipe_ends_level(self, pipe_ends_level: bool):
        self.pipe_ends_level_editor.setChecked(pipe_ends_level)
