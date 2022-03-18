from xmlrpc.client import Boolean
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QBoxLayout, QLabel

from foundry.smb3parse.util.rom import Rom
from foundry.game.File import ROM
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from dataclasses import dataclass
import copy

@dataclass
class UIStrings:
    title = "Player Lives"
    starting_lives = "Starting Lives"
    continue_lives = "Continue Lives"
    reload = "Reload"
    cancel = "cancel"
    accept = "Accept"

@dataclass
class Addresses:
    starting_lives = 0x308E1
    continue_lives = 0x3D2D6

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

    def __loadStateFromRom(self) -> State:
        return State(   
                        self.rom.read(Addresses.starting_lives, 1)[0],
                        self.rom.read(Addresses.continue_lives, 1)[0]
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

class View(CustomDialog):
    store : Store

    def __init__(self, parent, store: Store):
        super(View, self).__init__(parent, title=UIStrings.title)
        self.store = store
        self.store.subscribe(self.render)
        self.store.dispatch(ACTION_LOAD)
        self.show()

    def render(self):
        state = self.store.getState()
        main_layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        text_layout = QBoxLayout(QBoxLayout.TopToBottom)
        text_layout.addWidget(QLabel(f"{UIStrings.starting_lives}: {state.starting_lives}", self))
        text_layout.addWidget(QLabel(f"{UIStrings.continue_lives}: {state.continue_lives}", self))
        main_layout.addLayout(text_layout)

class PlayerLives():
    def __init__(self, parent):
        View(parent, Store(ROM()))


