""" Implements a UI to modify the player lives.

Supported editing various characteristics of the player lives such as the
number of starting lives, the number of lives on continues, if a death lowers
the life count, if a 1-up mushroom increases the life count, etc.

This UI uses a Redux pattern instead of MVC to increase the testability of the
code.  If you are if you want to try to reason about Redux in terms of MVC,
then the Redux state is the model, the Redux reducer is the Controller, and
obviously both still have a view.
"""
from dataclasses import dataclass
from enum import Enum

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QBoxLayout, QCheckBox, QDialogButtonBox, QGroupBox, QLabel

from foundry.core.redux_store import Action, ReduxStore
from foundry.game.File import ROM
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from foundry.smb3parse.util.code_edit_dict import CodeEditDict
from foundry.smb3parse.util.rom import Rom


class _UIStrings(Enum):
    """All string values used in the UI."""

    TITLE = "Orb Options"
    INVALID_ROM_WARNING = (
        "The selected ROM has code modifications that are"
        " incompatible with one or more features of this window. The affected"
        " features are visible but disabled."
    )

    MOVE_TITLE = "After touching an orb, the player can move:"
    MOVE_TOUCH_TO_TIMER = "Until the timer is counted into the score"
    MOVE_TIMER_TO_EXIT = "After the timer is counted until the level exits"
    TOUCH_TITLE = "When the player touches an orb:"
    TOUCH_GAME_TIMER_STOPS = "Stop the game timer. Allows the player to touch a stray orb without dying."


class Actions(Enum):
    """All user actions that can be performed."""

    MOVE_TOUCH_TO_TIMER = "[Orb] MoveTouchToTimer"
    MOVE_TIMER_TO_EXIT = "[Orb] MoveTimerToExit"
    TOUCH_GAME_TIMER_STOPS = "[Orb] TouchGameTimerStops"


@dataclass
class State:
    """Stores the current state of the UI

    The initial state is read from the ROM.  The final state is written to the
    ROM.  The intermediate values are stored in this state object while the
    user is modifying them.

    NOTE: Some of these values may be optional/None if the search for these
    code regions fails when reading to the ROM.  Invalid values written to the
    state may also be rejected when trying to write the state to the ROM.
    """

    move_touch_to_timer: bool | None
    move_timer_to_exit: bool | None
    touch_game_timer_stops: bool | None


class Store(ReduxStore[State]):
    """Concrete implementation of the ReduxStore for the PlayerLives UI"""

    def _reduce(self, state: State, action: Action) -> State:
        """Processes a user action into a new state.

        Processes user actions in the player_lives UI into new state data.
        This function should NEVER be called directly by the user.  To change
        the state, do store.dispatch(Action()) instead.

        See ReduxStore for more information."""
        if state is None:
            state = self.get_default_state()

        if action is None:
            return state

        if action.type == Actions.MOVE_TOUCH_TO_TIMER.value:
            state.move_touch_to_timer = action.payload

        elif action.type == Actions.MOVE_TIMER_TO_EXIT.value:
            state.move_timer_to_exit = action.payload

        elif action.type == Actions.TOUCH_GAME_TIMER_STOPS.value:
            state.touch_game_timer_stops = action.payload

        return state


