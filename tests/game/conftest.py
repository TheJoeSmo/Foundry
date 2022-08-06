import subprocess
from pathlib import Path

from git.repo.base import Repo
from pytest import fixture

from foundry.game.File import ROM


@fixture(scope="session", autouse=True)
def rom_singleton():
    rom_path = Path(__file__).parent.resolve() / "artifacts"

    if not rom_path.exists() and not rom_path.is_dir():
        Repo.clone_from("https://github.com/Drakim/smb3", rom_path)

    try:
        subprocess.run([rom_path / "asm6.exe", "smb3.asm"], cwd=rom_path)
    except PermissionError:
        # Try Linux alternative
        subprocess.run(["chmod", "+x", rom_path / "asm6.exe"])  # Give file execution perms

    test_rom_path = rom_path / "smb3.bin"

    rom = ROM(str(test_rom_path))

    yield rom
