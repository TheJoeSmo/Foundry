from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit_area import CodeEditArea

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])

def getTestRom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0xF8, [0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
    rom.write(0x101, [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    return rom

def test_isValidNoGuards():
    test_area = CodeEditArea(getTestRom(), 0x100, 1, empty_affix, empty_affix)
    assert True == test_area.isValid()

def test_isValid1BytePrefixInvalid():
    test_area = CodeEditArea(getTestRom(), 0x100, 1, [0x11], empty_affix)
    assert False == test_area.isValid()

def test_isValid1BytePostfixInvalid():
    test_area = CodeEditArea(getTestRom(), 0x100, 1, empty_affix, bytearray([0x11]))
    assert False == test_area.isValid()

def test_longPrefix():
    test_area = CodeEditArea(getTestRom(), 0x100, 1, long_prefix, empty_affix)
    assert True == test_area.isValid()

def test_longPostfix():
    test_area = CodeEditArea(getTestRom(), 0x100, 1, empty_affix, long_postfix)
    assert True == test_area.isValid()

def test_fullAffix():
    test_area = CodeEditArea(getTestRom(), 0x100, 1, long_prefix, long_postfix)
    assert True == test_area.isValid()
