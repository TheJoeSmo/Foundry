from foundry.smb3parse.util.rom import Rom
from foundry.gui.PlayerLives import Addresses
from foundry.gui.PlayerLives import Store
from foundry.gui.PlayerLives import Action
from foundry.gui.PlayerLives import ActionNames

default_starting_lives = 5
default_continue_lives = 4

def defaultStore() -> Store:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(Addresses.starting_lives, [default_starting_lives])
    rom.write(Addresses.continue_lives, [default_continue_lives])
    return Store(rom)

def test_initialState():
    initialState(defaultStore())

def initialState(store : Store):
    assert default_starting_lives == store.getState().starting_lives
    assert default_continue_lives == store.getState().continue_lives

def test_subscribe():
    callback_called = False
    store = Store(Rom(bytearray([0] * 0x50000)))
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action("", None))
    assert 1 == callback.called

def test_startingLivesAction():
    startingLivesAction(defaultStore(), 1)

def startingLivesAction(store: Store, updated_starting_lives: int):
    store.dispatch(Action(ActionNames.starting_lives, updated_starting_lives))
    assert updated_starting_lives == store.getState().starting_lives

def test_continueLivesAction():
    updated_continue_lives = 2
    store = defaultStore()
    store.dispatch(Action(ActionNames.continue_lives, updated_continue_lives))
    assert updated_continue_lives == store.getState().continue_lives

def test_load():
    store = defaultStore()
    startingLivesAction(store, 1)
    store.dispatch(Action(ActionNames.load, None))
    initialState(store)

class CallbackTester:
    called = 0
    def function(self):
        self.called = self.called+1



