""" Tests for the Orb UI window """
from foundry.gui.orb import Store, State, Actions, Action, RomInterface
from foundry.smb3parse.util.rom import Rom


def test_store_initial_state_is_state():
    state1 = State(True, True, True)
    store1 = Store(state1)
    assert state1 == store1.get_state()

    state2 = State(False, True, True)
    store2 = Store(state2)
    assert state2 == store2.get_state()

    state3 = State(True, False, False)
    store3 = Store(state3)
    assert state3 == store3.get_state()


def test_store_reduce_none():
    state = State(True, True, True)
    store = Store(state)
    assert state == store._reduce(None, None)


def test_store_move_touch_to_timer():
    state = State(True, True, True)
    store = Store(state)
    store.dispatch(Action(Actions.MOVE_TOUCH_TO_TIMER, False))
    assert False is store.get_state().move_touch_to_timer
    store.dispatch(Action(Actions.MOVE_TOUCH_TO_TIMER, True))
    assert True is store.get_state().move_touch_to_timer


def test_store_move_timer_to_exit():
    state = State(True, True, True)
    store = Store(state)
    store.dispatch(Action(Actions.MOVE_TIMER_TO_EXIT, False))
    assert False is store.get_state().move_timer_to_exit
    store.dispatch(Action(Actions.MOVE_TIMER_TO_EXIT, True))
    assert True is store.get_state().move_timer_to_exit


def test_store_touch_game_timer_stops():
    state = State(True, True, True)
    store = Store(state)
    store.dispatch(Action(Actions.TOUCH_GAME_TIMER_STOPS, False))
    assert False is store.get_state().touch_game_timer_stops
    store.dispatch(Action(Actions.TOUCH_GAME_TIMER_STOPS, True))
    assert True is store.get_state().touch_game_timer_stops


def create_move_touch_to_timer_rom(data: bytearray) -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x6913 - 4, bytearray([0xb5, 0x9a, 0xf0, 0x0e]))
    rom.write(0x6913, data)
    rom.write(0x6913 + len(data), bytearray([0x20, 0x12, 0xc4, 0xd0]))
    return rom


