from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit import CodeEdit

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])

def get_test_rom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0xF8, long_prefix)
    rom.write(0x101, long_postfix)
    return rom

def test_is_valid_no_guards():
    test_area = CodeEdit(get_test_rom(), 0x100, 1, empty_affix, empty_affix)
    assert True == test_area.isValid()

def test_is_valid_1_byte_prefix_invalid():
    test_area = CodeEdit(get_test_rom(), 0x100, 1, bytearray([0x11]), empty_affix)
    assert False == test_area.isValid()

def test_is_valid_1_byte_postfix_invalid():
    test_area = CodeEdit(get_test_rom(), 0x100, 1, empty_affix, bytearray([0x11]))
    assert False == test_area.isValid()

def test_long_prefix():
    test_area = CodeEdit(get_test_rom(), 0x100, 1, long_prefix, empty_affix)
    assert True == test_area.isValid()

def test_long_postfix():
    test_area = CodeEdit(get_test_rom(), 0x100, 1, empty_affix, long_postfix)
    assert True == test_area.isValid()

def test_full_affix():
    test_area = CodeEdit(get_test_rom(), 0x100, 1, long_prefix, long_postfix)
    assert True == test_area.isValid()
    