from xmlrpc.client import Boolean
from PySide6.QtGui import QPixmap, Qt, QIntValidator
from PySide6.QtWidgets import QBoxLayout, QLabel, QDialogButtonBox, QLineEdit

from foundry.smb3parse.util.rom import Rom
from foundry.game.File import ROM
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from foundry.smb3parse.util.code_edit_area import CodeEditArea
from dataclasses import dataclass
import copy

@dataclass
class UIStrings:
    title = "Player Lives"
    starting_lives = "Starting Lives"
    continue_lives = "Continue Lives"

@dataclass
class CodeEditAreas:
    starting_lives = CodeEditArea(0x308E1, 1, bytearray([]), bytearray([]))
    continue_lives = CodeEditArea(0x3D2D6, 1, bytearray([]), bytearray([]))

@dataclass
class Action:
    type: str
    payload: any

@dataclass
class ActionNames:
    load = "[PlayerLives] Load"
    starting_lives = "[PlayerLives] StartingLives"
    continue_lives = "[PlayerLives] ContinueLives"

ACTION_LOAD = Action(ActionNames.load, None)

@dataclass
class State:
    starting_lives: int
    continue_lives: int

class Store():
    rom : Rom
    state : State = None
    subscribers = []

    def __init__(self, rom: Rom):
        self.rom = rom
        self.state = self.__loadStateFromRom()

    def __loadStateFromRom(self) -> State:
        return State(   
                        self.rom.read(CodeEditAreas.starting_lives.address, 1)[0],
                        self.rom.read(CodeEditAreas.continue_lives.address, 1)[0]
                    )

    def getState(self) -> State:
        return self.state

    def dispatch(self, action: Action):
        oldState = copy.deepcopy(self.state)
        self.state = self.__reduce(copy.deepcopy(self.state), action)

        if self.state != oldState:
            self.__notifySubscribers()

    def __notifySubscribers(self):
        for subscriber in self.subscribers:
            subscriber()

    def __reduce(self, state:State, action: Action) -> State:

        if state is None:
            state = self.__loadStateFromRom()

        if action.type == ActionNames.starting_lives:
            if(Store.__isBoundedInteger(action.payload, 0, 99)):
                state.starting_lives = action.payload

        elif action.type == ActionNames.continue_lives:
            if(Store.__isBoundedInteger(action.payload, 0, 99)):
                state.continue_lives = action.payload

        elif action.type == ActionNames.load:
            state = self.__loadStateFromRom()

        return state

    def __isBoundedInteger(input, lower_limit: int, upper_limit: int) -> Boolean:
        if isinstance(input, int) == False: return False
        return (input >= lower_limit) & (input <= upper_limit)

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

class Generator():
    store : Store
    rom : Rom

    def __init__(self, store: Store, rom : Rom):
        self.store = store
        self.rom = rom

    def render(self):
        state = self.store.getState()
        self.rom.write(CodeEditAreas.starting_lives.address, [state.starting_lives])
        self.rom.write(CodeEditAreas.continue_lives.address, [state.continue_lives])
        self.rom.save_to

class View(CustomDialog):
    store : Store
    generator : Generator

    starting_lives_edit : QLineEdit
    continue_lives_edit : QLineEdit

    button_box : QDialogButtonBox

    def __init__(self, parent, store : Store, generator : Generator):
        super(View, self).__init__(parent, title=UIStrings.title)
        self.generator = generator
        self.store = store

        main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)

        starting_lives_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.starting_lives_edit = QLineEdit(self)
        self.starting_lives_edit.setValidator(QIntValidator(0, 99, self))
        self.starting_lives_edit.textEdited.connect(self.__on_starting_lives)
        starting_lives_layout.addWidget(QLabel(f"{UIStrings.starting_lives} (0-99):", self))
        starting_lives_layout.addWidget(self.starting_lives_edit)

        continue_lives_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.continue_lives_edit = QLineEdit(self)
        self.continue_lives_edit.setValidator(QIntValidator(0, 99, self))
        self.continue_lives_edit.textEdited.connect(self.__on_continue_lives)
        continue_lives_layout.addWidget(QLabel(f"{UIStrings.continue_lives} (0-99):", self))
        continue_lives_layout.addWidget(self.continue_lives_edit)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.Ok).clicked.connect(self.__on_ok)
        self.button_box.addButton(QDialogButtonBox.Cancel).clicked.connect(self.__on_cancel)

        main_layout.addLayout(starting_lives_layout)
        main_layout.addLayout(continue_lives_layout)
        main_layout.addWidget(HorizontalLine())
        main_layout.addWidget(self.button_box, alignment=Qt.AlignRight)

        self.store.subscribe(self.render)
        self.render()
        self.show()

    def render(self):
        state = self.store.getState()
        self.starting_lives_edit.setText(f"{state.starting_lives}")
        self.continue_lives_edit.setText(f"{state.continue_lives}")

    def __on_ok(self):
        self.generator.render()
        self.done(QDialogButtonBox.Apply)

    def __on_cancel(self):
        self.done(QDialogButtonBox.Cancel)

    def __on_starting_lives(self, text : str):
        self.store.dispatch(Action(ActionNames.starting_lives, int(text)))

    def __on_continue_lives(self, text : str):
        self.store.dispatch(Action(ActionNames.continue_lives, int(text)))
    

class PlayerLives():
    def __init__(self, parent):
        rom = ROM()
        store = Store(rom)
        View(parent, store, Generator(store, rom))


