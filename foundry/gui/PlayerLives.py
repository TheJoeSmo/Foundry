from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QBoxLayout, QLabel

from foundry.smb3parse.util.rom import Rom
from foundry.game.File import ROM
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from dataclasses import dataclass

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
    state : State
    subscribers = []

    def __init__(self, rom: Rom):
        self.rom = rom
        self.state = Store.__defaultState(rom)

    def __defaultState(rom: Rom) -> State:
        return State(   
                        rom.read(Addresses.starting_lives, 1)[0],
                        rom.read(Addresses.continue_lives, 1)[0]
                    )

    def getState(self) -> State:
        return self.state

    def dispatch(self, action: Action):
        self.state = self.__reduce(self.state, action)
        for subscriber in self.subscribers:
            subscriber()

    def __reduce(self, state:State, action: Action) -> State:
        if state is None:
            state = Store.__defaultState(self.rom)

        if action.type == ActionNames.starting_lives:
            state.starting_lives = action.payload

        elif action.type == ActionNames.continue_lives:
            state.continue_lives = action.payload

        elif action.type == ActionNames.load:
            state = Store.__defaultState(self.rom)

        return state

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


