from foundry.smb3parse.util.rom import Rom
from foundry.gui.player_lives import Store, State, Action, ActionNames, RomInterface

default_starting_lives = 5
default_continue_lives = 4

def default_store() -> Store:
    return Store(State(default_starting_lives, default_continue_lives, True, True, True, True, True, True, True))

def test_subscribe_invalid_action():
    store = default_store()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action("", None))
    assert 0 == callback.called

def test_subscribe_on_valid_action_state_change():
    store = default_store()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action(ActionNames.starting_lives, 1))
    assert 1 == callback.called

def test_subscribe_on_valid_action_no_state_change():
    store = default_store()
    callback = CallbackTester()
    store.subscribe(callback.function)
    assert 0 == callback.called

    store.dispatch(Action(ActionNames.starting_lives, default_starting_lives))
    assert 0 == callback.called

def test_starting_lives_action():
    startingLivesAction(default_store(), 1)

def startingLivesAction(store: Store, updated_starting_lives):
    store.dispatch(Action(ActionNames.starting_lives, updated_starting_lives))
    assert updated_starting_lives == store.get_state().starting_lives

def test_starting_lives_action_invalid_type():
    store = default_store()
    store.dispatch(Action(ActionNames.starting_lives, "P"))
    assert default_starting_lives == store.get_state().starting_lives

def test_starting_lives_action_invalid_values():
    store = default_store()
    store.dispatch(Action(ActionNames.starting_lives, -1))
    assert default_starting_lives == store.get_state().starting_lives
    store.dispatch(Action(ActionNames.starting_lives, 100))
    assert default_starting_lives == store.get_state().starting_lives

def test_continue_lives_action_invalid_type():
    store = default_store()
    store.dispatch(Action(ActionNames.continue_lives, "P"))
    assert default_continue_lives == store.get_state().continue_lives

def test_continue_lives_action_invalid_values():
    store = default_store()
    store.dispatch(Action(ActionNames.continue_lives, -1))
    assert default_continue_lives == store.get_state().continue_lives
    store.dispatch(Action(ActionNames.continue_lives, 100))
    assert default_continue_lives == store.get_state().continue_lives

def test_continue_lives_action():
    updated_continue_lives = 2
    store = default_store()
    store.dispatch(Action(ActionNames.continue_lives, updated_continue_lives))
    assert updated_continue_lives == store.get_state().continue_lives

def test_warning_start_lives_valid():
    store = default_store()
    assert store.get_state().starting_lives

def test_warning_continue_lives_valid():
    store = default_store()
    assert store.get_state().continue_lives

def test_death_takes_lives_action():
    store = default_store()
    store.dispatch(Action(ActionNames.death_takes_lives, False))
    assert False == store.get_state().death_takes_lives
    store.dispatch(Action(ActionNames.death_takes_lives, True))
    assert True == store.get_state().death_takes_lives

class CallbackTester:
    called = 0
    def function(self):
        self.called = self.called+1

def test_read_state_starting_lives_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().starting_lives

def create_starting_lives_rom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    
    rom.write(0x308E1-4, [0xCA, 0x10, 0xF8, 0xA9])
    rom.write(0x308E1, [0x04])
    rom.write(0x308E1+1, [0x8D, 0x36, 0x07, 0x8D])
    return rom

def test_read_state_starting_lives_valid():
    state = RomInterface(create_starting_lives_rom()).read_state()
    assert 0x04 == state.starting_lives

def test_write_state_starting_lives():
    rom_interface = RomInterface(create_starting_lives_rom())
    state = State(0xAA, default_continue_lives, True, True, True, True, True, True, True)
    assert 0x04 == rom_interface.read_state().starting_lives
    rom_interface.write_state(state)
    assert 0xAA == rom_interface.read_state().starting_lives

def test_read_state_continue_lives_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().continue_lives

def create_continue_lives_rom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))   
    rom.write(0x3D2D6-4, [0x08, 0xD0, 0x65, 0xA9])
    rom.write(0x3D2D6, [0x04])
    rom.write(0x3D2D6+1, [0x9D, 0x36, 0x07, 0xA5])
    return rom

