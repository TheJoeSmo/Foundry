from typing import Any

from PySide6.QtCore import QSize
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from foundry import icon
from foundry.core.gui import Signal, SignalInstance
from foundry.core.palette import PaletteGroup
from foundry.game.File import ROM
from foundry.graphic_editor import ROM_FILTER
from foundry.graphic_editor.Canvas import Canvas
from foundry.graphic_editor.internal_plugins import CommonIcons
from foundry.gui.core import MainWindow
from foundry.gui.Menu import Menu
from foundry.gui.palette import PaletteGroupWidget
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


class GraphicEditor(MainWindow):
    _updated = Signal()

    _file_path: str | None = None

    def __init__(self, path: str | None, parent: Any = None, *args, **kwargs) -> None:
        self._parent = parent
        self._file_path = path
        super().__init__(parent)

        self.initialize_state(path, *args, **kwargs)

    @property
    def updated(self) -> SignalInstance[str | None]:
        return SignalInstance(self, self._updated)

    @property
    def is_loaded(self) -> bool:
        return self.file_path is not None

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @file_path.setter
    def file_path(self, path: str | None) -> None:
        self._file_path = path
        self.updated.emit(path)

    def initialize_state(
        self, path: str | None, user_settings: UserSettings | None = None, gui_loader: GUILoader | None = None
    ):
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
        self.menu_toolbar.setOrientation(Qt.Orientation.Horizontal)
        self.menu_toolbar.setIconSize(QSize(20, 20))
        self.menu_toolbar.add_action(
            "Editor Settings", self.display_settings_dialog, icon=CommonIcons.to_icon(CommonIcons.SETTINGS)
        )
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.menu_toolbar)

        self.bottom_toolbar = Toolbar("Bottom Toolbar", self)
        self.bottom_toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.bottom_toolbar.setOrientation(Qt.Orientation.Horizontal)
        self.bottom_toolbar.setFloatable(True)
        self.bottom_toolbar.setAllowedAreas(Qt.ToolBarArea.BottomToolBarArea | Qt.ToolBarArea.TopToolBarArea)

        self.palette_group_widget = PaletteGroupWidget(PaletteGroup.as_empty())  # type: ignore

        self.bottom_toolbar.addWidget(self.palette_group_widget)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.bottom_toolbar)

        self.file_path = open_file(self, self.file_path)
        if not self.is_loaded:
            return

        canvas = Canvas(Canvas.Model(), self)
        self.setCentralWidget(canvas)

        self.showMaximized()

    def change_active_rom(self, *_, path: str | None = None) -> str | None:
        self.file_path = open_file(self, path)
        self.update()
        return path

    def display_settings_dialog(self):
        SettingsDialog(self, user_settings=self.user_settings, gui_loader=self.gui_loader).exec()
