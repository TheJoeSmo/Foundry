import base64
import json
import os
import pathlib
import shlex
import subprocess
import tempfile
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QMouseEvent, QShortcut, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QToolBar,
    QWhatsThis,
)

from foundry import (
    auto_save_level_data_path,
    auto_save_m3l_path,
    auto_save_rom_path,
    get_current_version_name,
    get_latest_version_name,
    icon,
    main_window_flags_path,
    open_url,
    releases_link,
)
from foundry.game.File import ROM
from foundry.game.gfx.Palette import (
    PaletteGroup,
    restore_all_palettes,
    save_all_palette_groups,
)
from foundry.game.level.LevelManager import LevelManager
from foundry.gui.AboutWindow import AboutDialog
from foundry.gui.ContextMenu import CMAction
from foundry.gui.LevelSelector import LevelSelector
from foundry.gui.settings import GUI_STYLE, SETTINGS, save_settings
from foundry.gui.SettingsDialog import POWERUPS, SettingsDialog
from foundry.gui.util import setup_window
from foundry.smb3parse.constants import (
    TILE_LEVEL_1,
    Title_DebugMenu,
    Title_PrepForWorldMap,
)
from foundry.smb3parse.levels.world_map import WorldMap as SMB3World
from foundry.smb3parse.util.rom import Rom as SMB3Rom

ROM_FILE_FILTER = "ROM files (*.nes *.rom);;All files (*)"
M3L_FILE_FILTER = "M3L files (*.m3l);;All files (*)"
IMG_FILE_FILTER = "Screenshots (*.png);;All files (*)"

with open(main_window_flags_path, "r") as data:
    main_window_flags = json.loads(data.read())
del data

menu_options_groups = main_window_flags["menu"]["view"]["options"]
menu_options = {}
for menu_option in menu_options_groups:
    menu_options.update(menu_option)

CHECKABLE_MENU_ITEMS = [option["id"] for option in menu_options.values()]
CHECKABLE_MENU = {option["id"]: option for option in menu_options.values()}
del menu_options_groups
del menu_options

ID_PROP = "ID"

# mouse modes

MODE_FREE = 0
MODE_DRAG = 1
MODE_RESIZE = 2


