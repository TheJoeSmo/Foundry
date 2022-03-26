from foundry.smb3parse.util.rom import Rom
from foundry.gui.PlayerLives import Store, State, Action, ActionNames, Generator

default_starting_lives = 5
default_continue_lives = 4

def defaultStore() -> Store:
    return Store(State(default_starting_lives, True, default_continue_lives, True, True, True))

def test_subscribeOnInvalidAction():
    store = defaultStore()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action("", None))
    assert 0 == callback.called

def test_subscribeOnValidActionStateChange():
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

def test_warningStartLivesValid():
    store = defaultStore()
    assert True == store.getState().starting_lives_area_valid

def test_warningContinueLivesValid():
    store = defaultStore()
    assert True == store.getState().continue_lives_area_valid

def test_deathTakesLivesAction():
    store = defaultStore()
    store.dispatch(Action(ActionNames.death_takes_lives, False))
    assert False == store.getState().death_takes_lives
    store.dispatch(Action(ActionNames.death_takes_lives, True))
    assert True == store.getState().death_takes_lives

class CallbackTester:
    called = 0
    def function(self):
        self.called = self.called+1



