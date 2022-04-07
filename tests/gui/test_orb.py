""" Tests for the Orb UI window """
from foundry.gui.orb import Action, Actions, RomInterface, State, Store
from foundry.smb3parse.util.rom import Rom


def test_store_initial_state_is_state_all_true():
    state = State(True, True, True)
    store = Store(state)
    assert state == store.get_state()


def test_store_initial_state_is_state_all_false():
    state = State(False, False, False)
    store = Store(state)
    assert state == store.get_state()


def test_store_reduce_none():
    state = State(True, True, True)
    store = Store(state)
    assert state == store._reduce(None, None)


def test_store_move_touch_to_timer():
    state = State(True, True, True)
    store = Store(state)
    store.dispatch(Action(Actions.MOVE_TOUCH_TO_TIMER.value, False))
    assert False is store.get_state().move_touch_to_timer
    store.dispatch(Action(Actions.MOVE_TOUCH_TO_TIMER.value, True))
    assert True is store.get_state().move_touch_to_timer


def test_store_move_timer_to_exit():
    state = State(True, True, True)
    store = Store(state)
    store.dispatch(Action(Actions.MOVE_TIMER_TO_EXIT.value, False))
    assert False is store.get_state().move_timer_to_exit
    store.dispatch(Action(Actions.MOVE_TIMER_TO_EXIT.value, True))
    assert True is store.get_state().move_timer_to_exit


def test_store_touch_game_timer_stops():
    state = State(True, True, True)
    store = Store(state)
    store.dispatch(Action(Actions.TOUCH_GAME_TIMER_STOPS.value, False))
    assert False is store.get_state().touch_game_timer_stops
    store.dispatch(Action(Actions.TOUCH_GAME_TIMER_STOPS.value, True))
    assert True is store.get_state().touch_game_timer_stops


def create_move_touch_to_timer_rom(data: bytearray) -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x6913 - 4, bytearray([0xB5, 0x9A, 0xF0, 0x0E]))
    rom.write(0x6913, data)
    rom.write(0x6913 + len(data), bytearray([0x20, 0x12, 0xC4, 0xD0]))
    return rom


def test_rom_interface_read_state_move_touch_to_timer_false():
    rom = create_move_touch_to_timer_rom(bytearray([0x8D, 0xF4, 0x7C]))
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
    rom = create_move_touch_to_timer_rom(bytearray([0x8D, 0xF4, 0x7C]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_touch_to_timer
    rom_interface.write_state(State(True, False, False))
    assert True is rom_interface.read_state().move_touch_to_timer


def test_rom_interface_write_state_move_touch_to_timer_invalid():
    rom = create_move_touch_to_timer_rom(bytearray([0x8D, 0xF4, 0x7C]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_touch_to_timer
    rom_interface.write_state(State(None, False, False))
    assert False is rom_interface.read_state().move_touch_to_timer


def create_move_timer_to_exit_rom(data: bytearray) -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x68FD - 4, bytearray([0x18, 0x05, 0xF0, 0x12]))
    rom.write(0x68FD, data)
    rom.write(0x68FD + len(data), bytearray([0x88, 0xD0, 0x0B, 0x8C]))
    return rom


def test_rom_interface_read_state_move_timer_to_exit_false():
    rom = create_move_timer_to_exit_rom(bytearray([0x8C, 0xF4, 0x7C]))
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
    rom = create_move_timer_to_exit_rom(bytearray([0x8C, 0xF4, 0x7C]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_timer_to_exit
    rom_interface.write_state(State(False, True, False))
    assert True is rom_interface.read_state().move_timer_to_exit


def test_rom_interface_write_state_move_timer_to_exit_invalid():
    rom = create_move_timer_to_exit_rom(bytearray([0x8C, 0xF4, 0x7C]))
    rom_interface = RomInterface(rom)
    assert False is rom_interface.read_state().move_timer_to_exit
    rom_interface.write_state(State(False, None, False))
    assert False is rom_interface.read_state().move_timer_to_exit


def create_stop_timer_rom(jump_table: bytearray, stop_timer: bytearray) -> Rom:
    rom = Rom(bytearray([0] * 0x50000))

    rom.write(0x6014 - 4, bytearray([0x46, 0xBF, 0xFF, 0xA9]))
    rom.write(0x6014, jump_table)
    rom.write(0x6014 + len(jump_table), bytearray([0x88, 0xD0, 0x0B, 0x8C]))

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
