""" Tests for the Player Lives UI window """
from foundry.game.File import ROM
from foundry.gui.player_lives import Action, ActionNames, RomInterface, State, Store

DEFAULT_STARTING_LIVES = 5
DEFAULT_CONTINUE_LIVES = 4


def default_store() -> Store:
    """Provides a default store used by many tests."""
    return Store(State(DEFAULT_STARTING_LIVES, DEFAULT_CONTINUE_LIVES, True, True, True, True, True, True, True))


def test_subscribe_invalid_action():
    """An invalid action shouldn't cause a store callback"""
    store = default_store()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action("", None))
    assert 0 == callback.called


def test_subscribe_on_valid_action_state_change():
    """A valid action that causes a state change should cause a callback."""
    store = default_store()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action(ActionNames.STARTING_LIVES.value, 1))
    assert 1 == callback.called


def test_subscribe_on_valid_action_no_state_change():
    """A valid action that causes no state change should not cause a callback."""
    store = default_store()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action(ActionNames.STARTING_LIVES.value, DEFAULT_STARTING_LIVES))
    assert 0 == callback.called


def test_starting_lives_action():
    """Verify the starting lives action updates the state."""
    starting_lives_action(default_store(), 1)


def starting_lives_action(store: Store, updated_starting_lives):
    """Verify the starting lives action updates the state."""
    store.dispatch(Action(ActionNames.STARTING_LIVES.value, updated_starting_lives))
    assert updated_starting_lives == store.get_state().starting_lives


def test_starting_lives_action_invalid_type():
    """Passing in an invalid type to action payload doesn't update state"""
    store = default_store()
    store.dispatch(Action(ActionNames.STARTING_LIVES.value, "P"))
    assert DEFAULT_STARTING_LIVES == store.get_state().starting_lives


def test_starting_lives_action_invalid_values():
    """passing in to small/large numbers to starting live doesn't update state"""
    store = default_store()
    store.dispatch(Action(ActionNames.STARTING_LIVES.value, -1))
    assert DEFAULT_STARTING_LIVES == store.get_state().starting_lives
    store.dispatch(Action(ActionNames.STARTING_LIVES.value, 100))
    assert DEFAULT_STARTING_LIVES == store.get_state().starting_lives


def test_continue_lives_action_invalid_type():
    """Invalid payload type to continuous life action isn't accepted."""
    store = default_store()
    store.dispatch(Action(ActionNames.CONTINUE_LIVES.value, "P"))
    assert DEFAULT_CONTINUE_LIVES == store.get_state().continue_lives


def test_continue_lives_action_invalid_values():
    """Passing in too small/large a number doesn't update the state."""
    store = default_store()
    store.dispatch(Action(ActionNames.CONTINUE_LIVES.value, -1))
    assert DEFAULT_CONTINUE_LIVES == store.get_state().continue_lives
    store.dispatch(Action(ActionNames.CONTINUE_LIVES.value, 100))
    assert DEFAULT_CONTINUE_LIVES == store.get_state().continue_lives


def test_continue_lives_action():
    """valid action updates state"""
    updated_continue_lives = 2
    store = default_store()
    store.dispatch(Action(ActionNames.CONTINUE_LIVES.value, updated_continue_lives))
    assert updated_continue_lives == store.get_state().continue_lives


def test_death_takes_lives_action():
    """DEATH_TAKES_LIVES action results in state change."""
    store = default_store()
    store.dispatch(Action(ActionNames.DEATH_TAKES_LIVES.value, False))
    assert False is store.get_state().death_takes_lives
    store.dispatch(Action(ActionNames.DEATH_TAKES_LIVES.value, True))
    assert True is store.get_state().death_takes_lives


class CallbackTester:
    """Small class to verify a callback was called when required."""

    called = 0

    def function(self):
        """Test callback keeps track of number of times it has been called."""
        self.called = self.called + 1


