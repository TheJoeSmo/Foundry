""" Implements a concretion of the CodeEdit interface with a byte payload.

A single byte is the data type that is written to the specified address. """
from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.rom import Rom


class CodeEditByte(CodeEdit[int]):
    """Edit a single byte of memory in the ROM."""

    def __init__(self, rom: Rom, start_address: int, prefix: bytearray, postfix: bytearray):
        super().__init__(rom, start_address, 1, prefix, postfix)

    def read(self) -> int | None:
        """Reads the target byte out of the ROM.

        This reads the byte at the target code address if both the prefix and
        postfix are valid.  If they are not valid, returns None.
        """
        if not self.is_valid():
            return None
        return self.rom.read(self.address, self.length)[0]

    def write(self, option: int):
        """Writes the specified byte to the target address if valid.

        If the prefix or postfix or not valid, the write is not allowed.

        Throws OverflowError if a value larger than a byte is given.
        """
        if not self.is_valid():
            return
        self.rom.write(self.address, option.to_bytes(1, "little"))
