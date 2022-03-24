from dataclasses import dataclass
from foundry.smb3parse.util.rom import Rom

@dataclass
class CodeEditArea:
    address: int
    length: int
    preamble: bytearray
    postamble: bytearray

    def __validate(rom: Rom, testAddress: int, data: bytearray):
        if len(data) == 0: return True
        return data == rom.read(testAddress, len(data))

    def isValid(self, rom: Rom):
        if not CodeEditArea.__validate(rom, self.address - len(self.preamble), self.preamble): return False
        return CodeEditArea.__validate(rom, self.address + self.length, self.postamble)
    