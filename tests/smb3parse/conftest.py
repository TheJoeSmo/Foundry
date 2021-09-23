from pathlib import Path

import pytest

from PySide2.QtGui import QPixmap

from tests.gui import ApprovalDialog

from foundry import root_dir
from foundry.smb3parse.levels.world_map import WorldMap
from foundry.smb3parse.util.rom import Rom

test_rom_path = root_dir / Path("SMB3.nes")
assert test_rom_path.exists(), f"The test suite needs a SMB3(U) Rom at '{test_rom_path}' to run."


@pytest.fixture()
def rom():
    if not test_rom_path.exists():
        raise ValueError(
            f"To run the test suite, place a US SMB3 Rom named '{test_rom_path}' in the root of the repository."
        )

    with open(test_rom_path, "rb") as rom_file:
        yield Rom(bytearray(rom_file.read()))


@pytest.fixture
def world_1(rom):
    return WorldMap.from_world_number(rom, 1)


@pytest.fixture
def world_8(rom):
    return WorldMap.from_world_number(rom, 8)