def test_read_state_starting_lives_invalid():
    """Test that starting lines state is None when the ROM is invalid."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().starting_lives


def create_starting_lives_rom() -> ROM:
    """Create a test ROM that has valid starting lives section."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore

    rom[0x308E1 - 4] = bytes([0xCA, 0x10, 0xF8, 0xA9])
    rom[0x308E1] = bytes([0x04])
    rom[0x308E1 + 1] = bytes([0x8D, 0x36, 0x07, 0x8D])
    return rom


def test_read_state_starting_lives_valid():
    """On valid ROM, starting lives is read out correctly."""
    state = RomInterface(create_starting_lives_rom()).read_state()
    assert 0x04 == state.starting_lives


def test_write_state_starting_lives():
    """Writing to starting lives writes correctly to ROM"""
    rom_interface = RomInterface(create_starting_lives_rom())
    state = State(0xAA, DEFAULT_CONTINUE_LIVES, True, True, True, True, True, True, True)
    assert 0x04 == rom_interface.read_state().starting_lives
    rom_interface.write_state(state)
    assert 0xAA == rom_interface.read_state().starting_lives


def test_read_state_continue_lives_invalid():
    """Test when ROM invalid, continue lives read results in None."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().continue_lives


def create_continue_lives_rom() -> ROM:
    """Creates a test ROM with valid section for Continue Lives"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x3D2D6 - 4] = bytes([0x08, 0xD0, 0x65, 0xA9])
    rom[0x3D2D6] = bytes([0x04])
    rom[0x3D2D6 + 1] = bytes([0x9D, 0x36, 0x07, 0xA5])
    return rom


def test_read_state_continue_lives_valid():
    """ " Read of the continue lives is correct when valid."""
    state = RomInterface(create_continue_lives_rom()).read_state()
    assert 0x04 == state.continue_lives


def test_write_state_continue_lives():
    """Write to continue lives is correct when valid."""
    rom_interface = RomInterface(create_continue_lives_rom())
    state = State(0x00, 0xAA, True, True, True, True, True, True, True)
    assert 0x04 == rom_interface.read_state().continue_lives
    rom_interface.write_state(state)
    assert 0xAA == rom_interface.read_state().continue_lives


def test_read_state_death_takes_lives_invalid():
    """Read of death takes lives None when invalid"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().death_takes_lives


def create_death_takes_lives_rom(value):
    """Create valid test ROM for death takes lives"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x3D133 - 4] = bytes([0x8B, 0x07, 0xD0, 0x05])
    rom[0x3D133] = bytes(value)
    rom[0x3D133 + 3] = bytes([0x30, 0x0B, 0xA9, 0x80])
    return rom


