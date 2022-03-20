from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit_area import CodeEditArea

long_preamble = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postamble = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_amble = bytearray([])

def getTestRom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0xF8, [0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
    rom.write(0x101, [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    return rom

def test_isValidNoGuards():
    test_area = CodeEditArea(0x100, 1, empty_amble, empty_amble)
    assert True == test_area.isValid(getTestRom())

def test_isValid1BytePreambleInvalid():
    test_area = CodeEditArea(0x100, 1, [0x11], empty_amble)
    assert False == test_area.isValid(getTestRom())

def test_isValid1BytePostambleInvalid():
    test_area = CodeEditArea(0x100, 1, empty_amble, bytearray([0x11]))
    assert False == test_area.isValid(getTestRom())

def test_longPreamble():
    test_area = CodeEditArea(0x100, 1, long_preamble, empty_amble)
    assert True == test_area.isValid(getTestRom())

def test_longPostamble():
    test_area = CodeEditArea(0x100, 1, empty_amble, long_postamble)
    assert True == test_area.isValid(getTestRom())

def test_fullAmbles():
    test_area = CodeEditArea(0x100, 1, long_preamble, long_postamble)
    assert True == test_area.isValid(getTestRom())
