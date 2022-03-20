from dataclasses import dataclass
from foundry.smb3parse.util.rom import Rom

@dataclass
class CodeEditArea:
    start_address: int
    length: int
    pre_guard: bytearray
    post_guard: bytearray

    def isValid(self, rom: Rom):
        return True
    