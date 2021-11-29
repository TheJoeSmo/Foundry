#!/usr/bin/env python3
import logging
import os
import sys
import traceback
from argparse import ArgumentParser, BooleanOptionalAction

import pretty_errors  # noqa: F401 is used to provide nicer messages throughout the project.
from PySide6.QtWidgets import QApplication, QMessageBox

from foundry import auto_save_rom_path, github_issue_link
from foundry.gui.AutoSaveDialog import AutoSaveDialog
from foundry.gui.settings import load_settings, save_settings

logger = logging.getLogger(__name__)

# change into the tmp directory pyinstaller uses for the data
if hasattr(sys, "_MEIPASS"):
    logger.info(f"Changing current dir to {getattr(sys, '_MEIPASS')}")
    os.chdir(getattr(sys, "_MEIPASS"))

from foundry.gui.MainWindow import MainWindow  # noqa: E402


def start():
    parser = ArgumentParser(description="The future of editing SMB3!")
    parser.add_argument("--path", dest="path", type=str, help="The path to the ROM", default="")
    parser.add_argument(
        "--dev", default=False, action=BooleanOptionalAction, type=bool, help="Override path with system path"
    )
    parser.add_argument("--level", type=int, help="Level index", default=None)
    parser.add_argument("--world", type=int, help="World Index", default=None)

    args = parser.parse_args()
    path: str = args.path
    if args.dev:
        dev_path = os.getenv("SMB3_TEST_ROM")
        if dev_path is not None:
            path = dev_path
    main(path, args.world, args.level)


def main(path_to_rom: str = "", world=None, level=None):
    load_settings()

    app = QApplication()

    if auto_save_rom_path.exists():
        result = AutoSaveDialog().exec_()

        if result == QMessageBox.AcceptRole:
            path_to_rom = auto_save_rom_path

            QMessageBox.information(
                None, "Auto Save recovered", "Don't forget to save the loaded ROM under a new name!"
            )

    window = MainWindow(path_to_rom, world, level)
    if window.loaded:
        del window.loaded
        app.exec_()
        save_settings()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ""

    try:
        main(path)
    except Exception as e:
        box = QMessageBox()
        box.setWindowTitle("Crash report")
        box.setText(
            f"An unexpected error occurred! Please contact the developers at {github_issue_link} "
            f"with the error below:\n\n{str(e)}\n\n{traceback.format_exc()}"
        )
        box.exec_()
        raise
