import logging
import os
from collections.abc import Callable
from typing import Optional, Protocol, Tuple

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QPixmap, Qt
from PySide6.QtWidgets import QDialog

from foundry.core.Data import Data, DataProtocol
from foundry.game.File import ROM
from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.Palette import restore_all_palettes
from foundry.game.level.Level import Level, world_and_level_for_level_address
from foundry.game.level.LevelControlled import LevelControlled
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.AutoScrollEditor import AutoScrollEditor
from foundry.gui.BlockViewer import BlockViewer
from foundry.gui.HeaderEditor import HeaderEditor
from foundry.gui.JumpEditor import JumpEditor
from foundry.gui.LevelSelector import LevelSelector
from foundry.gui.LevelView import undoable
from foundry.gui.PaletteViewer import PaletteViewer


def require_safe_to_change(function: Callable):
    def required_safe_to_change_wrapper(self, *args, **kwargs):
        if self.parent.safe_to_change:
            return function(self, *args, **kwargs)

    return required_safe_to_change_wrapper


class LevelSelectorController(Protocol):
    last_level: Optional[tuple[int, int]]


class LevelController:
    def __init__(self, parent: LevelControlled, level_ref: LevelRef):
        self.parent = parent
        self.level_ref = level_ref
        self.level_ref.data_changed.connect(self.on_level_data_changed)
        self.level_selector_last_level = None

    @property
    def changes(self) -> list[DataProtocol]:
        (gen_loc, gen_data), (ene_loc, ene_data) = self.level_ref.level.to_bytes()
        return [Data(gen_loc, gen_data), Data(ene_loc, ene_data)]

    @property
    def screenshot(self) -> QPixmap:
        return self.parent.level_view.make_screenshot()

    @property
    def title_suggestion(self) -> str:
        return f"{self.parent.level_view.level_ref.level.name} - {ROM.name}"

    @property
    def last_position(self) -> tuple[int, int]:
        return self.parent.context_menu.get_position()

    @property
    def actions(self) -> list[QAction]:
        return self.parent.context_menu.get_all_menu_item_ids()

    @property
    def suggested_object(self) -> int:
        return self.parent.object_dropdown.currentIndex()

    @require_safe_to_change
    def on_reload(self) -> None:
        self.update_level(
            level_name=self.level_ref.level.name,
            object_data_offset=self.level_ref.level.header_offset,
            enemy_data_offset=self.level_ref.level.enemy_offset,
            object_set=self.level_ref.level.object_set_number,
        )

    @require_safe_to_change
    def warp_to_alternative(self):
        level_address = self.level_ref.level.next_area_objects
        enemy_address = self.level_ref.level.next_area_enemies + 1
        object_set = self.level_ref.level.next_area_object_set

        world, level = world_and_level_for_level_address(level_address)

        self.update_level(f"Level {world}-{level}", level_address, enemy_address, object_set)

    @require_safe_to_change
    def on_select(self):
        selector = LevelSelector(self.parent, start_level=self.level_selector_last_level)

        if QDialog.Accepted == selector.exec():
            self.level_selector_last_level = selector.current_level_index
            self.update_level(
                selector.level_name if selector.level_name is not None else "",
                selector.object_data_offset,
                selector.enemy_data_offset,
                selector.object_set,
            )

    def to_data(self) -> list[DataProtocol]:
        (object_offset, object_data), (enemy_offset, enemy_data) = self.level_ref.state

        return [Data(object_offset, object_data), Data(enemy_offset, enemy_data)]

    def load_m3l(self, m3l_data: bytearray, pathname: str):
        self.level_ref.level.from_m3l(m3l_data)
        self.level_ref.level.name = os.path.basename(pathname)

        self.update_gui_for_level()

    def to_m3l(self) -> bytearray:
        return self.level_ref.level.to_m3l()

    def refresh(self):
        self.on_reload()
        self.level_ref.level.reload()

    def update(self):
        self.parent.level_view.update()

    @property
    def safe_to_change(self) -> bool:
        if not self.level_ref.is_loaded:
            return True
        return not self.level_ref.level.changed and not self.parent.side_palette.changed

    @safe_to_change.setter
    def safe_to_change(self, value: bool):
        self.level_ref.level.changed = not value
        self.parent.side_palette.changed = not value

    @property
    def stable_changes(self) -> tuple[bool, str, str]:
        return self.parent.level_view.level_safe_to_save()

    @property
    def is_attached(self) -> bool:
        return self.level_ref.level.attached_to_rom

    @is_attached.setter
    def is_attached(self, value: bool):
        self.level_ref.level.attached_to_rom = value

    def attach(self, generator_pointer: int, enemy_pointer: int):
        self.level_ref.level.attach_to_rom(generator_pointer, enemy_pointer)

    def zoom_in(self):
        self.parent.level_view.zoom_in()

    def zoom_out(self):
        self.parent.level_view.zoom_out()

    def middle_mouse_release(self, position: QPoint):
        pointf = self.parent.level_view.mapFromGlobal(position)
        pos = (int(pointf.x()), int(pointf.y()))

        # If the number is negative do not do anything
        if any([num < 0 for num in pos]):
            return
        self.place_object_from_dropdown(pos)

    @undoable
    def to_foreground(self):
        self.level_ref.level.bring_to_foreground(self.level_ref.selected_objects)

    @undoable
    def to_background(self):
        self.level_ref.level.bring_to_background(self.level_ref.selected_objects)

    @undoable
    def create_object_at(self, x: int, y: int):
        self.parent.level_view.create_object_at(x, y)

    @undoable
    def create_enemy_at(self, x: int, y: int):
        self.parent.level_view.create_enemy_at(x, y)

    def cut(self):
        self.copy()
        self.delete()

    def copy(self):
        if selected := self.parent.level_view.get_selected_objects().copy():
            self.parent.context_menu.set_copied_objects(selected)

    @undoable
    def paste(self, x: Optional[int] = None, y: Optional[int] = None):
        self.parent.level_view.paste_objects_at(self.parent.context_menu.get_copied_objects(), x, y)

    def select_all(self):
        self.parent.level_view.select_all()

    def focus_selected(self):
        self.parent.object_dropdown.setFocus()

    @undoable
    def delete(self):
        self.parent.jump_list.delete()
        self.parent.level_view.remove_selected_objects()
        self.parent.level_view.update()
        self.parent.spinner_panel.disable_all()

    @undoable
    def on_jump_added(self):
        self.parent.level_view.add_jump()

    @undoable
    def on_jump_removed(self):
        self.parent.level_view.remove_jump(self.parent.jump_list.currentIndex().row())

    @undoable
    def on_jump_edited(self, jump):
        index = self.parent.jump_list.currentIndex().row()

        assert index >= 0

        if isinstance(self.level_ref.level, Level):
            self.level_ref.level.jumps[index] = jump
            self.parent.jump_list.item(index).setText(str(jump))

    @undoable
    def place_object_from_dropdown(self, pos: Tuple[int, int]) -> None:
        # the dropdown is synchronized with the toolbar, so it doesn't matter where to take it from
        level_object = self.parent.object_dropdown.currentData(Qt.UserRole)

        self.parent.object_toolbar.add_recent_object(level_object)

        if isinstance(level_object, LevelObject):
            self.parent.level_view.create_object_at(*pos, level_object.domain, level_object.obj_index)
        elif isinstance(level_object, EnemyObject):
            self.parent.level_view.add_enemy(level_object.obj_index, *pos, -1)

    @undoable
    def on_spin(self, _):
        selected_objects = self.level_ref.selected_objects

        if len(selected_objects) != 1:
            logging.error(selected_objects, RuntimeWarning)
            return

        selected_object = selected_objects[0]

        obj_type = self.parent.spinner_panel.get_type()

        if isinstance(selected_object, LevelObject):
            domain = self.parent.spinner_panel.get_domain()

            if selected_object.is_4byte:
                length = self.parent.spinner_panel.get_length()
            else:
                length = None

            self.parent.level_view.replace_object(selected_object, domain, obj_type, length)
        else:
            self.parent.level_view.replace_enemy(selected_object, obj_type)

        self.level_ref.data_changed.emit()

    def on_level_data_changed(self):
        self.parent.undo_action.setEnabled(self.level_ref.can_undo)
        self.parent.redo_action.setEnabled(self.level_ref.can_redo)

        self.parent.jump_destination_action.setEnabled(self.level_ref.level.has_next_area)
        self.parent.menu_toolbar_save_action.setEnabled(
            self.level_ref.level.changed or not self.level_ref.level.attached_to_rom or self.parent.side_palette.changed
        )

    def update_level(self, level_name: str, object_data_offset: int, enemy_data_offset: int, object_set: int):
        self.level_ref.load_level(level_name, object_data_offset, enemy_data_offset, object_set)
        self.update_gui_for_level()
        self.parent.update_title()
        self.parent.side_palette.load_from_level(self.level_ref.level)

    def update_gui_for_level(self):
        restore_all_palettes()

        self.parent.jump_list.update()
        self.parent.object_dropdown.set_object_set(
            self.level_ref.level.object_set_number, self.level_ref.level.graphic_set
        )
        self.parent.object_toolbar.set_object_set(
            self.level_ref.level.object_set_number, self.level_ref.level.graphic_set
        )

        self.parent.level_view.update()

    def display_header_editor(self):
        header_editor = HeaderEditor(self.parent, self.level_ref)  # type: ignore
        header_editor.tab_widget.setCurrentIndex(3)
        header_editor.exec_()

    def display_jump_editor(self):
        index = self.parent.jump_list.currentIndex().row()

        updated_jump = JumpEditor.edit_jump(
            self.parent,  # type: ignore
            self.level_ref.level.jumps[index],
            not self.level_ref.level.is_vertical,
            (self.level_ref.level.length // 0x10) - 1,
        )

        self.on_jump_edited(updated_jump)

    def display_palette_viewer(self):
        PaletteViewer(self.parent, self.level_ref).exec_()

    def display_autoscroll_editor(self):
        AutoScrollEditor(self.parent, self.level_ref).exec_()

    def display_block_viewer(self):
        block_viewer = BlockViewer(parent=self.parent)
        block_viewer.object_set = self.level_ref.level.object_set.number
        block_viewer.palette_group = self.level_ref.level.object_palette_index
        block_viewer.show()

    def display_warnings(self):
        self.parent.warning_list.show()
