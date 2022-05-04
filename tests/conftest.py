import os
import subprocess
from pathlib import Path

import pytest
from git.repo.base import Repo
from PySide6.QtGui import QPixmap

from foundry.game.File import ROM
from foundry.game.level.Level import Level
from foundry.smb3parse.objects.object_set import PLAINS_OBJECT_SET
from tests.gui import ApprovalDialog

level_1_1_object_address = 0x1FB92
level_1_1_enemy_address = 0xC537 + 1

level_1_2_object_address = 0x20F3A
level_1_2_enemy_address = 0xC6BA + 1


@pytest.fixture
def level(rom_singleton, qtbot):
    return Level("PydanticLevel 1-1", level_1_1_object_address, level_1_1_enemy_address, PLAINS_OBJECT_SET)


@pytest.fixture(scope="module", autouse=True)
def rom_singleton():
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

    rom = ROM(str(test_rom_path))

    yield rom


def compare_images(image_name: str, ref_image_path: str, gen_image: QPixmap):
    if os.path.exists(ref_image_path):
        result = ApprovalDialog.compare(image_name, QPixmap(ref_image_path), gen_image)

        if result == ApprovalDialog.Rejected:
            pytest.fail(f"{image_name} did not look like the reference.")
        elif result == ApprovalDialog.Accepted:
            pass
        elif result == ApprovalDialog.Ignore:
            pytest.skip(f"{image_name} did not look like the reference, but was ignored.")
        else:
            # accepted and overwrite ref
            gen_image.toImage().save(ref_image_path)

            pass
    else:
        gen_image.toImage().save(ref_image_path)

        pytest.skip(f"No ref image was found. Saved new ref under {ref_image_path}.")
