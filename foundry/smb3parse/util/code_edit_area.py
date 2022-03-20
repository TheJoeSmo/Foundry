from dataclasses import dataclass
from foundry.smb3parse.util.rom import Rom

@dataclass
class CodeEditArea:
    start_address: int
    length: int
    preamble: bytearray
    postamble: bytearray

    def __validate(rom: Rom, address: int, data: bytearray):
        if len(data) == 0: return True
        return data == rom.read(address, len(data))

    def isValid(self, rom: Rom):
        if CodeEditArea.__validate(rom, self.start_address - len(self.preamble), self.preamble) == False: return False
        return CodeEditArea.__validate(rom, self.start_address + len(self.postamble), self.postamble) == True
    