def test_read_state_continue_lives_valid():
    state = RomInterface(create_continue_lives_rom()).read_state()
    assert 0x04 == state.continue_lives

def test_write_state_continue_lives():
    rom_interface = RomInterface(create_continue_lives_rom())
    state = State(0x00, 0xAA, True, True, True, True, True, True, True)
    assert 0x04 == rom_interface.read_state().continue_lives
    rom_interface.write_state(state)
    assert 0xAA == rom_interface.read_state().continue_lives

def test_read_state_death_takes_lives_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().death_takes_lives

def create_death_takes_lives_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x3D133-4, [0x8B, 0x07, 0xD0, 0x05])
    rom.write(0x3D133, value)
    rom.write(0x3D133+3, [0x30, 0x0b, 0xA9, 0x80])
    return rom

def test_read_state_death_takes_lives_false():
    state = RomInterface(create_death_takes_lives_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.death_takes_lives

def test_read_state_death_takes_lives_true():
    state = RomInterface(create_death_takes_lives_rom([0xDE, 0x36, 0x07])).read_state()
    assert True == state.death_takes_lives

""" 100 coins """

def test_read_state_100_coins_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().hundred_coins_1up

def create_100_coins_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x350A7-4, [0x7d, 0xae, 0x26, 0x07])
    rom.write(0x350A7, value)
    rom.write(0x350A7+3, [0xa9, 0x40, 0x8d, 0xf2])
    return rom

