from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit_byte import CodeEditByte

long_prefix = bytearray([0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
long_postfix = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
empty_affix = bytearray([])

def getTestRom() -> Rom:
    rom = Rom(bytearray([0] * 0x50000))
    rom.write(0x100-len(long_prefix), long_prefix)
    rom.write(0x100, [0x5A, 0xA5, 0xF0])
    rom.write(0x103, long_postfix)
    return rom