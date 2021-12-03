from collections.abc import Callable
from typing import Optional, Protocol, TypeVar

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QPixmap, Qt
from PySide6.QtWidgets import QScrollArea, QSplitter

from foundry.core.Data import DataProtocol
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.level import LevelByteData
from foundry.game.level.LevelController import LevelController
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.ContextMenu import ContextMenu
from foundry.gui.JumpCreator import JumpCreator
from foundry.gui.JumpList import JumpList
from foundry.gui.LevelSelector import select_by_world_and_level
from foundry.gui.LevelSizeBar import LevelSizeBar
from foundry.gui.LevelView import LevelView
from foundry.gui.ObjectDropdown import ObjectDropdown
from foundry.gui.ObjectIcon import ObjectButton
from foundry.gui.ObjectIcon import ObjectViewer as ObjectToolbarViewer
from foundry.gui.ObjectList import ObjectList
from foundry.gui.ObjectStatusBar import ObjectStatusBar
from foundry.gui.ObjectToolBar import ObjectToolBar
from foundry.gui.ObjectViewer import ObjectViewer
from foundry.gui.PaletteEditor import PaletteEditor
from foundry.gui.SpinnerPanel import SpinnerPanel
from foundry.gui.Toolbar import create_toolbar
from foundry.gui.WarningList import WarningList


class Manager(Protocol):
    @property
    def enabled(self) -> bool:
        ...

    def display_block_viewer(self) -> None:
        ...

    def display_object_viewer(self) -> None:
        ...


T = TypeVar("T")


def require_enabled(function: Callable[..., T]) -> Callable[..., T]:
    def require_enabled_wrapped(self, *args, **kwargs):
        if self.controller is None:
            raise NotImplementedError(f"{self.__class__.__name__} is not enabled")
        return function(self, *args, **kwargs, controller=self.controller)

    return require_enabled_wrapped


