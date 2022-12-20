from foundry.smb3parse.util.rom import Rom


def test_find():
    rom_bytes = bytearray(b"\x00\x01\x02\x03\x04\x05\x06\x00")

    rom = Rom(rom_bytes)

    assert rom.find(b"\x00") == 0
    assert rom.find(b"\x00", 1) == 7
    assert rom.find(b"\x07") == -1


def test_int():
    rom_bytes = bytearray(b"\x00\x01\x02\x03\x04\x1f")
    numbers = [0, 1, 2, 3, 4, 0x1F]

    rom = Rom(rom_bytes)

    for offset, number in enumerate(numbers):
        assert rom.int(offset) == number
