import subprocess
from pathlib import Path
from shutil import copyfile

import pytest
from git.repo.base import Repo
from pytest import fixture

from foundry.game.File import ROM
from foundry.smb3parse.levels.world_map import WorldMap


@fixture(scope="session", autouse=True)
def rom_singleton():
    rom_directory: Path = Path(__file__).parent.resolve() / "artifacts"
    rom_path: Path = rom_directory / "smb3.bin"
    test_rom_path: Path = rom_directory / "smb3_test.nes"

    if not rom_directory.exists() and not rom_directory.is_dir():
        Repo.clone_from("https://github.com/Drakim/smb3", rom_directory)

    if not rom_path.exists():
        try:
            subprocess.run([rom_directory / "asm6.exe", "smb3.asm"], cwd=rom_directory)
        except PermissionError:
            # Try Linux alternative
            subprocess.run(["chmod", "+x", rom_directory / "asm6.exe"])  # Give file execution perms

    copyfile(rom_path, test_rom_path)
    rom = ROM.from_file(test_rom_path)

    yield rom


@pytest.fixture
def world_1(rom_singleton: ROM):
    return WorldMap.from_world_number(rom_singleton, 1)


@pytest.fixture
def world_8(rom_singleton: ROM):
    return WorldMap.from_world_number(rom_singleton, 8)
