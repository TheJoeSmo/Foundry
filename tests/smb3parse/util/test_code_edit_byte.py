""" Test CodeEditByte implementation """
import unittest

from foundry.smb3parse.util.code_edit_byte import CodeEditByte
from foundry.smb3parse.util.rom import Rom

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])


def get_test_rom() -> Rom:
    """Create valid test ROM"""
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x100 - len(long_prefix), long_prefix)
    rom.write(0x100, bytes([0x5A]))
    rom.write(0x101, long_postfix)
    return rom


def test_length_is_1():
    """length of edit is 1 (because a byte)"""
    edit = CodeEditByte(get_test_rom(), 0x100, [], [])
    assert 1 == edit.length


def test_read():
    """read() gets the correct byte from ROM."""
    edit = CodeEditByte(get_test_rom(), 0x100, [], [])
    assert 0x5A == edit.read()


def test_read_invalid():
    """read() returns None when code area is invalid."""
    edit = CodeEditByte(get_test_rom(), 0x100, [0x11], [])
    assert None is edit.read()


def test_write():
    """write() updates value when valid."""
    edit = CodeEditByte(get_test_rom(), 0x100, long_prefix, long_postfix)
    assert 0x5A == edit.read()
    edit.write(0xA5)
    assert 0xA5 == edit.read()


def test_write_blocked_when_invalid():
    """write blocked when invalid"""
    rom = get_test_rom()
    edit = CodeEditByte(rom, 0x100, [0x11], [])
    edit.write(0xA5)
    assert 0x5A == rom.read(0x100, 1)[0]


class TestStringMethods(unittest.TestCase):
    """Class for testing assertion error for OverflowError"""

    def test_write_larger_than_byte(self):
        """if given more than a byte, an OverflowError is raised and write is
        aborted."""
        edit = CodeEditByte(get_test_rom(), 0x100, long_prefix, long_postfix)
        assert 0x5A == edit.read()
        with self.assertRaises(OverflowError):
            edit.write(0x100)
        assert 0x5A == edit.read()
