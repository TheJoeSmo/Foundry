import subprocess
from pathlib import Path
from shutil import copyfile

import pytest
from git.repo.base import Repo

from foundry.game.File import ROM
from foundry.gui.MainWindow import MainWindow
from foundry.smb3parse.objects.object_set import PLAINS_OBJECT_SET
from tests.conftest import level_1_1_enemy_address, level_1_1_object_address


@pytest.fixture(scope="session", autouse=True)
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
    rom = ROM(str(test_rom_path))

    yield rom


@pytest.fixture
def main_window(qtbot):
    # mock the rom loading, since it is a modal dialog. the rom is loaded in conftest.py
    MainWindow.on_open_rom = mocked_open_rom_and_level_select
    MainWindow.showMaximized = lambda _: None  # don't open automatically
    MainWindow.safe_to_change = lambda _: True  # don't ask for confirmation on changed level

    main_window = MainWindow()

    qtbot.addWidget(main_window)

    return main_window


def mocked_open_rom_and_level_select(self: MainWindow, *_):
    self.manager.controller.update_level(
        "Level 1-1", level_1_1_object_address, level_1_1_enemy_address, PLAINS_OBJECT_SET
    )

    return True
