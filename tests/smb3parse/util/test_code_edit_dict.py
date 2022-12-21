""" Test CodeEditDict implementation. """
from foundry.game.File import ROM
from foundry.smb3parse.util.code_edit_dict import CodeEditDict

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])
default_value = bytearray([0x5A, 0xA5, 0xF0])
unknown_value = bytearray([0x00, 0xA5, 0xF0])


def get_test_rom() -> ROM:
    """Create a valid test ROM with valid prefix/postfix."""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0x100 - len(long_prefix)] = long_prefix
    rom[0x100] = default_value
    rom[0x103] = long_postfix
    return rom


def test_is_valid():
    """test is valid on valid data and valid prefix/postfix."""
    testdict = {"default": default_value}

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True is edit.is_valid()


def test_is_valid_invalid_value():
    """is_valid is False when data is unable to match."""
    testdict = {"default": unknown_value}

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert False is edit.is_valid()


def test_read_value():
    """read correctly matches when valid present."""
    testdict = {"default": default_value}

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert "default" == edit.read()


def test_read_invalid_value():
    """read returns None if unable to match data."""
    testdict = {"default": unknown_value}

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert None is edit.read()


def test_write():
    """Write is successful on valid data."""
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02]),
    }

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True is edit.is_valid()
    assert "default" == edit.read()

    edit.write("test_1")
    assert "test_1" == edit.read()

    edit.write("test_2")
    assert "test_2" == edit.read()


def test_write_invalid():
    """Write is prevented on invalid code area/data"""
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02]),
    }

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True is edit.is_valid()
    assert "default" == edit.read()

    edit.write("invalid")
    assert "default" == edit.read()


def test_write_value_incorrect_length():
    """Test that a dictionary entry that is the incorrect length will not write."""
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02, 0x02]),
    }

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), long_prefix, testdict, long_postfix)
    assert True is edit.is_valid()
    assert "default" == edit.read()

    edit.write("test_2")
    assert "default" == edit.read()


def test_valid_option():
    testdict = {
        "default": default_value,
        "test_1": bytearray([0x01, 0x01, 0x01]),
        "test_2": bytearray([0x02, 0x02, 0x02, 0x02]),
    }

    edit = CodeEditDict(get_test_rom(), 0x100, len(default_value), bytearray(), testdict, bytearray())

    assert True is edit.is_option("default")
    assert True is edit.is_option("test_1")
    assert True is edit.is_option("test_2")
    assert False is edit.is_option("test_3")
