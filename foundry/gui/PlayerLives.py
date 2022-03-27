from email.policy import default
from PySide6.QtGui import QPixmap, Qt, QIntValidator
from PySide6.QtWidgets import QBoxLayout, QLabel, QDialogButtonBox, QLineEdit, QGridLayout, QCheckBox, QGroupBox

from dataclasses import dataclass
import copy

from foundry.smb3parse.util.rom import Rom
from foundry.game.File import ROM
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.code_edit_byte import CodeEditByte
from foundry.smb3parse.util.code_edit_dict import CodeEditDict
from foundry.core.ReduxStore import ReduxStore, Action

@dataclass
class UIStrings:
    title = "Player Lives"
    starting_lives = "Starting Lives"
    continue_lives = "Continue Lives"
    invalid_rom_warning = "The selected ROM has code modifications that are incompatible with one or more features of this window. The affected features are visible but disabled."
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

ACTION_LOAD = Action(ActionNames.load, None)

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
    def reduce(self, state:State, action: Action) -> State:
        if state is None:
            state = self.getDefault()

        if action.type == ActionNames.starting_lives:
            if Store.__isBoundedInteger(action.payload, 0, 99):
                state.starting_lives = int(action.payload)

        elif action.type == ActionNames.continue_lives:
            if Store.__isBoundedInteger(action.payload, 0, 99):
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
            state = self.getDefault()

        return state

    def __isBoundedInteger(input, lower_limit: int, upper_limit: int) -> bool:
        try:
            return (int(input) >= lower_limit) & (int(input) <= upper_limit)
        except ValueError:
            return False