def test_rom_interface_read_state_move_touch_to_timer_false():
    rom = create_move_touch_to_timer_rom(bytearray([0x8d, 0xf4, 0x7c]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_touch_to_timer


def test_rom_interface_read_state_move_touch_to_timer_true():
    rom = create_move_touch_to_timer_rom(bytearray([0xEA, 0xEA, 0xEA]))
    rom_interface = RomInterface(rom)
    assert True is rom_interface.read_state().move_touch_to_timer


def test_rom_interface_read_state_move_touch_to_timer_invalid():
    rom = create_move_touch_to_timer_rom(bytearray([0x11, 0x22, 0x33]))
    rom_interface = RomInterface(rom)
    assert None is rom_interface.read_state().move_touch_to_timer


def test_rom_interface_write_state_move_touch_to_timer_false():
    rom = create_move_touch_to_timer_rom(bytearray([0xEA, 0xEA, 0xEA]))
    rom_interface = RomInterface(rom)
    assert True is rom_interface.read_state().move_touch_to_timer
    rom_interface.write_state(State(False, True, True))
    assert False is rom_interface.read_state().move_touch_to_timer


def test_rom_interface_write_state_move_touch_to_timer_true():
    rom = create_move_touch_to_timer_rom(bytearray([0x8d, 0xf4, 0x7c]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_touch_to_timer
    rom_interface.write_state(State(True, False, False))
    assert True is rom_interface.read_state().move_touch_to_timer


def test_rom_interface_write_state_move_touch_to_timer_invalid():
    rom = create_move_touch_to_timer_rom(bytearray([0x8d, 0xf4, 0x7c]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_touch_to_timer
    rom_interface.write_state(State(None, False, False))
    assert False is rom_interface.read_state().move_touch_to_timer


def create_move_timer_to_exit_rom(data: bytearray) -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x68FD - 4, bytearray([0x18, 0x05, 0xF0, 0x12]))
    rom.write(0x68FD, data)
    rom.write(0x68FD + len(data), bytearray([0x88, 0xd0, 0x0b, 0x8c]))
    return rom


def test_rom_interface_read_state_move_timer_to_exit_false():
    rom = create_move_timer_to_exit_rom(bytearray([0x8c, 0xf4, 0x7c]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_timer_to_exit


def test_rom_interface_read_state_move_timer_to_exit_true():
    rom = create_move_timer_to_exit_rom(bytearray([0xEA, 0xEA, 0xEA]))
    rom_interface = RomInterface(rom)
    assert True is rom_interface.read_state().move_timer_to_exit


def test_rom_interface_read_state_move_timer_to_exit_invalid():
    rom = create_move_timer_to_exit_rom(bytearray([0x11, 0x22, 0x33]))
    rom_interface = RomInterface(rom)
    assert None is rom_interface.read_state().move_timer_to_exit


def test_rom_interface_write_state_move_timer_to_exit_false():
    rom = create_move_timer_to_exit_rom(bytearray([0xEA, 0xEA, 0xEA]))
    rom_interface = RomInterface(rom)
    assert True is rom_interface.read_state().move_timer_to_exit
    rom_interface.write_state(State(True, False, True))
    assert False is rom_interface.read_state().move_timer_to_exit


def test_rom_interface_write_state_move_timer_to_exit_true():
    rom = create_move_timer_to_exit_rom(bytearray([0x8c, 0xf4, 0x7c]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_timer_to_exit
    rom_interface.write_state(State(False, True, False))
    assert True is rom_interface.read_state().move_timer_to_exit


def test_rom_interface_write_state_move_timer_to_exit_invalid():
    rom = create_move_timer_to_exit_rom(bytearray([0x8c, 0xf4, 0x7c]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_timer_to_exit
    rom_interface.write_state(State(False, None, False))
    assert False is rom_interface.read_state().move_timer_to_exit


def create_stop_timer_rom(jump_table: bytearray, stop_timer: bytearray) -> Rom:
    rom = Rom(bytearray([0] * 0x50000))

    rom.write(0x6014 - 4, bytearray([0x46, 0xBF, 0xFF, 0xA9]))
    rom.write(0x6014, jump_table)
    rom.write(0x6014 + len(jump_table), bytearray([0x88, 0xd0, 0x0b, 0x8c]))

    rom.write(0x7FCF - 4, bytearray([0x07, 0x4C, 0xE7, 0xD5]))
    rom.write(0x7FCF, stop_timer)
    return rom


def test_rom_interface_read_state_stop_timer_false():
    rom = create_stop_timer_rom(bytearray([0x5B, 0xA9]), bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().touch_game_timer_stops


def test_rom_interface_read_state_stop_timer_true():
    rom = create_stop_timer_rom(bytearray([0xBF, 0xBF]), bytearray([0xA9, 0x01, 0x8D, 0xF3, 0x05, 0x60]))
    rom_interface = RomInterface(rom)
    assert True is rom_interface.read_state().touch_game_timer_stops


def test_rom_interface_read_state_stop_timer_invalid():
    rom = create_stop_timer_rom(bytearray([0x5B, 0xA9]), bytearray([0xA9, 0x01, 0x8D, 0xF3, 0x05, 0x60]))
    rom_interface = RomInterface(rom)
    assert None is rom_interface.read_state().touch_game_timer_stops

    rom = create_stop_timer_rom(bytearray([0xBF, 0xBF]), bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]))
    rom_interface = RomInterface(rom)
    assert None is rom_interface.read_state().touch_game_timer_stops


def test_rom_interface_write_state_stop_timer_false():
    rom = create_stop_timer_rom(bytearray([0xBF, 0xBF]), bytearray([0xA9, 0x01, 0x8D, 0xF3, 0x05, 0x60]))
    rom_interface = RomInterface(rom)
    assert True is rom_interface.read_state().touch_game_timer_stops
    rom_interface.write_state(State(True, True, False))
    assert False is rom_interface.read_state().touch_game_timer_stops


def test_rom_interface_write_state_stop_timer_true():
    rom = create_stop_timer_rom(bytearray([0x5B, 0xA9]), bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().touch_game_timer_stops
    rom_interface.write_state(State(False, False, True))
    assert True is rom_interface.read_state().touch_game_timer_stops


def test_rom_interface_write_state_stop_timer_invalid():
    rom = create_stop_timer_rom(bytearray([0x5B, 0xA9]), bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().touch_game_timer_stops
    rom_interface.write_state(State(False, False, None))
    assert False is rom_interface.read_state().touch_game_timer_stops
