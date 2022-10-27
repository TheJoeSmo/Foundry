def start():
    """
    The starting point to the command line application for the graphical editor.

    Notes
    -----
    The options are as follows:

    -h, --help       Show a help message and exit
    --path PATH      The path to the ROM
    --dev, --no-dev  Override path with system path to `SMB3_TEST_ROM`, by default False
    """
    from argparse import ArgumentParser, BooleanOptionalAction
    from os import getenv

    parser = ArgumentParser(description="A built in utility to graphically expand the horizons of SMB3!")
    parser.add_argument("--path", dest="path", type=str, help="The path to the ROM", default="")
    parser.add_argument(
        "--dev", default=False, action=BooleanOptionalAction, type=bool, help="Override path with system path"
    )
    parser.add_argument(
        "--debug", default="n", choices=["n", "d", "i", "w", "c"], help="Shows additional debug information"
    )

    args = parser.parse_args()
    path: str | None = args.path
    if args.dev:
        path = getenv("SMB3_TEST_ROM")
    if args.debug != "n":
        from logging import CRITICAL, DEBUG, INFO, WARNING, basicConfig

        basicConfig(
            filename="./log.log",
            level={"d": DEBUG, "i": INFO, "w": WARNING, "c": CRITICAL}[args.debug],
            encoding="utf-8",
            filemode="w",
        )

    main(path)


def main(path: str | None = None):
    """
    Starts the graphical application with `path` specified from the user.

    Parameters
    ----------
    path : str | None, optional
        The path to the ROM to edit, by default None
    """
    from PySide6.QtWidgets import QApplication

    from foundry.graphic_editor.GraphicEditor import GraphicEditor
    from foundry.graphic_editor.internal_plugins import load_namespace
    from foundry.gui.settings import load_gui_loader, load_settings, save_settings

    user_settings = load_settings()
    gui_loader = load_gui_loader()

    app = QApplication()

    load_namespace()

    window = GraphicEditor(path=path, user_settings=user_settings, gui_loader=gui_loader)
    if window.is_loaded:
        app.exec()
        save_settings(user_settings)
