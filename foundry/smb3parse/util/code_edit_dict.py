from typing import Any
from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit import CodeEdit

class CodeEditDict(CodeEdit):
    options: dict

    def __init__(self, rom: Rom, start_address: int, length: int, prefix: bytearray, options: dict, postfix: bytearray):
        """
        options: dict 
            * needs to be of types: [Any, bytearray]
            * all of the values(bytearray) should be the same length
            * values(bytearray) are what will be written to memory or used to find the current setting
            * values(bytearray) need to be same length as length parameter
            * duplicates in values will return first found entry on read
        """
        super().__init__(rom, start_address, length, prefix, postfix)
        self.options = options

    def isValid(self):
        if not super().isValid(): return False
        return self.read() is not None

    def read(self) -> Any:
        rom_value = self.rom.read(self.address, self.length) 
        for key, value in self.options.items():
            if rom_value == value:
                return key
        return None

    def write(self, selection: Any):
        try:
            value = self.options[selection]
            if len(value) is self.length:
                self.rom.write(self.address, value)
        except:
            pass
