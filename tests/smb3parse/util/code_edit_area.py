from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit_area import CodeEditArea

def getTestRom() -> Rom:
    return Rom(bytearray([0] * 0x50000))


def test_isValidNoGuards():
    test_area = CodeEditArea(0x100, 1, [], [])
    assert True == test_area.isValid(getTestRom())
