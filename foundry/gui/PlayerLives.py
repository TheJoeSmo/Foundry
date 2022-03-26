from email.policy import default
from PySide6.QtGui import QPixmap, Qt, QIntValidator
from PySide6.QtWidgets import QBoxLayout, QLabel, QDialogButtonBox, QLineEdit, QGridLayout, QCheckBox

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

@dataclass
class ActionNames:
    load = "[PlayerLives] Load"
    starting_lives = "[PlayerLives] StartingLives"
    continue_lives = "[PlayerLives] ContinueLives"
    death_takes_lives = "[PlayerLives] DeathTakesLives"

ACTION_LOAD = Action(ActionNames.load, None)

@dataclass
class State:
    starting_lives: int
    starting_lives_area_valid: bool
    continue_lives: int
    continue_lives_area_valid: bool
    death_takes_lives: bool
    death_takes_lives_area_valid: bool

class Store(ReduxStore[State]):        
    def reduce(self, state:State, action: Action) -> State:
        if state is None:
            state = self.getDefault()

        if action.type == ActionNames.starting_lives:
            print(action.payload)
            if Store.__isBoundedInteger(action.payload, 0, 99):
                state.starting_lives = int(action.payload)

        elif action.type == ActionNames.continue_lives:
            if Store.__isBoundedInteger(action.payload, 0, 99):
                state.continue_lives = int(action.payload)

        elif action.type == ActionNames.load:
            state = self.getDefault()

        elif action.type == ActionNames.death_takes_lives:
            state.death_takes_lives = action.payload

        return state

    def __isBoundedInteger(input, lower_limit: int, upper_limit: int) -> bool:
        try:
            return (int(input) >= lower_limit) & (int(input) <= upper_limit)
        except ValueError:
            return False

class RomInterface():
    def __init__(self, rom: Rom):
        self.rom = rom
        death_takes_lives_dict = {
            True: bytearray([0xDE, 0x36, 0x07]),
            False: bytearray([0xEA, 0xEA, 0xEA])
        }
        self.death_takes_lives = CodeEditDict(rom, 0x3D133, 3, bytearray([0x8B, 0x07, 0xD0, 0x05]), bytearray([0x30, 0x0b, 0xA9, 0x80]), death_takes_lives_dict)
        self.starting_lives = CodeEditByte(rom, 0x308E1, bytearray([0xCA, 0x10, 0xF8, 0xA9]), bytearray([0x8D, 0x36, 0x07, 0x8D]))
        self.continue_lives = CodeEditByte(rom, 0x3D2D6, bytearray([0x08, 0xD0, 0x65, 0xA9]), bytearray([0x9D, 0x36, 0x07, 0xA5]))
        
    def readState(self) -> State:
        return State(   
                        self.starting_lives.read(),
                        self.starting_lives.isValid(),
                        self.continue_lives.read(),
                        self.continue_lives.isValid(),
                        self.death_takes_lives.read(),
                        self.death_takes_lives.isValid()
                    )

    def writeState(self, state: State):
        self.starting_lives.write(state.starting_lives)
        self.continue_lives.write(state.continue_lives)
        self.death_takes_lives.write(state.death_takes_lives)    

class View(CustomDialog):
    store : Store
    romInterface : RomInterface

    starting_lives_edit : QLineEdit
    continue_lives_edit : QLineEdit
    invalid_rom_warning : QLabel
    death_takes_lives: QCheckBox

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
        self.death_takes_lives = QCheckBox(f"{UIStrings.death_takes_lives}")
        self.death_takes_lives.stateChanged.connect(self.__on_death_takes_lives)
        layout.addWidget(self.death_takes_lives)

        return layout

    def __create_button_options_layout(self) -> QDialogButtonBox:
        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Ok).clicked.connect(self.__on_ok)
        button_box.addButton(QDialogButtonBox.Cancel).clicked.connect(self.__on_cancel)
    
        return button_box

    def __init__(self, parent, store : Store, romInterface : RomInterface):
        super(View, self).__init__(parent, title=UIStrings.title)
        self.romInterface = romInterface
        self.store = store

        main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)

        main_layout.addLayout(self.__create_invalid_rom_layout())
        main_layout.addLayout(self.__create_lives_layout())
        main_layout.addLayout(self.__create_death_options_layout())
        main_layout.addWidget(HorizontalLine())
        main_layout.addWidget(self.__create_button_options_layout(), alignment=Qt.AlignRight)

        self.store.subscribe(self.render)
        self.render()
        self.show()

    def render(self):
        state = self.store.getState()

        self.starting_lives_edit.setDisabled(state.starting_lives_area_valid == False)
        self.starting_lives_edit.setText(f"{state.starting_lives}")

        self.continue_lives_edit.setDisabled(state.continue_lives_area_valid == False)
        self.continue_lives_edit.setText(f"{state.continue_lives}")

        self.invalid_rom_warning.setVisible(View.allAreasValid(state) == False)  

        if state.death_takes_lives_area_valid == False or state.death_takes_lives == None:
            self.death_takes_lives.setDisabled(True)
        else:
            self.death_takes_lives.setDisabled(False)
            self.death_takes_lives.setChecked(state.death_takes_lives)     

    def allAreasValid(state : State) -> bool:
        return state.starting_lives_area_valid and\
            state.continue_lives_area_valid and\
            state.death_takes_lives_area_valid

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

class PlayerLives():
    def __init__(self, parent):
        romInterface = RomInterface(ROM())        
        store = Store(romInterface.readState())               
        View(parent, store, romInterface)