class RomInterface:
    """Handles all the read/write operations to the ROM.

    This reads out the initial state of the ROM into a new State object.  It
    can also take in a State object and write that into the ROM data.
    """

    def __init__(self, rom: Rom):
        """Create all of the CodeEdit objects for all UI selections."""
        self.rom = rom
        nop_x_3 = bytearray([0xEA, 0xEA, 0xEA])

        self._move_timer_to_exit = CodeEditDict(
            rom,
            0x68FD,
            3,
            bytearray([0x18, 0x05, 0xF0, 0x12]),
            {False: bytearray([0x8C, 0xF4, 0x7C]), True: nop_x_3},
            bytearray([0x88, 0xD0, 0x0B, 0x8C]),
        )

        self._move_touch_to_timer = CodeEditDict(
            rom,
            0x6913,
            3,
            bytearray([0xB5, 0x9A, 0xF0, 0x0E]),
            {False: bytearray([0x8D, 0xF4, 0x7C]), True: nop_x_3},
            bytearray([0x20, 0x12, 0xC4, 0xD0]),
        )

        self._stop_timer = self.StrayOrb(rom)

    def read_state(self) -> State:
        """Reads the ROM and creates a cooresponding abstract State instance."""
        return State(self._move_touch_to_timer.read(), self._move_timer_to_exit.read(), self._stop_timer.read())

    def write_state(self, state: State):
        """Takes in an abstract State instance, and writes to the ROM.

        NOTE: This writes to the specified ROM which is not writing to the
        file itself.  The caller/user is responsible for requesting the changes
        be saved to the file.
        """
        self._move_touch_to_timer.write(state.move_touch_to_timer)
        self._move_timer_to_exit.write(state.move_timer_to_exit)
        self._stop_timer.write(state.touch_game_timer_stops)

    class StrayOrb:
        def __init__(self, rom: Rom):
            self._rom = rom

            self._jump_table = CodeEditDict(
                rom,
                0x6014,
                2,
                bytearray([0x46, 0xBF, 0xFF, 0xA9]),
                {False: bytearray([0x5B, 0xA9]), True: bytearray([0xBF, 0xBF])},
                bytearray([0x88, 0xD0, 0x0B, 0x8C]),
            )

            self._stop_timer = CodeEditDict(
                rom,
                0x7FCF,
                6,
                bytearray([0x07, 0x4C, 0xE7, 0xD5]),
                {
                    False: bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]),
                    True: bytearray([0xA9, 0x01, 0x8D, 0xF3, 0x05, 0x60]),
                },
                bytearray(),
            )

        def read(self) -> bool | None:
            results_list = [self._jump_table.read(), self._stop_timer.read()]

            if results_list[0] != results_list[1]:
                return None

            return results_list[0]

        def write(self, option: bool):
            if self.read() is not None and self._jump_table.is_option(option) and self._stop_timer.is_option(option):
                self._jump_table.write(option)
                self._stop_timer.write(option)


