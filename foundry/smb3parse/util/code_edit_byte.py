from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.rom import Rom

class CodeEditByte(CodeEdit):
    def __init__(self, rom: Rom, start_address: int, prefix: bytearray, postfix: bytearray):
        super().__init__(rom, start_address, 1, prefix, postfix)

    def read(self) -> int:
        return self.rom.read(self.address, self.length)[0]

    def write(self, value: int):
        if not self.isValid(): return
        self.rom.write(self.address, [value])
