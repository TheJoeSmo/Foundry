from dataclasses import dataclass
from typing import Any
from foundry.smb3parse.util.rom import Rom

@dataclass
class CodeEdit:
    rom: Rom
    address: int
    length: int
    prefix: bytearray
    postfix: bytearray

    def __validateAffix(self, testAddress: int, data: bytearray):
        if len(data) == 0: return True
        return data == self.rom.read(testAddress, len(data))

    def isValid(self):
        if not self.__validateAffix(self.address - len(self.prefix), self.prefix): return False
        return self.__validateAffix(self.address + self.length, self.postfix)