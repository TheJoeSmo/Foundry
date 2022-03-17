from foundry.smb3parse.util.rom import Rom
from foundry.gui.PlayerLives import Addresses
from foundry.gui.PlayerLives import Store
from foundry.gui.PlayerLives import Action

def test_initialState():
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(Addresses.starting_lives, [5])
    assert 5 == Store(rom).getState().starting_lives

def test_subscribe():
    callback_called = False
    store = Store(Rom(bytearray([0] * 0x50000)))
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action("", None))
    assert 1 == callback.called

class CallbackTester:
    called = 0
    def function(self):
        self.called = self.called+1



