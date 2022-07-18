from attr import attrs
from PySide6.QtCore import QSize
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QWidget

from foundry import icon
from foundry.game.File import ROM
from foundry.graphic_editor import ROM_FILTER
from foundry.graphic_editor.internal_plugins import CommonIcons
from foundry.gui.Menu import Menu
from foundry.gui.settings import GUILoader, UserSettings, load_gui_loader
from foundry.gui.SettingsDialog import SettingsDialog
from foundry.gui.Toolbar import Toolbar


def ask_user_to_select_file(parent: QWidget) -> str | None:
    """
    Asks the user to select a ROM file.

    Parameters
    ----------
    parent : QWidget
        The parent to make the dialog from.

    Returns
    -------
    str | None
        The path the user selected, otherwise None.
    """
    path, _ = QFileDialog.getOpenFileName(parent, caption="Open ROM", filter=ROM_FILTER)
    return path


def open_file(parent: QWidget, path: str | None = None) -> str | None:
    """
    Opens the ROM file provided from the user or requests that they select another path.

    Parameters
    ----------
    parent : QWidget
        The parent to make the dialogs from.
    path : str | None, optional
        The path to default the user to, by default None

    Returns
    -------
    str | None
        The path the user selected, None if the ROM failed to load.
    """
    path = path or ask_user_to_select_file(parent)
    if not path:
        return None

    try:
        ROM.load_from_file(path)
    except OSError as exp:
        QMessageBox.warning(parent, type(exp).__name__, f"Cannot open file '{path}'.")
        return None
    return path


@attrs(slots=True, auto_attribs=True)
class GraphicEditorModel:
    path: str


class GraphicEditor(QMainWindow):
    def __init__(
        self, path: str | None, user_settings: UserSettings | None = None, gui_loader: GUILoader | None = None
    ):
        super().__init__()

        self.setWindowIcon(icon("foundry.ico"))
        self.user_settings = UserSettings() if user_settings is None else user_settings
        self.gui_loader = load_gui_loader() if gui_loader is None else gui_loader

        # Set up the menu items

        # Set up the file menu options
        menu = Menu("File", self)
        menu.add_action("Open ROM", lambda: self.change_active_rom())
        menu.add_action("Save ROM")
        menu.add_action("Save ROM as ...")
        menu.addSeparator()
        menu.add_action("Settings")
        menu.addSeparator()
        menu.add_action("Exit", self.close)

        self.menuBar().addMenu(menu)

        # Set up the primary options
        self.menu_toolbar = Toolbar("Menu Toolbar", self)
        self.menu_toolbar.setOrientation(Qt.Horizontal)
        self.menu_toolbar.setIconSize(QSize(20, 20))
        self.menu_toolbar.add_action(
            "Editor Settings", self.display_settings_dialog, icon=CommonIcons.to_icon(CommonIcons.SETTINGS)
        )

        path = open_file(self, path)
        if path is None:
            self.loaded = False
            return
        self.loaded = True

        self.showMaximized()

    def change_active_rom(self, *_, path: str | None = None) -> str | None:
        path = open_file(self, path)
        self.update()
        return path

    def display_settings_dialog(self):
        SettingsDialog(self, user_settings=self.user_settings, gui_loader=self.gui_loader).exec_()
