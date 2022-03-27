from email.policy import default
from PySide6.QtGui import QPixmap, Qt, QIntValidator
from PySide6.QtWidgets import QBoxLayout, QLabel, QDialogButtonBox, QLineEdit, QGridLayout, QCheckBox, QGroupBox

from dataclasses import dataclass
from foundry.smb3parse.util.rom import Rom
from foundry.game.File import ROM
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from foundry.smb3parse.util.code_edit_byte import CodeEditByte
from foundry.smb3parse.util.code_edit_dict import CodeEditDict
from foundry.core.redux_store import ReduxStore, Action

@dataclass
class _UIStrings:
    """ All string values used in the UI. """

    title = "Player Lives"
    starting_lives = "Starting Lives"
    continue_lives = "Continue Lives"
    invalid_rom_warning = "The selected ROM has code modifications that are"  \
        " incompatible with one or more features of this window. The affected" \
        " features are visible but disabled."
    death_takes_lives = "Subtract a life when the player dies"
    title_1up = "Add a life when player gets 1up from:"
    end_card_1up = "Level end card"
    mushroom_1up = "1up Mushroom / Jumps on enemies "
    dice_game_1up = "Dice Game"
    roulette_1up = "Roulette Game"
    card_game_1up = "Card Game"
    hundred_coins_1up = "100 Coins"

@dataclass
class ActionNames:
    """ All user actions that can be performed. """

    load = "[PlayerLives] Load"
    starting_lives = "[PlayerLives] StartingLives"
    continue_lives = "[PlayerLives] ContinueLives"
    death_takes_lives = "[PlayerLives] DeathTakesLives"
    hundred_coins_1up = "[PlayerLives] 100Coins"
    end_card_1up = "[PlayerLives] EndCard"
    mushroom_1up = "[PlayerLives] Mushroom"
    dice_game_1up = "[PlayerLives] DiceGame"
    roulette_1up = "[PlayerLives] Roulette"
    card_game_1up = "[PlayerLives] CardGame"

@dataclass
class State:
    starting_lives: int
    continue_lives: int
    death_takes_lives: bool
    hundred_coins_1up: bool
    end_card_1up: bool
    mushroom_1up: bool
    dice_game_1up: bool
    roulette_1up: bool
    card_game_1up: bool

class Store(ReduxStore[State]):        
    def _reduce(self, state:State, action: Action) -> State:
        """ Processes a user action into a new state.
        
        Processes user actions in the player_lives UI into new state data.  
        This function should NEVER be called directly by the user.  To change
        the state, do store.dispatch(Action()) instead.
        
        See ReduxStore for more information."""
        if state is None:
            state = self.get_default_state()

        if action.type == ActionNames.starting_lives:
            if Store._is_bounded_int(action.payload, 0, 99):
                state.starting_lives = int(action.payload)

        elif action.type == ActionNames.continue_lives:
            if Store._is_bounded_int(action.payload, 0, 99):
                state.continue_lives = int(action.payload)

        elif action.type == ActionNames.death_takes_lives:
            state.death_takes_lives = action.payload

        elif action.type == ActionNames.hundred_coins_1up:
            state.hundred_coins_1up = action.payload

        elif action.type == ActionNames.end_card_1up:
            state.end_card_1up = action.payload

        elif action.type == ActionNames.mushroom_1up:
            state.mushroom_1up = action.payload

        elif action.type == ActionNames.dice_game_1up:
            state.dice_game_1up = action.payload

        elif action.type == ActionNames.roulette_1up:
            state.roulette_1up = action.payload

        elif action.type == ActionNames.card_game_1up:
            state.card_game_1up = action.payload

        elif action.type == ActionNames.load:
            state = self.get_default_state()

        return state

    def _is_bounded_int(input, lower_limit: int, upper_limit: int) -> bool:
        """ Checks if the input is an int and within a min/max boundary. """
        try:
            return (int(input) >= lower_limit) & (int(input) <= upper_limit)
        except ValueError:
            return False

