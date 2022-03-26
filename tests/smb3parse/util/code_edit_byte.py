from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit_byte import CodeEditByte

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])

def getTestRom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x100-len(long_prefix), long_prefix)
    rom.write(0x100, [0x5A])
    rom.write(0x101, long_postfix)
    return rom

def test_lengthIs1():
    edit = CodeEditByte(getTestRom(), 0x100, [], [])
    assert 1 == edit.length    

def test_read():
    edit = CodeEditByte(getTestRom(), 0x100, [], [])
    assert 0x5A == edit.read()

def test_write():
    edit = CodeEditByte(getTestRom(), 0x100, long_prefix, long_postfix)
    assert 0x5A == edit.read()
    edit.write(0xA5)
    assert 0xA5 == edit.read()

def test_writeBlockedWhenInvalid():
    edit = CodeEditByte(getTestRom(), 0x100, [0x11], [])
    assert 0x5A == edit.read()
    edit.write(0xA5)
    assert 0x5A == edit.read()