def test_read_state_death_takes_lives_false():
    """Death takes lives returns False correctly on instruction match."""
    state = RomInterface(create_death_takes_lives_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.death_takes_lives


def test_read_state_death_takes_lives_true():
    """Death takes lives returns True correctly on instruction match"""
    state = RomInterface(create_death_takes_lives_rom([0xDE, 0x36, 0x07])).read_state()
    assert True is state.death_takes_lives


def test_read_state_100_coins_invalid():
    """100 coins is None when ROM is invalid."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().hundred_coins_1up


def create_100_coins_rom(value):
    """Create valid test ROM for 100 coins edit."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x350A7 - 4] = bytes([0x7D, 0xAE, 0x26, 0x07])
    rom[0x350A7] = bytes(value)
    rom[0x350A7 + 3] = bytes([0xA9, 0x40, 0x8D, 0xF2])
    return rom


def test_read_state_100_coins_false():
    """100 Coins reads False on instruction match."""
    state = RomInterface(create_100_coins_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.hundred_coins_1up


def test_read_state_100_coins_true():
    """100 Coins reads True on instruction match"""
    state = RomInterface(create_100_coins_rom([0xFE, 0x36, 0x07])).read_state()
    assert True is state.hundred_coins_1up


def test_write_state_100_coins():
    """Write to 100 coins is successful."""
    rom_interface = RomInterface(create_100_coins_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False is rom_interface.read_state().hundred_coins_1up
    rom_interface.write_state(state)
    assert True is rom_interface.read_state().hundred_coins_1up


def test_100_coins_action():
    """100 coins action updates the state correctly."""
    store = default_store()
    store.dispatch(Action(ActionNames.HUNDRED_COINS_1UP.value, False))
    assert False is store.get_state().hundred_coins_1up
    store.dispatch(Action(ActionNames.HUNDRED_COINS_1UP.value, True))
    assert True is store.get_state().hundred_coins_1up


def test_read_state_end_card_invalid():
    """End card read is None when ROM is invalid."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().end_card_1up


def create_end_card_rom(value):
    """Create valid test ROM for end card code edit"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x5D99 - 4] = bytes([0x60, 0xAE, 0x26, 0x07])
    rom[0x5D99] = bytes(value)
    rom[0x5D99 + 3] = bytes([0xEE, 0x40, 0x04, 0x60])
    return rom


def test_read_state_end_card_false():
    """Read of end card return False on instruction match."""
    state = RomInterface(create_end_card_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.end_card_1up


def test_read_state_end_card_true():
    """Read of end card returns True on instruction match."""
    state = RomInterface(create_end_card_rom([0xFE, 0x36, 0x07])).read_state()
    assert True is state.end_card_1up


def test_write_state_end_card():
    """Write to end card code edit is successful."""
    rom_interface = RomInterface(create_end_card_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False is rom_interface.read_state().end_card_1up
    rom_interface.write_state(state)
    assert True is rom_interface.read_state().end_card_1up


def test_end_card_action():
    """End card action updates state correctly."""
    store = default_store()
    store.dispatch(Action(ActionNames.END_CARD_1UP.value, False))
    assert False is store.get_state().end_card_1up
    store.dispatch(Action(ActionNames.END_CARD_1UP.value, True))
    assert True is store.get_state().end_card_1up


def test_read_state_mushroom_1up_invalid():
    """Mushroom 1up Read is None when ROM invalid"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().mushroom_1up


def create_mushroom_1up_rom(value):
    """Create valid test ROM for mushroom 1up"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0xEB0F - 4] = bytes([0x36, 0x07, 0x30, 0x03])
    rom[0xEB0F] = bytes(value)
    rom[0xEB0F + 3] = bytes([0xA6, 0xCD, 0xBD, 0xA3])
    return rom


def test_read_state_mushroom_1up_false():
    """Read of Mushroom 1up returns False on instruction match."""
    state = RomInterface(create_mushroom_1up_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.mushroom_1up


def test_read_state_mushroom_1up_true():
    """Read of Mushroom 1up returns True on instruction match."""
    state = RomInterface(create_mushroom_1up_rom([0xFE, 0x36, 0x07])).read_state()
    assert True is state.mushroom_1up


def test_write_state_mushroom_1up():
    """Writing to Mushroom 1up is successful."""
    rom_interface = RomInterface(create_mushroom_1up_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False is rom_interface.read_state().mushroom_1up
    rom_interface.write_state(state)
    assert True is rom_interface.read_state().mushroom_1up


def test_mushroom_action():
    """Mushroom 1up action updates state."""
    store = default_store()
    store.dispatch(Action(ActionNames.MUSHROOM_1UP.value, False))
    assert False is store.get_state().mushroom_1up
    store.dispatch(Action(ActionNames.MUSHROOM_1UP.value, True))
    assert True is store.get_state().mushroom_1up


def test_read_state_dice_game_invalid():
    """Read of Dice game is None when ROM is invalid"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().dice_game_1up


def create_dice_game_rom(value):
    """Create valid test ROM for Dice Game 1up."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x2CD78 - 4] = bytes([0x60, 0xAE, 0x26, 0x07])
    rom[0x2CD78] = bytes(value)
    rom[0x2CD78 + 3] = bytes([0xEE, 0x40, 0x04, 0x60])
    return rom


def test_read_state_dice_game_false():
    """Dice game returns False on instruction match."""
    state = RomInterface(create_dice_game_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.dice_game_1up


def test_read_state_dice_game_true():
    """Dice game returns True on instruction match."""
    state = RomInterface(create_dice_game_rom([0xFE, 0x36, 0x07])).read_state()
    assert True is state.dice_game_1up


def test_write_state_dice_game():
    """Write to dice game successful."""
    rom_interface = RomInterface(create_dice_game_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False is rom_interface.read_state().dice_game_1up
    rom_interface.write_state(state)
    assert True is rom_interface.read_state().dice_game_1up


def test_dice_game_action():
    """Dice game action updates state."""
    store = default_store()
    store.dispatch(Action(ActionNames.DICE_GAME_1UP.value, False))
    assert False is store.get_state().dice_game_1up
    store.dispatch(Action(ActionNames.DICE_GAME_1UP.value, True))
    assert True is store.get_state().dice_game_1up


def test_read_state_roulette_game_invalid():
    """Roulette game read returns None when ROM is invalid."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().roulette_1up


def create_roulette_game_rom(value):
    """Create a test ROM for roulette code edit."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x2D2BE - 4] = bytes([0x36, 0x07, 0x30, 0x03])
    rom[0x2D2BE] = bytes(value)
    rom[0x2D2BE + 3] = bytes([0x4C, 0xD2, 0xD2, 0xCE])
    return rom


def test_read_state_roulette_game_false():
    """Read of Roulette game returns False on instruction match."""
    state = RomInterface(create_roulette_game_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.roulette_1up


def test_read_state_roulette_game_true():
    """Read of Roulette game returns True on instruction match."""
    state = RomInterface(create_roulette_game_rom([0xFE, 0x36, 0x07])).read_state()
    assert True is state.roulette_1up


def test_write_state_roulette_game():
    """Write of Roulette game successful."""
    rom_interface = RomInterface(create_roulette_game_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False is rom_interface.read_state().roulette_1up
    rom_interface.write_state(state)
    assert True is rom_interface.read_state().roulette_1up


def test_roulette_game_action():
    """Roulette action updates state."""
    store = default_store()
    store.dispatch(Action(ActionNames.ROULETTE_1UP.value, False))
    assert False is store.get_state().roulette_1up
    store.dispatch(Action(ActionNames.ROULETTE_1UP.value, True))
    assert True is store.get_state().roulette_1up


def test_read_state_card_game_invalid():
    """Card game read returns None on invalid ROM"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    assert None is RomInterface(rom).read_state().card_game_1up


def create_card_game_rom(value):
    """Create a valid ROM for card game edit."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x2DD50 - 4] = bytes([0x0D, 0xAE, 0x26, 0x07])
    rom[0x2DD50] = bytes(value)
    rom[0x2DD50 + 3] = bytes([0xA9, 0x40, 0x8D, 0xF2])
    return rom


def test_read_state_card_game_false():
    """Read the card game returns False on instruction match."""
    state = RomInterface(create_card_game_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False is state.card_game_1up


def test_read_state_card_game_true():
    """Read of card game returns True on instruction match."""
    state = RomInterface(create_card_game_rom([0xFE, 0x36, 0x07])).read_state()
    assert True is state.card_game_1up


def test_write_state_card_game():
    """Write to card game successful."""
    rom_interface = RomInterface(create_card_game_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False is rom_interface.read_state().card_game_1up
    rom_interface.write_state(state)
    assert True is rom_interface.read_state().card_game_1up


def test_card_game_action():
    """Card game action updates state."""
    store = default_store()
    store.dispatch(Action(ActionNames.CARD_GAME_1UP.value, False))
    assert False is store.get_state().card_game_1up
    store.dispatch(Action(ActionNames.CARD_GAME_1UP.value, True))
    assert True is store.get_state().card_game_1up