class RomInterface():
    """ Handles all the read/write operations to the ROM.
    
    This reads out the initial state of the ROM into a new State object.  It 
    can also take in a State object and write that into the ROM data.
    """

    def __init__(self, rom: Rom):
        """ Create all of the CodeEdit objects for all UI selections. """
        self.rom = rom
        NOP_X_3 = bytearray([0xEA, 0xEA, 0xEA])
        INC_NUM_LIVES = bytearray([0xfe, 0x36, 0x07])
        
        self.death_takes_lives = CodeEditDict(
            rom, 
            0x3D133, 
            3, 
            bytearray([0x8B, 0x07, 0xD0, 0x05]),
            {
                True: bytearray([0xDE, 0x36, 0x07]),
                False: NOP_X_3
            },
            bytearray([0x30, 0x0b, 0xA9, 0x80]))

        self.starting_lives = CodeEditByte(
            rom, 
            0x308E1, 
            bytearray([0xCA, 0x10, 0xF8, 0xA9]), 
            bytearray([0x8D, 0x36, 0x07, 0x8D]))
        
        self.continue_lives = CodeEditByte(
            rom, 
            0x3D2D6, 
            bytearray([0x08, 0xD0, 0x65, 0xA9]), 
            bytearray([0x9D, 0x36, 0x07, 0xA5]))

        self.hundred_coins_1up = CodeEditDict(
            rom, 
            0x350A7, 
            3, 
            bytearray([0x7d, 0xae, 0x26, 0x07]),
            {
                True: INC_NUM_LIVES,
                False: NOP_X_3
            },
            bytearray([0xa9, 0x40, 0x8d, 0xf2]))
        
        self.end_card_1up = CodeEditDict(
            rom, 
            0x5d99, 
            3, 
            bytearray([0x60, 0xae, 0x26, 0x07]),
            {
                True: INC_NUM_LIVES,
                False: NOP_X_3
            },
            bytearray([0xee, 0x40, 0x04, 0x60]))

        self.mushroom_1up = CodeEditDict(
            rom, 
            0xeb0f, 
            3, 
            bytearray([0x36, 0x07, 0x30, 0x03]),
            {
                True: INC_NUM_LIVES,
                False: NOP_X_3
            },
            bytearray([0xa6, 0xcd, 0xbd, 0xa3]))

        self.dice_game_1up = CodeEditDict(
            rom, 
            0x2cd78, 
            3, 
            bytearray([0x60, 0xae, 0x26, 0x07]),
            {
                True: INC_NUM_LIVES,
                False: NOP_X_3
            },
            bytearray([0xee, 0x40, 0x04, 0x60]))

        self.roulette_1up = CodeEditDict(
            rom, 
            0x2d2be, 
            3, 
            bytearray([0x36, 0x07, 0x30, 0x03]),
            {
                True: INC_NUM_LIVES,
                False: NOP_X_3
            },
            bytearray([0x4c, 0xd2, 0xd2, 0xce]))

        self.card_game_1up = CodeEditDict(
            rom, 
            0x2dd50, 
            3, 
            bytearray([0x0d, 0xae, 0x26, 0x07]),
            {
                True: INC_NUM_LIVES,
                False: NOP_X_3
            },
            bytearray([0xa9, 0x40, 0x8d, 0xf2]))

    def read_state(self) -> State:
        """ Reads the ROM and creates a cooresponding abstract State instance. """
        return State(   
                        self.starting_lives.read(),
                        self.continue_lives.read(),
                        self.death_takes_lives.read(),
                        self.hundred_coins_1up.read(),
                        self.end_card_1up.read(),
                        self.mushroom_1up.read(),
                        self.dice_game_1up.read(),
                        self.roulette_1up.read(),
                        self.card_game_1up.read()
                    )

    def write_state(self, state: State):
        """ Takes in an abstract State instance, and writes to the ROM.
        
        NOTE: This writes to the specified ROM which is not writing to the
        file itself.  The caller/user is responsible for requesting the changes
        be saved to the file.
        """
        self.starting_lives.write(state.starting_lives)
        self.continue_lives.write(state.continue_lives)
        self.death_takes_lives.write(state.death_takes_lives)
        self.hundred_coins_1up.write(state.hundred_coins_1up)    
        self.end_card_1up.write(state.end_card_1up)
        self.mushroom_1up.write(state.mushroom_1up)
        self.dice_game_1up.write(state.dice_game_1up)
        self.roulette_1up.write(state.roulette_1up)
        self.card_game_1up.write(state.card_game_1up)

