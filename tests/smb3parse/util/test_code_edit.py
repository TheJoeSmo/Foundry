""" Test the abstract CodeEdit class """

from foundry.game.File import ROM
from foundry.smb3parse.util.code_edit import CodeEdit

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])


class CodeEditTest(CodeEdit[bool]):
    """Create simple concretion of abstract class for testing."""

    value: bool = True

    def read(self) -> bool:
        """mock read implementation."""
        return self.value

    def write(self, value: bool):
        """mock write implementation."""
        self.value = value


def get_test_rom() -> ROM:
    """Create a test ROM with valid prefix/postfix"""
    rom: ROM = ROM(None, "test", bytearray([0] * 0x50000), "test", None, None)  # type: ignore
    rom[0xF8] = long_prefix
    rom[0x101] = long_postfix
    return rom


def test_is_valid_no_guards():
    """A code edit with no prefix/postfix should be valid."""
    test_area = CodeEditTest(get_test_rom(), 0x100, 1, empty_affix, empty_affix)
    assert True is test_area.is_valid()


def test_is_valid_1_byte_prefix_invalid():
    """invalid prefix is not valid."""
    test_area = CodeEditTest(get_test_rom(), 0x100, 1, bytearray([0x11]), empty_affix)
    assert False is test_area.is_valid()


def test_is_valid_1_byte_postfix_invalid():
    """invalid postfix is not valid."""
    test_area = CodeEditTest(get_test_rom(), 0x100, 1, empty_affix, bytearray([0x11]))
    assert False is test_area.is_valid()


def test_long_prefix():
    """valid long prefix only is valid."""
    test_area = CodeEditTest(get_test_rom(), 0x100, 1, long_prefix, empty_affix)
    assert True is test_area.is_valid()


def test_long_postfix():
    """valid long postfix only is valid."""
    test_area = CodeEditTest(get_test_rom(), 0x100, 1, empty_affix, long_postfix)
    assert True is test_area.is_valid()


def test_full_affix():
    """valid long prefix and postfix is valid."""
    test_area = CodeEditTest(get_test_rom(), 0x100, 1, long_prefix, long_postfix)
    assert True is test_area.is_valid()