class RomInterface():
    def __init__(self, rom: Rom):
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

    def readState(self) -> State:
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

    def writeState(self, state: State):
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
    store : Store
    romInterface : RomInterface

    starting_lives_edit : QLineEdit
    continue_lives_edit : QLineEdit
    invalid_rom_warning : QLabel
    death_takes_lives: QCheckBox
    hundred_coins_1up: QCheckBox
    end_card_1up: QCheckBox
    mushroom_1up: QCheckBox
    dice_game_1up: QCheckBox
    roulette_1up: QCheckBox
    card_game_1up: QCheckBox


    def __create_invalid_rom_layout(self) -> QBoxLayout:
        invalid_rom_warning_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.invalid_rom_warning = QLabel(f"{UIStrings.invalid_rom_warning}")
        self.invalid_rom_warning.setWordWrap(True)
        self.invalid_rom_warning.setFixedWidth(400)
        self.invalid_rom_warning.setStyleSheet("QLabel { background-color : pink; }")   # I didn't see a style sheet to draw from, should probably create one?  Better way to do this?
        invalid_rom_warning_layout.addWidget(self.invalid_rom_warning)

        return invalid_rom_warning_layout

    def __create_lives_layout(self) -> QGridLayout:
        self.starting_lives_edit = QLineEdit(self)
        self.starting_lives_edit.setValidator(QIntValidator(0, 99, self))
        self.starting_lives_edit.textEdited.connect(self.__on_starting_lives)

        self.continue_lives_edit = QLineEdit(self)
        self.continue_lives_edit.setValidator(QIntValidator(0, 99, self))
        self.continue_lives_edit.textEdited.connect(self.__on_continue_lives)

        fields_layout = QGridLayout()
        fields_layout.addWidget(QLabel(f"{UIStrings.starting_lives} (0-99):", self), 0, 0)
        fields_layout.addWidget(self.starting_lives_edit, 0, 1)
        fields_layout.addWidget(QLabel(f"{UIStrings.continue_lives} (0-99):", self), 1, 0)
        fields_layout.addWidget(self.continue_lives_edit, 1, 1)

        return fields_layout

    def __create_death_options_layout(self) -> QBoxLayout:
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.death_takes_lives = View.__create_checkbox(UIStrings.death_takes_lives, self.__on_death_takes_lives, layout)
        return layout

    def __create_button_options_layout(self) -> QDialogButtonBox:
        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Ok).clicked.connect(self.__on_ok)
        button_box.addButton(QDialogButtonBox.Cancel).clicked.connect(self.__on_cancel)
    
        return button_box

    def __create_1up_layout(self) -> QBoxLayout:
        external_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group = QGroupBox(f"{UIStrings.title_1up}")
        internal_layout = QBoxLayout(QBoxLayout.TopToBottom)
        group.setLayout(internal_layout)

        self.mushroom_1up = View.__create_checkbox(UIStrings.mushroom_1up, self.__on_mushroom_1up, internal_layout)
        self.hundred_coins_1up = View.__create_checkbox(UIStrings.hundred_coins_1up, self.__on_hundred_coins_1up, internal_layout)
        self.end_card_1up = View.__create_checkbox(UIStrings.end_card_1up, self.__on_end_card_1up, internal_layout)
        self.card_game_1up = View.__create_checkbox(UIStrings.card_game_1up, self.__on_card_game_1up, internal_layout)
        self.roulette_1up = View.__create_checkbox(UIStrings.roulette_1up, self.__on_roulette_1up, internal_layout)
        self.dice_game_1up = View.__create_checkbox(UIStrings.dice_game_1up, self.__on_dice_game_1up, internal_layout)
        
        external_layout.addWidget(group)
        return external_layout

    def __create_checkbox(title: str, function, layout: QBoxLayout) -> QCheckBox:
        checkbox = QCheckBox(f"{title}")
        checkbox.stateChanged.connect(function)
        layout.addWidget(checkbox)
        return checkbox

    def __init__(self, parent, store : Store, romInterface : RomInterface):
        super(View, self).__init__(parent, title=UIStrings.title)
        self.romInterface = romInterface
        self.store = store

        main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)

        main_layout.addLayout(self.__create_invalid_rom_layout())
        main_layout.addLayout(self.__create_lives_layout())
        main_layout.addLayout(self.__create_death_options_layout())
        main_layout.addLayout(self.__create_1up_layout())
        main_layout.addWidget(HorizontalLine())
        main_layout.addWidget(self.__create_button_options_layout(), alignment=Qt.AlignRight)

        self.store.subscribe(self.render)
        self.render()
        self.show()

    def render(self):
        state = self.store.getState()

        View.__renderLineEdit(self.starting_lives_edit, state.starting_lives)
        View.__renderLineEdit(self.continue_lives_edit, state.continue_lives)

        View.__renderCheckbox(self.death_takes_lives, state.death_takes_lives)
        View.__renderCheckbox(self.hundred_coins_1up, state.hundred_coins_1up)
        View.__renderCheckbox(self.end_card_1up, state.end_card_1up)
        View.__renderCheckbox(self.mushroom_1up, state.mushroom_1up)
        View.__renderCheckbox(self.dice_game_1up, state.dice_game_1up)
        View.__renderCheckbox(self.roulette_1up, state.roulette_1up)
        View.__renderCheckbox(self.card_game_1up, state.card_game_1up)

        self.invalid_rom_warning.setVisible(View.__allAreasValid(state) == False)  
    
    def __intOrDefaultToString(value: str, default: str):
        return default if value is None else str(value)

    def __renderLineEdit(lineEdit: QLineEdit, value: int):
        lineEdit.setDisabled(value == None)
        lineEdit.setText(View.__intOrDefaultToString(value, "?"))

    def __renderCheckbox(checkBox: QCheckBox, value: bool):
        checkBox.setDisabled(value is None)
        checkBox.setChecked(False if value is None else value)

    def __allAreasValid(state : State) -> bool:
        return  state.starting_lives is not None and\
                state.continue_lives is not None and\
                state.death_takes_lives is not None and\
                state.hundred_coins_1up is not None and\
                state.end_card_1up is not None and\
                state.mushroom_1up is not None and\
                state.dice_game_1up is not None and\
                state.roulette_1up is not None and\
                state.card_game_1up is not None

    def __on_ok(self):
        self.romInterface.writeState(self.store.getState())
        self.done(QDialogButtonBox.Ok)

    def __on_cancel(self):
        self.done(QDialogButtonBox.Cancel)

    def __on_starting_lives(self, text : str):
        self.store.dispatch(Action(ActionNames.starting_lives, text))

    def __on_continue_lives(self, text : str):
        self.store.dispatch(Action(ActionNames.continue_lives, text))

    def __on_death_takes_lives(self):
        self.store.dispatch(Action(ActionNames.death_takes_lives, self.death_takes_lives.isChecked()))

    def __on_end_card_1up(self):
        self.store.dispatch(Action(ActionNames.end_card_1up, self.end_card_1up.isChecked()))

    def __on_mushroom_1up(self):
        self.store.dispatch(Action(ActionNames.mushroom_1up, self.mushroom_1up.isChecked()))

    def __on_dice_game_1up(self):
        self.store.dispatch(Action(ActionNames.dice_game_1up, self.dice_game_1up.isChecked()))

    def __on_roulette_1up(self):
        self.store.dispatch(Action(ActionNames.roulette_1up, self.roulette_1up.isChecked()))

    def __on_card_game_1up(self):
        self.store.dispatch(Action(ActionNames.card_game_1up, self.card_game_1up.isChecked()))

    def __on_hundred_coins_1up(self):
        self.store.dispatch(Action(ActionNames.hundred_coins_1up, self.hundred_coins_1up.isChecked()))

class PlayerLives():
    def __init__(self, parent):
        romInterface = RomInterface(ROM())        
        store = Store(romInterface.readState())               
        View(parent, store, romInterface)
