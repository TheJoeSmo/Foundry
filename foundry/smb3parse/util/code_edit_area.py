from dataclasses import dataclass
from foundry.smb3parse.util.rom import Rom

@dataclass
class CodeEditArea:
    address: int
    length: int
    prefix: bytearray
    postfix: bytearray

    def __validateAffix(rom: Rom, testAddress: int, data: bytearray):
        if len(data) == 0: return True
        return data == rom.read(testAddress, len(data))

    def isValid(self, rom: Rom):
        if not CodeEditArea.__validateAffix(rom, self.address - len(self.prefix), self.prefix): return False
        return CodeEditArea.__validateAffix(rom, self.address + self.length, self.postfix)
    