class View(CustomDialog):
    """Creates the UI and sends actions to update the State

    The view operates only on the State variable.  It doesn't operate on the
    ROM at all.  When the user clicks OK to submit the changes to the ROM, the
    view will send a request to the RomInterface to have the state written to
    the ROM.
    """

    store: Store
    rom_interface: RomInterface

    _move_touch_to_timer: QCheckBox
    _move_timer_to_exit: QCheckBox
    _touch_game_timer_stops: QCheckBox

    WARNING_STYLE = "QLabel { background-color : pink; }"

    def __init__(self, parent, store: Store, rom_interface: RomInterface):
        """Creates the main layout and shows the form.

        All UI elements will dispatch an action on change which will
        update the internal state.  On "OK" the internal state will be written
        to the ROM.

        The render() routine subscribes to the store so that whenever the
        state changes in the system, the UI will automatically re-render.
        """

        super().__init__(parent, title=_UIStrings.TITLE.value)
        self.rom_interface = rom_interface
        self.store = store

        main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)

        main_layout.addLayout(self._create_invalid_rom_layout())
        main_layout.addLayout(self._create_touch_options_layout())
        main_layout.addLayout(self._create_move_options_layout())
        main_layout.addWidget(HorizontalLine())
        main_layout.addWidget(self._create_button_options_layout(), alignment=Qt.AlignRight)

        self.store.subscribe(self.render)
        self.render()
        self.show()

    def _create_invalid_rom_layout(self) -> QBoxLayout:
        """Create warning about the ROM having incompatible code modifications.

        If the user has provided a ROM that has shifted some of the code, then
        some of the UI elements might not be able to work correctly.  This
        creates a warning label to the user to let them know that some of the
        features are unsupported."""

        _invalid_rom_warning_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._invalid_rom_warning = QLabel(f"{_UIStrings.INVALID_ROM_WARNING.value}")
        self._invalid_rom_warning.setWordWrap(True)
        self._invalid_rom_warning.setFixedWidth(500)
        self._invalid_rom_warning.setStyleSheet(self.WARNING_STYLE)
        _invalid_rom_warning_layout.addWidget(self._invalid_rom_warning)

        return _invalid_rom_warning_layout

    def _create_touch_options_layout(self) -> QBoxLayout:
        external_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group = QGroupBox(f"{_UIStrings.TOUCH_TITLE.value}")
        internal_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group.setLayout(internal_layout)

        self._touch_game_timer_stops = View._create_checkbox(
            _UIStrings.TOUCH_GAME_TIMER_STOPS.value, self._on_touch_game_timer_stops, internal_layout
        )

        external_layout.addWidget(group)
        return external_layout

    def _create_move_options_layout(self) -> QBoxLayout:
        external_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group = QGroupBox(f"{_UIStrings.MOVE_TITLE.value}")
        internal_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group.setLayout(internal_layout)

        self._move_touch_to_timer = View._create_checkbox(
            _UIStrings.MOVE_TOUCH_TO_TIMER.value, self._on_move_touch_to_timer, internal_layout
        )

        self._move_timer_to_exit = View._create_checkbox(
            _UIStrings.MOVE_TIMER_TO_EXIT.value, self._on_move_timer_to_exit, internal_layout
        )

        external_layout.addWidget(group)
        return external_layout

    def _create_button_options_layout(self) -> QDialogButtonBox:
        """Creates layout for the OK/CANCEL buttons."""

        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Ok).clicked.connect(self._on_ok)
        button_box.addButton(QDialogButtonBox.Cancel).clicked.connect(self._on_cancel)

        return button_box

    @staticmethod
    def _create_checkbox(title: str, function, layout: QBoxLayout) -> QCheckBox:
        """Creates a checkbox with an stateChange callback and adds it to the specified layout"""

        checkbox = QCheckBox(f"{title}")
        checkbox.stateChanged.connect(function)
        layout.addWidget(checkbox)
        return checkbox

    def render(self):
        """Updates the UI with the current state values.

        This function is the subscriber to the store so that whenever there is
        a state change in the system, this render function is called
        automatically and the new state is rendered on screen.
        """

        state = self.store.get_state()

        View._render_checkbox(self._move_touch_to_timer, state.move_touch_to_timer)
        View._render_checkbox(self._move_timer_to_exit, state.move_timer_to_exit)
        View._render_checkbox(self._touch_game_timer_stops, state.touch_game_timer_stops)

        self._invalid_rom_warning.setVisible(View._all_areas_valid(state) is False)

    @staticmethod
    def _render_checkbox(checkbox: QCheckBox, value: bool):
        """Render a checkbox value."""

        checkbox.setDisabled(value is None)
        checkbox.setChecked(False if value is None else value)

    @staticmethod
    def _all_areas_valid(state: State) -> bool:
        """Checks to make sure all state values are valid."""
        return (
            state.move_touch_to_timer is not None
            and state.move_timer_to_exit is not None
            and state.touch_game_timer_stops is not None
        )

    def _on_ok(self):
        """Process UI press of OK button."""
        self.rom_interface.write_state(self.store.get_state())
        self.done(QDialogButtonBox.Ok)

    def _on_cancel(self):
        """Process UI press of CANCEL button."""
        self.done(QDialogButtonBox.Cancel)

    def _on_move_touch_to_timer(self):
        self.store.dispatch(Action(Actions.MOVE_TOUCH_TO_TIMER.value, self._move_touch_to_timer.isChecked()))

    def _on_move_timer_to_exit(self):
        self.store.dispatch(Action(Actions.MOVE_TIMER_TO_EXIT.value, self._move_timer_to_exit.isChecked()))

    def _on_touch_game_timer_stops(self):
        self.store.dispatch(Action(Actions.TOUCH_GAME_TIMER_STOPS.value, self._touch_game_timer_stops.isChecked()))


class Orb:
    """Main entry point from main menu.

    This creates the Store, the View, and the RomInterface.
    """

    def __init__(self, parent):
        rom_interface = RomInterface(ROM())
        store = Store(rom_interface.read_state())
        View(parent, store, rom_interface)