class MainWindow(QMainWindow):
    level_selector_last_level: Optional[tuple[int, int]]

    def __init__(self, path_to_rom="", world=None, level=None):
        super(MainWindow, self).__init__()

        self.setWindowIcon(icon(main_window_flags["icon"]))
        try:
            GUI_STYLE[SETTINGS["gui_style"]](self)
        except KeyError:
            SETTINGS["gui_style"] = "LIGHT BLUE"
            GUI_STYLE[SETTINGS["gui_style"]]

        setup_window(self, main_window_flags)

        self.manager = LevelManager(self)
        self.manager.on_enable()

        self.menu_toolbar = QToolBar("Menu Toolbar", self)
        self.menu_toolbar.setOrientation(Qt.Horizontal)
        self.menu_toolbar.setIconSize(QSize(20, 20))

        self.menu_toolbar.addAction(icon("settings.svg"), "Editor Settings").triggered.connect(self._on_show_settings)
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addAction(icon("folder.svg"), "Open ROM").triggered.connect(self.on_open_rom)
        self.menu_toolbar_save_action = self.menu_toolbar.addAction(icon("save.svg"), "Save Level")
        self.menu_toolbar_save_action.triggered.connect(self.on_save_rom)
        self.menu_toolbar.addSeparator()

        self.undo_action = self.menu_toolbar.addAction(icon("rotate-ccw.svg"), "Undo Action")
        self.undo_action.triggered.connect(self.manager.undo)
        self.undo_action.setEnabled(False)
        self.redo_action = self.menu_toolbar.addAction(icon("rotate-cw.svg"), "Redo Action")
        self.redo_action.triggered.connect(self.manager.redo)
        self.redo_action.setEnabled(False)

        self.menu_toolbar.addSeparator()
        play_action = self.menu_toolbar.addAction(icon("play-circle.svg"), "Play Level")
        play_action.triggered.connect(self.on_play)
        play_action.setWhatsThis("Opens an emulator with the current Level set to 1-1.\nSee Settings.")
        self.menu_toolbar.addSeparator()
        self.menu_toolbar.addAction(icon("zoom-out.svg"), "Zoom Out").triggered.connect(self.manager.zoom_out)
        self.menu_toolbar.addAction(icon("zoom-in.svg"), "Zoom In").triggered.connect(self.manager.zoom_in)
        self.menu_toolbar.addSeparator()
        header_action = self.menu_toolbar.addAction(icon("tool.svg"), "Edit Level Header")
        header_action.triggered.connect(self.manager.display_header_editor)
        header_action.setWhatsThis(
            "<b>Header Editor</b><br/>"
            "Many configurations regarding the level are done in its header, like the length of "
            "the timer, or where and how Mario enters the level.<br/>"
        )

        self.jump_destination_action = self.menu_toolbar.addAction(
            icon("arrow-right-circle.svg"), "Go to Jump Destination"
        )
        self.jump_destination_action.triggered.connect(self.manager.warp_to_alternative)
        self.jump_destination_action.setWhatsThis(
            "Opens the level, that can be reached from this one, e.g. by entering a pipe."
        )

        self.menu_toolbar.addSeparator()

        whats_this_action = QWhatsThis.createAction()
        whats_this_action.setWhatsThis("Click on parts of the editor, to receive help information.")
        whats_this_action.setIcon(icon("help-circle.svg"))
        whats_this_action.setText("Starts 'What's this?' mode")
        self.menu_toolbar.addAction(whats_this_action)

        self.warning_action = self.menu_toolbar.addAction(icon("alert-triangle.svg"), "Warning Panel")
        self.warning_action.setWhatsThis("Shows a list of warnings.")
        self.warning_action.setDisabled(True)
        self.warning_action.triggered.connect(self.manager.display_warnings)

        self.addToolBar(Qt.TopToolBarArea, self.menu_toolbar)

        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self, self.manager.delete)

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_X), self, self.manager.cut)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_C), self, self.manager.copy)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_V), self, self.manager.paste)

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z), self, self.manager.undo)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Y), self, self.manager.redo)
        QShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_Z), self, self.manager.redo)

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Plus), self, self.manager.zoom_in)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Minus), self, self.manager.zoom_out)

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_A), self, self.manager.select_all)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_L), self, self.manager.focus_selected)

        self.loaded = self.on_open_rom(path_to_rom, world, level)

        self.showMaximized()

    def _on_show_settings(self):
        SettingsDialog(self).exec_()

    @staticmethod
    def _save_auto_rom():
        ROM().save_to_file(auto_save_rom_path, set_new_path=False)

    def _save_auto_data(self):
        if self.manager.controller is None:
            return

        (object_offset, object_data), (enemy_offset, enemy_data) = self.manager.controller.level_ref.level.to_bytes()

        object_set_number = self.manager.controller.level_ref.level.object_set_number

        base64_data = []
        base64_data.append(
            (
                object_offset,
                base64.b64encode(object_data).decode("ascii"),
                enemy_offset,
                base64.b64encode(enemy_data).decode("ascii"),
            )
        )

        with open(auto_save_level_data_path, "w") as level_data_file:
            level_data_file.write(json.dumps([object_set_number, object_offset, enemy_offset, base64_data]))

    def _load_auto_save(self):
        # rom already loaded
        with open(auto_save_level_data_path, "r") as level_data_file:
            json_data = level_data_file.read()

            object_set_number, level_offset, enemy_offset, base64_data = json.loads(json_data)

        # load level from ROM, or from m3l file
        if level_offset == enemy_offset == 0:
            if not auto_save_m3l_path.exists():
                QMessageBox.critical(
                    self,
                    "Failed loading auto save",
                    "Could not recover m3l file, that was edited, when the editor crashed.",
                )

            with open(auto_save_m3l_path, "rb") as m3l_file:
                self.load_m3l(bytearray(m3l_file.read()), auto_save_m3l_path)
        else:
            self.update_level("recovered level", level_offset, enemy_offset, object_set_number)

        # restore undo/redo stack
        byte_data = []
        level_offset, object_data, enemy_offset, enemy_data = base64_data
        object_data = bytearray(base64.b64decode(object_data))
        enemy_data = bytearray(base64.b64decode(enemy_data))
        byte_data.append(((level_offset, object_data), (enemy_offset, enemy_data)))

        if self.manager.controller is None:
            return
        self.manager.controller.level_ref.changed = bool(base64_data)
        self.manager.controller.level_ref.do(((level_offset, object_data), (enemy_offset, enemy_data)))

    def on_play(self):
        """
        Copies the ROM, including the current level, to a temporary directory, saves the current level as level 1-1 and
        opens the rom in an emulator.
        """
        temp_dir = pathlib.Path(tempfile.gettempdir()) / "smb3foundry"
        temp_dir.mkdir(parents=True, exist_ok=True)

        path_to_temp_rom = temp_dir / "instaplay.rom"

        ROM().save_to(str(path_to_temp_rom))

        temp_rom = self._open_rom(path_to_temp_rom)

        self._put_current_level_to_level_1_1(temp_rom)
        self._set_default_powerup(temp_rom)

        save_all_palette_groups(temp_rom)

        temp_rom.write(
            Title_PrepForWorldMap - 0x8,
            bytes([SETTINGS["default_starting_world"] - 1]),
        )

        temp_rom.save_to(str(path_to_temp_rom))

        arguments = SETTINGS["instaplay_arguments"].replace("%f", str(path_to_temp_rom))
        arguments = shlex.split(arguments, posix=False)

        emu_path = pathlib.Path(SETTINGS["instaplay_emulator"])

        if emu_path.is_absolute():
            if emu_path.exists():
                emulator = str(emu_path)
            else:
                QMessageBox.critical(
                    self, "Emulator not found", f"Check it under File > Settings.\nFile {emu_path} not found."
                )
                return
        else:
            emulator = SETTINGS["instaplay_emulator"]

        try:
            subprocess.run([emulator, *arguments])
        except Exception as e:
            QMessageBox.critical(self, "Emulator command failed.", f"Check it under File > Settings.\n{str(e)}")

    @staticmethod
    def _open_rom(path_to_rom):
        with open(path_to_rom, "rb") as smb3_rom:
            data = smb3_rom.read()

        rom = SMB3Rom(bytearray(data))
        return rom

    def _put_current_level_to_level_1_1(self, rom) -> bool:
        # load world data
        world = SMB3World.from_world_number(rom, SETTINGS["default_starting_world"])

        # find position of "level 1" tile in world map
        for position in world.gen_positions():
            if position.tile() == TILE_LEVEL_1:
                break
        else:
            QMessageBox.critical(
                self, "Couldn't place level", "Could not find a level 1 tile in World 1 to put your level at."
            )
            return False

        if self.manager.controller is not None and not self.manager.controller.level_ref.level.attached_to_rom:
            QMessageBox.critical(
                self,
                "Couldn't place level",
                "The Level is not part of the rom yet (M3L?). Try saving it into the ROM first.",
            )
            return False

        # write level and enemy data of current level
        if self.manager.controller is None:
            return False
        (layout_address, layout_bytes), (
            enemy_address,
            enemy_bytes,
        ) = self.manager.controller.level_ref.level.to_bytes()
        rom.write(layout_address, layout_bytes)
        rom.write(enemy_address, enemy_bytes)

        # replace level information with that of current level
        object_set_number = self.manager.controller.level_ref.level.object_set_number

        world.replace_level_at_position((layout_address, enemy_address - 1, object_set_number), position)

    def _set_default_powerup(self, rom) -> bool:
        *_, powerup, hasPWing = POWERUPS[SETTINGS["default_powerup"]]
        hasStar = SETTINGS["default_power_has_star"]
        nop = 0xEA

        rom.write(Title_PrepForWorldMap - 0x4, bytes([nop, nop, nop]))

        rom.write(Title_PrepForWorldMap + 0x1, bytes([powerup]))

        rts = 0x60
        lda = 0xA9
        staAbsolute = 0x8D
        Map_Power_DispHigh = 0x03
        Map_Power_DispLow = 0xF3

        # If a P-wing powerup is selected, another variable needs to be set with the P-wing value
        # This piece of code overwrites a part of Title_DebugMenu
        if hasPWing:
            # We need to start one byte before Title_DebugMenu to remove the RTS of Title_PrepForWorldMap
            # The assembly code below reads as follows:
            # LDA 0x08
            # STA $03F3
            # RTS
            if hasStar:
                rom.write(
                    Title_DebugMenu - 0x1,
                    bytes(
                        [
                            lda,
                            0x08,
                            staAbsolute,
                            Map_Power_DispLow,
                            Map_Power_DispHigh,
                            lda,
                            0x10,
                            staAbsolute,
                            Map_Power_DispLow - 1,
                            Map_Power_DispHigh,
                            rts,
                        ]
                    ),
                )
            else:
                rom.write(
                    Title_DebugMenu - 0x1, bytes([lda, 0x08, staAbsolute, Map_Power_DispLow, Map_Power_DispHigh, rts])
                )

        elif hasStar:
            rom.write(
                Title_DebugMenu - 0x1, bytes([lda, 0x10, staAbsolute, Map_Power_DispLow - 1, Map_Power_DispHigh, rts])
            )

        # Remove code that resets the powerup value by replacing it with no-operations
        # Otherwise this code would copy the value of the normal powerup here
        # (So if the powerup would be Raccoon Mario, Map_Power_Disp would also be
        # set as Raccoon Mario instead of P-wing
        Map_Power_DispResetLocation = 0x3C5A2
        rom.write(Map_Power_DispResetLocation, bytes([nop, nop, nop]))

    def on_screenshot(self, _) -> bool:
        recommended_file = f"{os.path.expanduser('~')}/{ROM.name} - {self.manager.title_suggestion}.png"

        pathname, _ = QFileDialog.getSaveFileName(
            self, caption="Save Screenshot", dir=recommended_file, filter=IMG_FILE_FILTER
        )

        if not pathname:
            return False

        # Proceed loading the file chosen by the user
        self.manager.screenshot.save(pathname)

        return True

    def update_title(self):
        self.setWindowTitle(self.manager.title_suggestion if self.manager.enabled else "SMB3Foundry")

    def on_open_rom(self, path_to_rom="", world: Optional[int] = None, level: Optional[int] = None) -> bool:
        if not self.safe_to_change():
            return False

        if not path_to_rom:
            # otherwise ask the user what new file to open
            path_to_rom, _ = QFileDialog.getOpenFileName(self, caption="Open ROM", filter=ROM_FILE_FILTER)
        if not path_to_rom:
            return False

        # Proceed loading the file chosen by the user
        try:
            ROM.load_from_file(path_to_rom)

            if path_to_rom == auto_save_rom_path:
                self._load_auto_save()
            else:
                self._save_auto_rom()
                if world is not None and level is not None:
                    self.manager.force_select(world, level)
                else:
                    self.manager.on_select()
            return True
        except IOError as exp:
            QMessageBox.warning(self, type(exp).__name__, f"Cannot open file '{path_to_rom}'.")
            return False

    def on_open_m3l(self, _) -> bool:
        if not self.safe_to_change():
            return False

        # otherwise ask the user what new file to open
        pathname, _ = QFileDialog.getOpenFileName(self, caption="Open M3L file", filter=M3L_FILE_FILTER)

        if not pathname:
            return False

        # Proceed loading the file chosen by the user
        try:
            with open(pathname, "rb") as m3l_file:

                m3l_data = bytearray(m3l_file.read())
        except IOError as exp:
            QMessageBox.warning(self, type(exp).__name__, f"Cannot open file '{pathname}'.")

            return False

        self.manager.load_m3l(m3l_data, pathname)
        self.save_m3l(auto_save_m3l_path, self.manager.to_m3l())

        return True

    def safe_to_change(self) -> bool:
        if self.manager.safe_to_change:
            return True
        else:
            answer = QMessageBox.question(
                self,
                "Please confirm",
                "Current content has not been saved! Proceed?",
                QMessageBox.No | QMessageBox.Yes,
                QMessageBox.No,
            )

            return answer == QMessageBox.Yes

    def _ask_for_palette_save(self) -> bool:
        """
        If Object Palettes have been changed, this function opens a dialog box, asking the user, if they want to save
        the changes, dismiss them, or cancel whatever they have been doing (probably saving/selecting another level).
        Saving or restoring Object Palettes is done inside the function if necessary.
        :return: False, if Cancel was chosen. True, if Palettes were restored or saved to ROM.
        """
        if not PaletteGroup.changed:
            return True

        answer = QMessageBox.question(
            self,
            "Please confirm",
            "You changed some object palettes. This is a change, that potentially affects other levels in this ROM. Do "
            "you want to save these changes?",
            QMessageBox.Cancel | QMessageBox.RestoreDefaults | QMessageBox.Yes,
            QMessageBox.Cancel,
        )

        if answer == QMessageBox.Cancel:
            return False

        if answer == QMessageBox.Yes:
            save_all_palette_groups()
        elif answer == QMessageBox.RestoreDefaults:
            restore_all_palettes()
            self.manager.refresh()

        return True

    def on_save_rom(self, _):
        self.save_rom(False)

    def on_save_rom_as(self, _):
        self.save_rom(True)

    def save_rom(self, is_save_as):
        safe_to_save, reason, additional_info = self.manager.stable_changes

        if not safe_to_save:
            answer = QMessageBox.warning(
                self,
                reason,
                f"{additional_info}\n\nDo you want to proceed?",
                QMessageBox.No | QMessageBox.Yes,
                QMessageBox.No,
            )

            if answer == QMessageBox.No:
                return

        if not self.manager.is_attached:
            QMessageBox.information(
                self,
                "Importing M3L into ROM",
                "You are currently editing a level stored in an m3l file outside of the ROM. Please select the "
                "positions in the ROM you want the level objects and enemies/items to be stored.",
                QMessageBox.Ok,
            )

            level_selector = LevelSelector(self)

            answer = level_selector.exec_()

            if answer == QMessageBox.Accepted:
                self.manager.attach(level_selector.object_data_offset, level_selector.enemy_data_offset)

                if is_save_as:
                    # if we save to another rom, don't consider the level
                    # attached (to the current rom)
                    self.manager.is_attached = False
                else:
                    # the m3l is saved to the current ROM, we can get rid of the auto save
                    auto_save_m3l_path.unlink(missing_ok=True)
            else:
                return

        if is_save_as:
            pathname, _ = QFileDialog.getSaveFileName(self, caption="Save ROM as", filter=ROM_FILE_FILTER)
            if not pathname:
                return  # the user changed their mind
        else:
            pathname = ROM.path

        if str(pathname) == str(auto_save_rom_path):
            QMessageBox.critical(
                self,
                "Cannot save to auto save ROM",
                "You can't save to the auto save ROM, as it will be deleted, when exiting the editor. Please choose "
                "another location, or your changes will be lost.",
            )

        self._save_current_changes_to_file(pathname, set_new_path=True)

        self.update_title()

        if not is_save_as:
            self.manager.safe_to_change = True

    def _save_current_changes_to_file(self, pathname: str, set_new_path):
        for data in self.manager.to_data():
            ROM().bulk_write(bytearray(data.data), data.location)

        try:
            ROM().save_to_file(pathname, set_new_path)

            self._save_auto_rom()
        except IOError as exp:
            QMessageBox.warning(self, f"{type(exp).__name__}", f"Cannot save ROM data to file '{pathname}'.")

    def on_save_m3l(self, _):
        suggested_file = self.manager.title_suggestion

        if not suggested_file.endswith(".m3l"):
            suggested_file += ".m3l"

        pathname, _ = QFileDialog.getSaveFileName(
            self, caption="Save M3L as", dir=suggested_file, filter=M3L_FILE_FILTER
        )

        if not pathname:
            return

        m3l_bytes = self.manager.to_m3l()

        self.save_m3l(pathname, m3l_bytes)

    def save_m3l(self, pathname: str, m3l_bytes: bytearray):
        try:
            with open(pathname, "wb") as m3l_file:
                m3l_file.write(m3l_bytes)
        except IOError as exp:
            QMessageBox.warning(self, type(exp).__name__, f"Couldn't save level to '{pathname}'.")

    def on_check_for_update(self):
        self.setCursor(Qt.WaitCursor)

        current_version = get_current_version_name()

        try:
            latest_version = get_latest_version_name()
        except ValueError as ve:
            QMessageBox.critical(self, "Error while checking for updates", f"Error: {ve}")
            self.setCursor(Qt.ArrowCursor)
            return

        if current_version != latest_version:
            latest_release_url = f"{releases_link}/tag/{latest_version}"

            go_to_github_button = QPushButton(icon("external-link.svg"), "Go to latest release")
            go_to_github_button.clicked.connect(lambda: open_url(latest_release_url))

            info_box = QMessageBox(
                QMessageBox.Information, "New release available", f"New Version {latest_version} is available."
            )

            info_box.addButton(QMessageBox.Cancel)
            info_box.addButton(go_to_github_button, QMessageBox.AcceptRole)

            info_box.exec_()
        else:
            QMessageBox.information(self, "No newer release", f"Version {current_version} is up to date.")

        self.setCursor(Qt.ArrowCursor)

    def reload_level(self):
        self.manager.refresh()

    def on_menu(self, action: QAction):
        item_id = action.property(ID_PROP)

        if item_id in CHECKABLE_MENU_ITEMS:
            self.on_menu_item_checked(action)

            # if setting a checkbox, keep the menu open
            menu_of_action: QMenu = self.sender()
            menu_of_action.exec_()

        elif item_id in self.manager.actions:
            x, y = self.manager.last_position

            if item_id == CMAction.REMOVE:
                self.manager.delete()
            elif item_id == CMAction.ADD_OBJECT:
                self.manager.create_object_from_suggestion((x, y))
            elif item_id == CMAction.CUT:
                self.manager.cut()
            elif item_id == CMAction.COPY:
                self.manager.copy()
            elif item_id == CMAction.PASTE:
                self.manager.paste(x, y)
            elif item_id == CMAction.FOREGROUND:
                self.manager.to_foreground()
            elif item_id == CMAction.BACKGROUND:
                self.manager.to_background()

        self.manager.update()

    def on_menu_item_checked(self, action: QAction):
        item_id = action.property(ID_PROP)

        checked = action.isChecked()

        if item_id not in CHECKABLE_MENU:
            return
        setattr(self.level_view, CHECKABLE_MENU[item_id]["attribute"], checked)
        SETTINGS[CHECKABLE_MENU[item_id]["name"]] = checked

        save_settings()

    def open_level_selector(self, _):
        self.manager.on_select()

    def on_object_viewer(self):
        self.manager.display_object_viewer()

    def on_block_viewer(self, _):
        self.manager.display_block_viewer()

    def on_palette_viewer(self, _):
        self.manager.display_palette_viewer()

    def on_edit_autoscroll(self, _):
        self.manager.display_autoscroll_editor()

    def on_header_editor(self, _):
        self.manager.display_header_editor()

    def on_jump_edit(self):
        self.manager.display_jump_editor()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.manager.middle_mouse_release(self.mapToGlobal(event.position()))

    def on_about(self, _):
        about = AboutDialog(self)
        about.show()

    def closeEvent(self, event: QCloseEvent):
        if not self.safe_to_change():
            event.ignore()

            return

        auto_save_rom_path.unlink(missing_ok=True)
        auto_save_m3l_path.unlink(missing_ok=True)
        auto_save_level_data_path.unlink(missing_ok=True)

        super(MainWindow, self).closeEvent(event)
