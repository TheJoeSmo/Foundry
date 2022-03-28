from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.rom import Rom
from typing import Optional

class CodeEditByte(CodeEdit[int]):
    """ Edit a single byte of memory in the ROM. """
    def __init__(self, rom: Rom, start_address: int, prefix: bytearray, postfix: bytearray):
        super().__init__(rom, start_address, 1, prefix, postfix)

    def read(self) -> Optional[int]:
        """ Reads the target byte out of the ROM.
        
        This reads the byte at the target code address if both the prefix and
        postfix are valid.  If they are not valid, returns None.
        """
        if not self.is_valid(): return None
        return self.rom.read(self.address, self.length)[0]

    def write(self, value: int):
        """ Writes the specified byte to the target address if valid. 
        
        If the prefix or postfix or not valid, the write is not allowed.
        """
        if not self.is_valid(): return
        try:
            byte_to_write = value.to_bytes(1, 'little')
        except OverflowError:
            return
        else:
            self.rom.write(self.address, bytes(byte_to_write))