class LevelManager:
    def __init__(self, parent):
        self.parent = parent
        self.controller: Optional[LevelController] = None
        self._enabled = False
        self._has_warnings = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def has_warnings(self) -> bool:
        return self._has_warnings

    @has_warnings.setter
    def has_warnings(self, value: bool) -> None:
        self._has_warnings
        self.parent.warning_action.setEnabled(value)

    def display_object_viewer(self):
        object_viewer = ObjectViewer(parent=self.parent)

        if self.enabled and self.controller is not None:
            object_viewer.set_object_and_graphic_set(
                self.controller.level_ref.level.object_set.number, self.controller.level_ref.level.graphic_set
            )

            if len(self.parent.level_view.get_selected_objects()) == 1:
                selected_object = self.parent.level_view.get_selected_objects()[0]

                if isinstance(selected_object, LevelObject):
                    object_viewer.set_object(selected_object.domain, selected_object.obj_index, selected_object.length)

        object_viewer.show()

    def on_disable(self):
        self._enabled = False

    def on_enable(self):
        self._enabled = True

        level_ref = LevelRef()

        self.controller = LevelController(self.parent, level_ref)

        self.parent.context_menu = ContextMenu(level_ref)
        self.parent.context_menu.triggered.connect(self.parent.on_menu)  # type: ignore
        self.parent.level_view = LevelView(self.parent, level_ref, self.parent.context_menu)
        self.parent.scroll_panel = QScrollArea()
        self.parent.scroll_panel.setWidgetResizable(True)
        self.parent.scroll_panel.setWidget(self.parent.level_view)
        self.parent.setCentralWidget(self.parent.scroll_panel)

        self.parent.spinner_panel = SpinnerPanel(self.parent, level_ref)
        self.parent.spinner_panel.zoom_in_triggered.connect(self.parent.level_view.zoom_in)
        self.parent.spinner_panel.zoom_out_triggered.connect(self.parent.level_view.zoom_out)
        self.parent.spinner_panel.object_change.connect(self.controller.on_spin)

        self.parent.object_list = ObjectList(self.parent, level_ref, self.parent.context_menu)

        self.parent.object_dropdown = ObjectDropdown(self.parent)
        self.parent.object_dropdown.object_selected.connect(self.parent.object_dropdown.select_object)

        self.parent.level_size_bar = LevelSizeBar(self.parent, "Generators", 0, 0)

        def update_level_size_bar(*args, **kwargs):
            self.parent.level_size_bar.current_value = level_ref.level.current_object_size()
            self.parent.level_size_bar.maximum_value = level_ref.level.object_size_on_disk

        level_ref.data_changed.connect(update_level_size_bar)

        self.parent.enemy_size_bar = LevelSizeBar(self.parent, "Enemies/Items", 0, 0)

        def update_enemy_size_bar(*args, **kwargs):
            self.parent.enemy_size_bar.current_value = level_ref.level.current_enemies_size()
            self.parent.enemy_size_bar.maximum_value = level_ref.level.enemy_size_on_disk

        level_ref.data_changed.connect(update_enemy_size_bar)

        self.parent.side_palette = PaletteEditor(self.parent)
        self.parent.side_palette.palette_updated.connect(
            lambda *_: self.controller.on_level_data_changed() if self.controller is not None else None
        )

        self.parent.jump_list = JumpList(self.parent, level_ref)
        self.parent.jump_list.add_jump.connect(self.controller.on_jump_added)
        self.parent.jump_list.edit_jump.connect(self.controller.display_jump_editor)
        self.parent.jump_list.remove_jump.connect(self.controller.on_jump_removed)

        # Toolbar Creation
        splitter = QSplitter(self.parent)
        splitter.setOrientation(Qt.Vertical)

        splitter.addWidget(self.parent.object_list)
        splitter.setStretchFactor(1, 1)
        splitter.addWidget(self.parent.jump_list)
        splitter.addWidget(JumpCreator(parent=self.parent, level_view=self.parent.level_view))

        splitter.setChildrenCollapsible(False)

        create_toolbar(self.parent, "Generator Editor", [self.parent.spinner_panel], Qt.RightToolBarArea)
        create_toolbar(self.parent, "Generator Dropdown", [self.parent.object_dropdown], Qt.RightToolBarArea)
        create_toolbar(self.parent, "Palette", [self.parent.side_palette], Qt.RightToolBarArea)
        create_toolbar(self.parent, "Level Size", [self.parent.level_size_bar], Qt.RightToolBarArea)
        create_toolbar(self.parent, "Enemy Size", [self.parent.enemy_size_bar], Qt.RightToolBarArea)
        create_toolbar(self.parent, "Splitter", [splitter], Qt.RightToolBarArea)

        self.parent.object_toolbar = ObjectToolBar(self.parent)
        self.parent.object_toolbar_viewer = ObjectToolbarViewer(self.parent)

        def set_object_viewer(item):
            self.parent.object_toolbar_viewer.icon = ObjectButton(self.parent.object_toolbar_viewer, item)

        def set_object_viewer_from_selected(items):
            if len(items) == 1:
                self.parent.object_toolbar_viewer.icon = ObjectButton(self.parent.object_toolbar_viewer, items[0])

        self.parent.object_dropdown.object_selected.connect(set_object_viewer)
        self.parent.level_view.objects_selected.connect(set_object_viewer_from_selected)
        self.parent.object_toolbar.selected.connect(set_object_viewer)
        self.parent.object_toolbar.selected.connect(self.parent.object_dropdown.select_object)

        create_toolbar(self.parent, "Object Viewer", [self.parent.object_toolbar_viewer], Qt.LeftToolBarArea)
        create_toolbar(self.parent, "Object Toolbar", [self.parent.object_toolbar], Qt.LeftToolBarArea)

        # Warning List Creation

        self.parent.warning_list = WarningList(self.parent, level_ref, self.parent.level_view, self.parent.object_list)
        self.parent.warning_list.warnings_updated.connect(lambda value: setattr(self, "has_warnings", value))

        # Status Bar Creation

        self.parent.setStatusBar(ObjectStatusBar(self.parent, level_ref))

    @property
    @require_enabled
    def is_attached(self, controller: LevelController) -> bool:
        return controller.is_attached

    @is_attached.setter
    @require_enabled
    def is_attached(self, value: bool, *, controller: LevelController):
        controller.is_attached = value

    @property
    @require_enabled
    def last_position(self, controller: LevelController) -> tuple[int, int]:
        return controller.last_position

    @property
    @require_enabled
    def actions(self, controller: LevelController) -> list[QAction]:
        return controller.actions

    @require_enabled
    def attach(self, generator_pointer: int, enemy_pointer: int, *, controller: LevelController):
        controller.attach(generator_pointer, enemy_pointer)

    @require_enabled
    def to_data(self, controller: LevelController) -> list[DataProtocol]:
        return controller.to_data()

    @require_enabled
    def load_m3l(self, m3l_data: bytearray, pathname: str, *, controller: LevelController):
        controller.load_m3l(m3l_data, pathname)

    @require_enabled
    def to_m3l(self, controller: LevelController) -> bytearray:
        return controller.to_m3l()

    @require_enabled
    def refresh(self, controller: LevelController):
        controller.refresh()

    @require_enabled
    def update(self, controller: LevelController):
        controller.update()

    @require_enabled
    def force_select(self, world: int, level: int, *, controller: LevelController):
        selection = select_by_world_and_level(world, level)
        controller.update_level(
            selection.display_information.name if selection.display_information.name is not None else "",
            selection.generator_pointer - 9,
            selection.enemy_pointer,
            selection.tileset,
        )

    @require_enabled
    def on_select(self, controller: LevelController):
        return controller.on_select()

    @property
    @require_enabled
    def safe_to_change(self, controller: LevelController) -> bool:
        return controller.safe_to_change

    @safe_to_change.setter
    @require_enabled
    def safe_to_change(self, value: bool, *, controller: LevelController):
        controller.safe_to_change = value

    @property
    @require_enabled
    def stable_changes(self, controller: LevelController) -> tuple[bool, str, str]:
        return controller.stable_changes

    @property
    def state(self) -> LevelByteData:
        if self.controller is None:
            raise NotImplementedError(f"{self.__class__.__name__} is not enabled")
        return self.controller.level_ref.state

    def do(self, new_state: LevelByteData) -> LevelByteData:
        if self.controller is None:
            raise NotImplementedError(f"{self.__class__.__name__} is not enabled")
        return self.controller.level_ref.do(new_state)

    @property
    def can_undo(self) -> bool:
        return self.controller is not None and self.controller.level_ref.can_undo

    def undo(self) -> LevelByteData:
        if self.controller is None:
            raise NotImplementedError(f"{self.__class__.__name__} is not enabled")
        return self.controller.level_ref.undo()

    @property
    def can_redo(self) -> bool:
        return self.controller is not None and self.controller.level_ref.can_redo

    def redo(self) -> LevelByteData:
        if self.controller is None:
            raise NotImplementedError(f"{self.__class__.__name__} is not enabled")
        return self.controller.level_ref.redo()

    @require_enabled
    def delete(self, controller: LevelController):
        controller.delete()

    @require_enabled
    def create_object_from_suggestion(self, position: tuple[int, int], *, controller: LevelController):
        if controller.suggested_object != -1:
            controller.place_object_from_dropdown(position)
        else:
            controller.create_object_at(*position)

    @require_enabled
    def to_foreground(self, controller: LevelController):
        controller.to_foreground()

    @require_enabled
    def to_background(self, controller: LevelController):
        controller.to_background()

    @property
    @require_enabled
    def title_suggestion(self, controller: LevelController) -> str:
        return controller.title_suggestion

    @property
    @require_enabled
    def screenshot(self, controller: LevelController) -> QPixmap:
        return controller.screenshot

    @require_enabled
    def cut(self, controller: LevelController):
        controller.cut()

    @require_enabled
    def copy(self, controller: LevelController):
        controller.copy()

    @require_enabled
    def paste(self, x: Optional[int] = None, y: Optional[int] = None, *, controller: LevelController):
        return controller.paste(x, y)

    @require_enabled
    def zoom_in(self, controller: LevelController):
        controller.zoom_in()

    @require_enabled
    def zoom_out(self, controller: LevelController):
        controller.zoom_out()

    @require_enabled
    def warp_to_alternative(self, controller: LevelController):
        controller.warp_to_alternative()

    @require_enabled
    def display_warnings(self, controller: LevelController):
        controller.display_warnings()

    @require_enabled
    def select_all(self, controller: LevelController):
        controller.select_all()

    @require_enabled
    def focus_selected(self, controller: LevelController):
        controller.focus_selected()

    @require_enabled
    def middle_mouse_release(self, position: QPoint, *, controller: LevelController):
        controller.middle_mouse_release(position)

    @require_enabled
    def display_block_viewer(self, controller: LevelController):
        controller.display_block_viewer()

    @require_enabled
    def display_palette_viewer(self, controller: LevelController):
        controller.display_palette_viewer()

    @require_enabled
    def display_autoscroll_editor(self, controller: LevelController):
        controller.display_autoscroll_editor()

    @require_enabled
    def display_header_editor(self, controller: LevelController):
        controller.display_header_editor()

    @require_enabled
    def display_jump_editor(self, controller: LevelController):
        controller.display_jump_editor()
