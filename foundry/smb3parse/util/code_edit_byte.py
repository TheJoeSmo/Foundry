<<<<<<< HEAD
""" Implements a concretion of the CodeEdit interface with a byte payload.

A single byte is the data type that is written to the specified address. """
from typing import Optional

from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.rom import Rom

class CodeEditByte(CodeEdit[int]):
    """ Edit a single byte of memory in the ROM. """
    def __init__(self, rom: Rom, start_address: int, 
                 prefix: bytearray, postfix: bytearray):
=======
from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.rom import Rom
from typing import Optional

class CodeEditByte(CodeEdit[int]):
    """ Edit a single byte of memory in the ROM. """
    def __init__(self, rom: Rom, start_address: int, prefix: bytearray, postfix: bytearray):
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
        super().__init__(rom, start_address, 1, prefix, postfix)

    def read(self) -> Optional[int]:
        """ Reads the target byte out of the ROM.
<<<<<<< HEAD

        This reads the byte at the target code address if both the prefix and
        postfix are valid.  If they are not valid, returns None.
        """
        if not self.is_valid(): 
            return None
        return self.rom.read(self.address, self.length)[0]

    def write(self, option: int):
        """ Writes the specified byte to the target address if valid.

=======
        
        This reads the byte at the target code address if both the prefix and
        postfix are valid.  If they are not valid, returns None.
        """
        if not self.is_valid(): return None
        return self.rom.read(self.address, self.length)[0]

    def write(self, value: int):
        """ Writes the specified byte to the target address if valid. 
        
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
        If the prefix or postfix or not valid, the write is not allowed.

        Throws OverflowError if a value larger than a byte is given.
        """
<<<<<<< HEAD
        if not self.is_valid(): 
            return
        self.rom.write(self.address, option.to_bytes(1, 'little'))
=======
        if not self.is_valid(): return
        self.rom.write(self.address, value.to_bytes(1, 'little'))
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
