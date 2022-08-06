import subprocess
from pathlib import Path

import pytest
from git.repo.base import Repo

from foundry.smb3parse.levels.world_map import WorldMap
from foundry.smb3parse.util.rom import Rom


@pytest.fixture(scope="session")
def rom():
    rom_path = Path(__file__).parent.resolve() / "artifacts"

    if not rom_path.exists() and not rom_path.is_dir():
        Repo.clone_from("https://github.com/Drakim/smb3", rom_path)

    try:
        subprocess.run([rom_path / "asm6.exe", "smb3.asm"], cwd=rom_path)
    except PermissionError:
        # Try Linux alternative
        subprocess.run(["chmod", "+x", rom_path / "asm6.exe"])  # Give file execution perms
        subprocess.run(["wine", rom_path / "asm6.exe", "smb3.asm"], cwd=rom_path)
    test_rom_path = rom_path / "smb3.bin"

    with open(test_rom_path, "rb") as rom_file:
        yield Rom(bytearray(rom_file.read()))


@pytest.fixture
def world_1(rom):
    return WorldMap.from_world_number(rom, 1)


@pytest.fixture
def world_8(rom):
    return WorldMap.from_world_number(rom, 8)
