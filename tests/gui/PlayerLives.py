from foundry.smb3parse.util.rom import Rom
from foundry.gui.PlayerLives import CodeEditAreas, Store, Action, ActionNames, Generator

default_starting_lives = 5
default_continue_lives = 4

def defaultStore() -> Store:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(CodeEditAreas.starting_lives.address, [default_starting_lives])
    rom.write(CodeEditAreas.continue_lives.address, [default_continue_lives])
    return Store(rom)

def test_verifyDefaultState():
    verifyDefaultState(defaultStore())

def verifyDefaultState(store : Store):
    assert default_starting_lives == store.getState().starting_lives
    assert default_continue_lives == store.getState().continue_lives

def test_subscribeOnInvalidAction():
    callback_called = False
    store = defaultStore()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action("", None))
    assert 0 == callback.called

def test_subscribeOnValidActionStateChange():
    callback_called = False
    store = defaultStore()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action(ActionNames.starting_lives, 1))
    assert 1 == callback.called

def test_subscribeOnValidActionNoStateChange():
    callback_called = False
    store = defaultStore()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action(ActionNames.starting_lives, default_starting_lives))
    assert 0 == callback.called

def test_startingLivesAction():
    startingLivesAction(defaultStore(), 1)

def startingLivesAction(store: Store, updated_starting_lives):
    store.dispatch(Action(ActionNames.starting_lives, updated_starting_lives))
    assert updated_starting_lives == store.getState().starting_lives

def test_startingLivesActionInvalidType():
    store = defaultStore()
    store.dispatch(Action(ActionNames.starting_lives, "P"))
    assert default_starting_lives == store.getState().starting_lives

def test_startingLivesActionInvalidValues():
    store = defaultStore()
    store.dispatch(Action(ActionNames.starting_lives, -1))
    assert default_starting_lives == store.getState().starting_lives
    store.dispatch(Action(ActionNames.starting_lives, 100))
    assert default_starting_lives == store.getState().starting_lives

def test_continueLivesActionInvalidType():
    store = defaultStore()
    store.dispatch(Action(ActionNames.continue_lives, "P"))
    assert default_continue_lives == store.getState().continue_lives

def test_continueLivesActionInvalidValues():
    store = defaultStore()
    store.dispatch(Action(ActionNames.continue_lives, -1))
    assert default_continue_lives == store.getState().continue_lives
    store.dispatch(Action(ActionNames.continue_lives, 100))
    assert default_continue_lives == store.getState().continue_lives

def test_continueLivesAction():
    updated_continue_lives = 2
    store = defaultStore()
    store.dispatch(Action(ActionNames.continue_lives, updated_continue_lives))
    assert updated_continue_lives == store.getState().continue_lives

def test_load():
    store = defaultStore()
    startingLivesAction(store, 1)
    store.dispatch(Action(ActionNames.load, None))
    verifyDefaultState(store)

def test_generator():
    store = defaultStore()
    rom = Rom(bytearray([0] * 0x50000))
    generator = Generator(store, rom)
    generator.render()
    assert default_starting_lives == rom.read(CodeEditAreas.starting_lives.address, 1)[0]
    assert default_continue_lives == rom.read(CodeEditAreas.continue_lives.address, 1)[0]

class CallbackTester:
    called = 0
    def function(self):
        self.called = self.called+1