def test_read_state_100_coins_false():
    state = RomInterface(create_100_coins_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.hundred_coins_1up

def test_read_state_100_coins_true():
    state = RomInterface(create_100_coins_rom([0xfe, 0x36, 0x07])).read_state()
    assert True == state.hundred_coins_1up

def test_write_state_100_coins():
    rom_interface = RomInterface(create_100_coins_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False == rom_interface.read_state().hundred_coins_1up
    rom_interface.write_state(state)
    assert True == rom_interface.read_state().hundred_coins_1up

def test_100CoinsAction():
    store = default_store()
    store.dispatch(Action(ActionNames.hundred_coins_1up, False))
    assert False == store.get_state().hundred_coins_1up
    store.dispatch(Action(ActionNames.hundred_coins_1up, True))
    assert True == store.get_state().hundred_coins_1up

""" End Card """

def test_read_state_end_card_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().end_card_1up

def create_end_card_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x5d99-4, [0x60, 0xae, 0x26, 0x07])
    rom.write(0x5d99, value)
    rom.write(0x5d99+3, [0xee, 0x40, 0x04, 0x60])
    return rom

def test_read_state_end_card_false():
    state = RomInterface(create_end_card_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.end_card_1up

def test_read_state_end_card_true():
    state = RomInterface(create_end_card_rom([0xfe, 0x36, 0x07])).read_state()
    assert True == state.end_card_1up

def test_write_state_end_card():
    rom_interface = RomInterface(create_end_card_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False == rom_interface.read_state().end_card_1up
    rom_interface.write_state(state)
    assert True == rom_interface.read_state().end_card_1up

def test_end_card_action():
    store = default_store()
    store.dispatch(Action(ActionNames.end_card_1up, False))
    assert False == store.get_state().end_card_1up
    store.dispatch(Action(ActionNames.end_card_1up, True))
    assert True == store.get_state().end_card_1up

""" Mushroom 1up"""

def test_read_state_mushroom_1up_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().mushroom_1up

def create_mushroom_1up_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0xeb0f-4, [0x36, 0x07, 0x30, 0x03])
    rom.write(0xeb0f, value)
    rom.write(0xeb0f+3, [0xa6, 0xcd, 0xbd, 0xa3])
    return rom

def test_read_stateMushroom1upFalse():
    state = RomInterface(create_mushroom_1up_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.mushroom_1up

def test_read_stateMushroom1upTrue():
    state = RomInterface(create_mushroom_1up_rom([0xfe, 0x36, 0x07])).read_state()
    assert True == state.mushroom_1up

def test_write_state_mushroom_1up():
    rom_interface = RomInterface(create_mushroom_1up_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False == rom_interface.read_state().mushroom_1up
    rom_interface.write_state(state)
    assert True == rom_interface.read_state().mushroom_1up

def test_mushroom_action():
    store = default_store()
    store.dispatch(Action(ActionNames.mushroom_1up, False))
    assert False == store.get_state().mushroom_1up
    store.dispatch(Action(ActionNames.mushroom_1up, True))
    assert True == store.get_state().mushroom_1up

""" Dice game """

def test_read_state_dice_game_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().dice_game_1up

def create_dice_game_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x2cd78-4, [0x60, 0xae, 0x26, 0x07])
    rom.write(0x2cd78, value)
    rom.write(0x2cd78+3, [0xee, 0x40, 0x04, 0x60])
    return rom

def test_read_state_dice_game_false():
    state = RomInterface(create_dice_game_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.dice_game_1up

def test_read_state_dice_game_true():
    state = RomInterface(create_dice_game_rom([0xfe, 0x36, 0x07])).read_state()
    assert True == state.dice_game_1up

def test_write_state_dice_game():
    rom_interface = RomInterface(create_dice_game_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False == rom_interface.read_state().dice_game_1up
    rom_interface.write_state(state)
    assert True == rom_interface.read_state().dice_game_1up

def test_dice_game_action():
    store = default_store()
    store.dispatch(Action(ActionNames.dice_game_1up, False))
    assert False == store.get_state().dice_game_1up
    store.dispatch(Action(ActionNames.dice_game_1up, True))
    assert True == store.get_state().dice_game_1up

""" Roulette game """

def test_read_state_roulette_game_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().roulette_1up

def create_roulette_game_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x2d2be-4, [0x36, 0x07, 0x30, 0x03])
    rom.write(0x2d2be, value)
    rom.write(0x2d2be+3, [0x4c, 0xd2, 0xd2, 0xce])
    return rom

def test_read_state_roulette_game_false():
    state = RomInterface(create_roulette_game_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.roulette_1up

def test_read_state_roulette_game_true():
    state = RomInterface(create_roulette_game_rom([0xfe, 0x36, 0x07])).read_state()
    assert True == state.roulette_1up

def test_write_state_roulette_game():
    rom_interface = RomInterface(create_roulette_game_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False == rom_interface.read_state().roulette_1up
    rom_interface.write_state(state)
    assert True == rom_interface.read_state().roulette_1up

def test_roulette_game_action():
    store = default_store()
    store.dispatch(Action(ActionNames.roulette_1up, False))
    assert False == store.get_state().roulette_1up
    store.dispatch(Action(ActionNames.roulette_1up, True))
    assert True == store.get_state().roulette_1up

""" Card game """

def test_read_state_card_game_invalid():
    rom = Rom(bytearray([0] * 0x50000))
    assert None == RomInterface(rom).read_state().card_game_1up

def create_card_game_rom(value):
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x2dd50-4, [0x0d, 0xae, 0x26, 0x07])
    rom.write(0x2dd50, value)
    rom.write(0x2dd50+3, [0xa9, 0x40, 0x8d, 0xf2])
    return rom

def test_read_state_card_game_false():
    state = RomInterface(create_card_game_rom([0xEA, 0xEA, 0xEA])).read_state()
    assert False == state.card_game_1up

def test_read_state_card_game_true():
    state = RomInterface(create_card_game_rom([0xfe, 0x36, 0x07])).read_state()
    assert True == state.card_game_1up

def test_write_state_card_game():
    rom_interface = RomInterface(create_card_game_rom([0xEA, 0xEA, 0xEA]))
    state = State(0x00, 0x00, True, True, True, True, True, True, True)
    assert False == rom_interface.read_state().card_game_1up
    rom_interface.write_state(state)
    assert True == rom_interface.read_state().card_game_1up

def test_card_game_action():
    store = default_store()
    store.dispatch(Action(ActionNames.card_game_1up, False))
    assert False == store.get_state().card_game_1up
    store.dispatch(Action(ActionNames.card_game_1up, True))
    assert True == store.get_state().card_game_1up