from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit_dict import CodeEditDict

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])
default_value = bytearray([0x5A, 0xA5, 0xF0])
unknown_value = bytearray([0x00, 0xA5, 0xF0])

def getTestRom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x100-len(long_prefix), long_prefix)
    rom.write(0x100, default_value)
    rom.write(0x103, long_postfix)
    return rom

def test_isValid():
    testdict = {
        "default": default_value
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True == edit.isValid()

def test_isValidInvalidValue():
    testdict = {
        "default": unknown_value
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert False == edit.isValid()

def test_readValid():
    testdict = {
        "default": default_value
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert "default" == edit.read()

def test_readInvalidValue():
    testdict = {
        "default": unknown_value
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert None == edit.read()

def test_write():
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02])
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True == edit.isValid()
    assert "default" == edit.read()

    edit.write("test_1")
    assert "test_1" == edit.read()

    edit.write("test_2")
    assert "test_2" == edit.read()

def test_writeInvalid():
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02])
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True == edit.isValid()
    assert "default" == edit.read()

    edit.write("invalid")
    assert "default" == edit.read()


def test_writeValueIncorrectLength():
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02, 0x02])
    }

    edit = CodeEditDict(getTestRom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True == edit.isValid()
    assert "default" == edit.read()

    edit.write("test_2")
    assert "default" == edit.read()

    