class View(CustomDialog):
    """ Creates the UI and sends actions to update the State
    
    The view operates only on the State variable.  It doesn't operate on the
    ROM at all.  When the user clicks OK to submit the changes to the ROM, the
    view will send a request to the RomInterface to have the state written to
    the ROM.
    """
    store : Store
    rom_interface : RomInterface

    _starting_lives_edit : QLineEdit
    _continue_lives_edit : QLineEdit
    _invalid_rom_warning : QLabel
    _death_takes_lives: QCheckBox
    _hundred_coins_1up: QCheckBox
    _end_card_1up: QCheckBox
    _mushroom_1up: QCheckBox
    _dice_game_1up: QCheckBox
    _roulette_1up: QCheckBox
    _card_game_1up: QCheckBox

    WARNING_STYLE = "QLabel { background-color : pink; }"

    def __init__(self, parent, store : Store, rom_interface : RomInterface):
        """ Creates the main layout and shows the form. 
        
        All UI elements will dispatch an action on change which will
        update the internal state.  On "OK" the internal state will be written
        to the ROM.  

        The render() routine subscribes to the store so that whenever the 
        state changes in the system, the UI will automatically re-render.
        """

        super(View, self).__init__(parent, title=_UIStrings.title)
        self.rom_interface = rom_interface
        self.store = store

        main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)

        main_layout.addLayout(self._create_invalid_rom_layout())
        main_layout.addLayout(self._create_lives_layout())
        main_layout.addLayout(self._create_death_options_layout())
        main_layout.addLayout(self._create_1up_layout())
        main_layout.addWidget(HorizontalLine())
        main_layout.addWidget(
            self._create_button_options_layout(), alignment=Qt.AlignRight)

        self.store.subscribe(self.render)
        self.render()
        self.show()

    def _create_invalid_rom_layout(self) -> QBoxLayout:
        """ Create warning about the ROM having incompatible code modifications. 
        
        If the user has provided a ROM that has shifted some of the code, then 
        some of the UI elements might not be able to work correctly.  This
        creates a warning label to the user to let them know that some of the
        features are unsupported. """

        _invalid_rom_warning_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._invalid_rom_warning = QLabel(f"{_UIStrings.invalid_rom_warning}")
        self._invalid_rom_warning.setWordWrap(True)
        self._invalid_rom_warning.setFixedWidth(400)
        self._invalid_rom_warning.setStyleSheet(self.WARNING_STYLE)
        _invalid_rom_warning_layout.addWidget(self._invalid_rom_warning)

        return _invalid_rom_warning_layout

    def _create_lives_layout(self) -> QGridLayout:
        """ Creates the inputs for the start and continue number of lives. """

        self._starting_lives_edit = QLineEdit(self)
        self._starting_lives_edit.setValidator(QIntValidator(0, 99, self))
        self._starting_lives_edit.textEdited.connect(self._on_starting_lives)

        self._continue_lives_edit = QLineEdit(self)
        self._continue_lives_edit.setValidator(QIntValidator(0, 99, self))
        self._continue_lives_edit.textEdited.connect(self._on_continue_lives)

        fields_layout = QGridLayout()
        fields_layout.addWidget(
            QLabel(f"{_UIStrings.starting_lives} (0-99):", self), 0, 0)
        fields_layout.addWidget(self._starting_lives_edit, 0, 1)
        fields_layout.addWidget(
            QLabel(f"{_UIStrings.continue_lives} (0-99):", self), 1, 0)
        fields_layout.addWidget(self._continue_lives_edit, 1, 1)

        return fields_layout

    def _create_death_options_layout(self) -> QBoxLayout:
        """ Creates layout for when a death occurs. """

        layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._death_takes_lives = View._create_checkbox(
            _UIStrings.death_takes_lives, 
            self._on_death_takes_lives, 
            layout)
        return layout

    def _create_button_options_layout(self) -> QDialogButtonBox:
        """ Creates layout for the OK/CANCEL buttons. """

        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Ok).clicked.connect(self._on_ok)
        button_box.addButton(QDialogButtonBox.Cancel).clicked.connect(self._on_cancel)
    
        return button_box

    def _create_1up_layout(self) -> QBoxLayout:
        """ Creates the layout for all of the possible 1up sources. """

        external_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group = QGroupBox(f"{_UIStrings.title_1up}")
        internal_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group.setLayout(internal_layout)

        self._mushroom_1up = View._create_checkbox(
            _UIStrings.mushroom_1up, 
            self._on_mushroom_1up, 
            internal_layout)

        self._hundred_coins_1up = View._create_checkbox(
            _UIStrings.hundred_coins_1up, 
            self._on_hundred_coins_1up, 
            internal_layout)

        self._end_card_1up = View._create_checkbox(
            _UIStrings.end_card_1up, 
            self._on_end_card_1up, 
            internal_layout)

        self._card_game_1up = View._create_checkbox(
            _UIStrings.card_game_1up, 
            self._on_card_game_1up, 
            internal_layout)

        self._roulette_1up = View._create_checkbox(
            _UIStrings.roulette_1up, 
            self._on_roulette_1up, 
            internal_layout)

        self._dice_game_1up = View._create_checkbox(
            _UIStrings.dice_game_1up, 
            self._on_dice_game_1up, 
            internal_layout)
        
        external_layout.addWidget(group)
        return external_layout

    def _create_checkbox(title: str, function, layout: QBoxLayout) -> QCheckBox:
        """ Creates a checkbox with an stateChange callback and adds it to the specified layout"""

        checkbox = QCheckBox(f"{title}")
        checkbox.stateChanged.connect(function)
        layout.addWidget(checkbox)
        return checkbox

    def render(self):
        """ Updates the UI with the current state values. 

        This function is the subscriber to the store so that whenever there is
        a state change in the system, this render function is called
        automatically and the new state is rendered on screen.
        """

        state = self.store.get_state()

        View._render_line_edit(self._starting_lives_edit, state.starting_lives)
        View._render_line_edit(self._continue_lives_edit, state.continue_lives)

        View._render_checkbox(self._death_takes_lives, state.death_takes_lives)
        View._render_checkbox(self._hundred_coins_1up, state.hundred_coins_1up)
        View._render_checkbox(self._end_card_1up, state.end_card_1up)
        View._render_checkbox(self._mushroom_1up, state.mushroom_1up)
        View._render_checkbox(self._dice_game_1up, state.dice_game_1up)
        View._render_checkbox(self._roulette_1up, state.roulette_1up)
        View._render_checkbox(self._card_game_1up, state.card_game_1up)

        self._invalid_rom_warning.setVisible(View._all_areas_valid(state) == False)  
    
    def _int_to_str_or_default(value: str, default: str):
        """ Converts an int to a str or provides a default if the int is None. """

        return default if value is None else str(value)

    def _render_line_edit(lineEdit: QLineEdit, value: int):
        """ Render a line edit value. """

        lineEdit.setDisabled(value == None)
        lineEdit.setText(View._int_to_str_or_default(value, "?"))

    def _render_checkbox(checkBox: QCheckBox, value: bool):
        """ Render a checkbox value. """

        checkBox.setDisabled(value is None)
        checkBox.setChecked(False if value is None else value)

    def _all_areas_valid(state : State) -> bool:
        """ Checks to make sure all state values are valid. """
        return  state.starting_lives is not None and\
                state.continue_lives is not None and\
                state.death_takes_lives is not None and\
                state.hundred_coins_1up is not None and\
                state.end_card_1up is not None and\
                state.mushroom_1up is not None and\
                state.dice_game_1up is not None and\
                state.roulette_1up is not None and\
                state.card_game_1up is not None

    def _on_ok(self):
        """ Process UI press of OK button. """
        self.rom_interface.write_state(self.store.get_state())
        self.done(QDialogButtonBox.Ok)

    def _on_cancel(self):
        """ Process UI press of CANCEL button. """
        self.done(QDialogButtonBox.Cancel)

    def _on_starting_lives(self, text : str):
        """ Process UI change of number of starting lives """
        self.store.dispatch(Action(
            ActionNames.starting_lives, 
            text))

    def _on_continue_lives(self, text : str):
        """ Process UI change of number of continue lives """
        self.store.dispatch(Action(
            ActionNames.continue_lives, 
            text))

    def _on_death_takes_lives(self):
        """ Process UI change of on death checkbox """
        self.store.dispatch(Action(
            ActionNames.death_takes_lives, 
            self._death_takes_lives.isChecked()))

    def _on_end_card_1up(self):
        """ Process UI change of end card 1up checkbox """
        self.store.dispatch(Action(
            ActionNames.end_card_1up, 
            self._end_card_1up.isChecked()))

    def _on_mushroom_1up(self):
        """ Process UI change of mushroom/enemy jumps 1up checkbox """
        self.store.dispatch(Action(
            ActionNames.mushroom_1up, 
            self._mushroom_1up.isChecked()))

    def _on_dice_game_1up(self):
        """ Process UI change of dice game 1up checkbox """
        self.store.dispatch(Action(
            ActionNames.dice_game_1up, 
            self._dice_game_1up.isChecked()))

    def _on_roulette_1up(self):
        """ Process UI change of roulette 1up checkbox """
        self.store.dispatch(Action(
            ActionNames.roulette_1up, 
            self._roulette_1up.isChecked()))

    def _on_card_game_1up(self):
        """ Process UI change of card game 1up checkbox """
        self.store.dispatch(Action(
            ActionNames.card_game_1up, 
            self._card_game_1up.isChecked()))

    def _on_hundred_coins_1up(self):
        """ Process UI change of 100 coins 1up checkbox """
        self.store.dispatch(Action(
            ActionNames.hundred_coins_1up, 
            self._hundred_coins_1up.isChecked()))

class PlayerLives():
    """ Main entry point from main menu. 
    
    This creates the Store, the View, and the RomInterface.
    """
    def __init__(self, parent):
        rom_interface = RomInterface(ROM())        
        store = Store(rom_interface.read_state())               
        View(parent, store, rom_interface)
