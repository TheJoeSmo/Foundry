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

    def _valid_affix(self, testAddress: int, data: bytearray) -> bool:
        if len(data) == 0: return True
        return data == self.rom.read(testAddress, len(data))

    def is_valid(self) -> bool:
        if not self._valid_affix(self.address - len(self.prefix), self.prefix): return False
        return self._valid_affix(self.address + self.length, self.postfix)