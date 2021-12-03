from bisect import bisect_right
from typing import List, Optional, Tuple, Union
from warnings import warn

from PySide6.QtCore import QMimeData, QPoint, QSize, Signal, SignalInstance
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
    Qt,
    QWheelEvent,
)
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from foundry.core.Position import Position
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.ObjectLike import (
    EXPANDS_BOTH,
    EXPANDS_HORIZ,
    EXPANDS_VERT,
)
from foundry.game.level.Level import Level
from foundry.game.level.LevelRef import LevelRef
from foundry.game.level.WorldMap import WorldMap
from foundry.gui.ContextMenu import ContextMenu
from foundry.gui.LevelDrawer import LevelDrawer
from foundry.gui.SelectionSquare import SelectionSquare
from foundry.gui.settings import RESIZE_LEFT_CLICK, RESIZE_RIGHT_CLICK, SETTINGS

HIGHEST_ZOOM_LEVEL = 8  # on linux, at least
LOWEST_ZOOM_LEVEL = 1 / 16  # on linux, but makes sense with 16x16 blocks

# mouse modes

MODE_FREE = 0
MODE_DRAG = 1
MODE_RESIZE_HORIZ = 2
MODE_RESIZE_VERT = 4
MODE_RESIZE_DIAG = MODE_RESIZE_HORIZ | MODE_RESIZE_VERT
RESIZE_MODES = [MODE_RESIZE_HORIZ, MODE_RESIZE_VERT, MODE_RESIZE_DIAG]


def undoable(func):
    def wrapped(self, *args):
        func(self, *args)
        self.level_ref.save_level_state()

    return wrapped


class LevelView(QWidget):
    objects_selected: SignalInstance = Signal(object)  # type: ignore

    def __init__(self, parent: Optional[QWidget], level: LevelRef, context_menu: ContextMenu):
        super(LevelView, self).__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        self.level_ref: LevelRef = level
        self.level_ref.data_changed.connect(self.update)

        self.context_menu = context_menu

        self.level_drawer = LevelDrawer()

        self.draw_grid = SETTINGS["draw_grid"]
        self.draw_jumps = SETTINGS["draw_jumps"]
        self.draw_expansions = SETTINGS["draw_expansion"]
        self.draw_mario = SETTINGS["draw_mario"]
        self.transparency = SETTINGS["block_transparency"]
        self.draw_jumps_on_objects = SETTINGS["draw_jump_on_objects"]
        self.draw_items_in_blocks = SETTINGS["draw_items_in_blocks"]
        self.draw_invisible_items = SETTINGS["draw_invisible_items"]
        self.draw_autoscroll = SETTINGS["draw_autoscroll"]

        self.zoom = 1
        self.block_length = Block.SIDE_LENGTH * self.zoom

        self.changed = False

        self.selection_square = SelectionSquare()

        self.mouse_mode = MODE_FREE

        self.last_mouse_position = 0, 0

        self.drag_start_point = 0, 0

        self.dragging_happened = True

        self.resize_mouse_start_x = 0
        self.resize_obj_start_point = 0, 0

        self.resizing_happened = False

        # dragged in from the object toolbar
        self.currently_dragged_object: Optional[Union[LevelObject, EnemyObject]] = None

        self.setWhatsThis(
            "<b>Level View</b><br/>"
            "This renders the level as it would appear in game plus additional information, that can be "
            "toggled in the View menu.<br/>"
            "It supports selecting multiple objects, moving, copy/pasting and resizing them using the "
            "mouse or the usual keyboard shortcuts.<br/>"
            "There are still occasional rendering errors, or small inconsistencies. If you find them, "
            "please report the kind of object (name or values in the SpinnerPanel) and the level or "
            "object set they appear in, in the discord and @Michael or on the github page under Help."
            "<br/><br/>"
            ""
            "If all else fails, click the play button up top to see your level in game in seconds."
        )

    @property
    def transparency(self):
        return self.level_drawer.transparency

    @transparency.setter
    def transparency(self, value):
        self.level_drawer.transparency = value

    @property
    def draw_grid(self):
        return self.level_drawer.draw_grid

    @draw_grid.setter
    def draw_grid(self, value):
        self.level_drawer.draw_grid = value

    @property
    def draw_jumps(self):
        return self.level_drawer.draw_jumps

    @draw_jumps.setter
    def draw_jumps(self, value):
        self.level_drawer.draw_jumps = value

    @property
    def draw_mario(self):
        return self.level_drawer.draw_mario

    @draw_mario.setter
    def draw_mario(self, value):
        self.level_drawer.draw_mario = value

    @property
    def draw_expansions(self):
        return self.level_drawer.draw_expansions

    @draw_expansions.setter
    def draw_expansions(self, value):
        self.level_drawer.draw_expansions = value

    @property
    def draw_jumps_on_objects(self):
        return self.level_drawer.draw_jumps_on_objects

    @draw_jumps_on_objects.setter
    def draw_jumps_on_objects(self, value):
        self.level_drawer.draw_jumps_on_objects = value

    @property
    def draw_items_in_blocks(self):
        return self.level_drawer.draw_items_in_blocks

    @draw_items_in_blocks.setter
    def draw_items_in_blocks(self, value):
        self.level_drawer.draw_items_in_blocks = value

    @property
    def draw_invisible_items(self):
        return self.level_drawer.draw_invisible_items

    @draw_invisible_items.setter
    def draw_invisible_items(self, value):
        self.level_drawer.draw_invisible_items = value

    @property
    def draw_autoscroll(self):
        return self.level_drawer.draw_autoscroll

    @draw_autoscroll.setter
    def draw_autoscroll(self, value):
        self.level_drawer.draw_autoscroll = value

    def mousePressEvent(self, event: QMouseEvent):
        pressed_button = event.button()

        if pressed_button == Qt.LeftButton:
            self._on_left_mouse_button_down(event)
        elif pressed_button == Qt.RightButton:
            self._on_right_mouse_button_down(event)
        else:
            return super(LevelView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouse_mode == MODE_DRAG:
            self.setCursor(Qt.ClosedHandCursor)
            self._dragging(event)

        elif self.mouse_mode in RESIZE_MODES:
            previously_selected_objects = self.level_ref.selected_objects

            self._resizing(event)

            self.level_ref.selected_objects = previously_selected_objects

        elif self.selection_square.active:
            self._set_selection_end(event.position().toPoint())

        elif SETTINGS["resize_mode"] == RESIZE_LEFT_CLICK:
            self._set_cursor_for_position(event)

        x, y = event.position().toPoint().toTuple()

        object_under_cursor = self.object_at(x, y)

        if SETTINGS["object_tooltip_enabled"] and object_under_cursor is not None:
            self.setToolTip(str(object_under_cursor))
        else:
            self.setToolTip("")
            QToolTip.hideText()

        return super(LevelView, self).mouseMoveEvent(event)

    def _set_cursor_for_position(self, event: QMouseEvent):
        level_object = self.object_at(*event.position().toTuple())

        if level_object is not None:
            if isinstance(level_object, LevelObject):
                is_resizable = not level_object.is_single_block
            else:
                is_resizable = False

            edges = self._cursor_on_edge_of_object(level_object, event.position().toPoint())

            if is_resizable and edges:
                if edges == Qt.RightEdge and level_object.expands() & EXPANDS_HORIZ:
                    cursor = Qt.SizeHorCursor
                elif edges == Qt.BottomEdge and level_object.expands() & EXPANDS_VERT:
                    cursor = Qt.SizeVerCursor
                elif (level_object.expands() & EXPANDS_BOTH) == EXPANDS_BOTH:
                    cursor = Qt.SizeFDiagCursor
                else:
                    return

                if self.mouse_mode not in RESIZE_MODES:
                    self.setCursor(cursor)

                return

        if self.mouse_mode not in RESIZE_MODES:
            self.setCursor(Qt.ArrowCursor)

    def _cursor_on_edge_of_object(
        self, level_object: Union[LevelObject, EnemyObject], pos: QPoint, edge_width: int = 4
    ):
        right = (level_object.get_rect().left() + level_object.get_rect().width()) * self.block_length
        bottom = (level_object.get_rect().top() + level_object.get_rect().height()) * self.block_length

        on_right_edge = pos.x() in range(right - edge_width, right)
        on_bottom_edge = pos.y() in range(bottom - edge_width, bottom)

        edges = 0

        if on_right_edge:
            edges |= Qt.RightEdge

        if on_bottom_edge:
            edges |= Qt.BottomEdge

        return edges

    def mouseReleaseEvent(self, event: QMouseEvent):
        released_button = event.button()

        if released_button == Qt.LeftButton:
            self._on_left_mouse_button_up(event)
        elif released_button == Qt.RightButton:
            self._on_right_mouse_button_up(event)
        else:
            super(LevelView, self).mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if SETTINGS["object_scroll_enabled"]:
            x, y = event.position().toPoint().toTuple()

            obj_under_cursor = self.object_at(x, y)

            if obj_under_cursor is None:
                return False

            if isinstance(self.level_ref.level, WorldMap):
                return False

            # scrolling through the level could unintentionally change objects, if the cursor would wander onto them.
            # this is annoying (to me) so only change already selected objects
            if obj_under_cursor not in self.level_ref.selected_objects:
                return False

            self._change_object_on_mouse_wheel(event.position().toPoint(), event.angleDelta().y())

            return True
        else:
            super(LevelView, self).wheelEvent(event)
            return False

    @undoable
    def _change_object_on_mouse_wheel(self, cursor_position: QPoint, y_delta: int):
        x, y = cursor_position.x(), cursor_position.y()

        obj = self.object_at(x, y)

        if obj is None:
            return
        obj.increment_type() if y_delta > 0 else obj.decrement_type()
        obj.selected = True

    def sizeHint(self) -> QSize:
        if not self.level_ref:
            return super(LevelView, self).sizeHint()
        else:
            width, height = self.level_ref.level.size

            return QSize(width * self.block_length, height * self.block_length)

    def update(self):
        self.resize(self.sizeHint())

        super(LevelView, self).update()

    def _on_right_mouse_button_down(self, event: QMouseEvent):
        if self.mouse_mode == MODE_DRAG:
            return

        x, y = event.position().toPoint().toTuple()
        level_x, level_y = self._to_level_point(x, y)

        self.last_mouse_position = level_x, level_y

        if self._select_objects_on_click(event) and SETTINGS["resize_mode"] == RESIZE_RIGHT_CLICK:
            self._try_start_resize(MODE_RESIZE_DIAG, event)

    def _try_start_resize(self, resize_mode: int, event: QMouseEvent):
        if resize_mode not in RESIZE_MODES:
            return

        x, y = event.position().toPoint().toTuple()
        level_x, level_y = self._to_level_point(x, y)

        self.mouse_mode = resize_mode

        self.resize_mouse_start_x = level_x

        obj = self.object_at(x, y)

        if obj is not None:
            self.resize_obj_start_point = obj.position.x, obj.position.y

    def _resizing(self, event: QMouseEvent):
        self.resizing_happened = True

        if isinstance(self.level_ref.level, WorldMap):
            return

        x, y = event.position().toPoint().toTuple()

        level_x, level_y = self._to_level_point(x, y)

        dx = dy = 0

        if self.mouse_mode & MODE_RESIZE_HORIZ:
            dx = level_x - self.resize_obj_start_point[0]

        if self.mouse_mode & MODE_RESIZE_VERT:
            dy = level_y - self.resize_obj_start_point[1]

        self.last_mouse_position = level_x, level_y

        selected_objects = self.get_selected_objects()

        for obj in selected_objects:
            obj.resize_by(dx, dy)

            self.level_ref.level.changed = True

        self.update()

    def _on_right_mouse_button_up(self, event: QMouseEvent):
        if self.resizing_happened:
            self._on_resize_happened_mouse_up(event)
        else:
            if self.get_selected_objects():
                menu = self.context_menu.as_object_menu()
            else:
                menu = self.context_menu.as_background_menu()

            self.context_menu.set_position(event.position().toPoint())

            menu_pos = self.mapToGlobal(event.position().toPoint())

            menu.popup(menu_pos)

        self.resizing_happened = False
        self.mouse_mode = MODE_FREE
        self.setCursor(Qt.ArrowCursor)

    def _stop_resize(self):
        self.level_ref.save_level_state()
        self.resizing_happened = False
        self.mouse_mode = MODE_FREE
        self.setCursor(Qt.ArrowCursor)

    def _on_left_mouse_button_down(self, event: QMouseEvent):
        if self._select_objects_on_click(event):
            x, y = event.position().toPoint().toTuple()

            obj = self.object_at(x, y)

            if obj is not None:
                edge = self._cursor_on_edge_of_object(obj, event.position().toPoint())

                if SETTINGS["resize_mode"] == RESIZE_LEFT_CLICK and edge:

                    self._try_start_resize(self._resize_mode_from_edge(edge), event)
                else:
                    self.drag_start_point = obj.position.x, obj.position.y
        else:
            self._start_selection_square(event.position().toPoint())

    def _on_resize_happened_mouse_up(self, event: QMouseEvent):
        x, y = event.pos().x(), event.pos().y()

        resize_end_x, _ = self._to_level_point(x, y)
        if self.resize_mouse_start_x != resize_end_x:
            self._stop_resize()

    @staticmethod
    def _resize_mode_from_edge(edge: int):
        mode = 0

        if edge & Qt.RightEdge:
            mode |= MODE_RESIZE_HORIZ

        if edge & Qt.BottomEdge:
            mode |= MODE_RESIZE_VERT

        return mode

    def _dragging(self, event: QMouseEvent):
        self.dragging_happened = True

        x, y = event.position().toPoint().toTuple()

        level_x, level_y = self._to_level_point(x, y)

        dx = level_x - self.last_mouse_position[0]
        dy = level_y - self.last_mouse_position[1]

        self.last_mouse_position = level_x, level_y

        selected_objects = self.get_selected_objects()

        for obj in selected_objects:
            obj.move_by(dx, dy)

            self.level_ref.level.changed = True

        self.update()

    def _on_left_mouse_button_up(self, event: QMouseEvent):
        if self.resizing_happened:
            self._on_resize_happened_mouse_up(event)
        elif self.mouse_mode == MODE_DRAG and self.dragging_happened:
            x, y = event.position().toPoint().toTuple()

            obj = self.object_at(x, y)

            if obj is not None:
                drag_end_point = obj.position.x, obj.position.y

                if self.drag_start_point != drag_end_point:
                    self._stop_drag()
                else:
                    self.dragging_happened = False
        else:
            self._stop_selection_square()

        self.mouse_mode = MODE_FREE
        self.setCursor(Qt.ArrowCursor)

    def _stop_drag(self):
        if self.dragging_happened:
            self.level_ref.save_level_state()

        self.dragging_happened = False

    def _select_objects_on_click(self, event: QMouseEvent) -> bool:
        x, y = event.position().toPoint().toTuple()
        level_x, level_y = self._to_level_point(x, y)

        self.last_mouse_position = level_x, level_y

        clicked_object = self.object_at(x, y)
        clicked_on_background = clicked_object is None

        if clicked_on_background and not event.modifiers() & Qt.ShiftModifier:
            self._select_object(None)
        else:
            self.mouse_mode = MODE_DRAG

            selected_objects = self.get_selected_objects()
            nothing_selected = not selected_objects
            if nothing_selected or (
                not event.modifiers() & Qt.ShiftModifier and not event.modifiers() & Qt.ControlModifier
            ):
                self._select_object([clicked_object])
            else:
                self._select_object([clicked_object] + selected_objects)  # type: ignore

        return not clicked_on_background

    def _set_zoom(self, zoom):
        if not (LOWEST_ZOOM_LEVEL <= zoom <= HIGHEST_ZOOM_LEVEL):
            return

        self.zoom = zoom
        self.block_length = int(Block.SIDE_LENGTH * self.zoom)

        self.update()

    def zoom_out(self):
        self._set_zoom(self.zoom / 2)

    def zoom_in(self):
        self._set_zoom(self.zoom * 2)

    def _start_selection_square(self, position):
        self.selection_square.start(position)

    def _set_selection_end(self, position):
        if not self.selection_square.is_active():
            return

        self.selection_square.set_current_end(position)

        sel_rect = self.selection_square.get_adjusted_rect(self.block_length, self.block_length)

        touched_objects = [obj for obj in self.level_ref.level.get_all_objects() if sel_rect.intersects(obj.get_rect())]

        if touched_objects != self.level_ref.selected_objects:
            self._set_selected_objects(touched_objects)

        self.update()

    def _stop_selection_square(self):
        self.selection_square.stop()

        self.update()

    def select_all(self):
        self.select_objects(self.level_ref.level.get_all_objects())

    def _select_object(self, objects: Optional[list]):
        if objects is not None:
            self.select_objects(objects)
            self.objects_selected.emit(objects)
        else:
            self.select_objects([])
            self.objects_selected.emit([])

    def select_objects(self, objects):
        self._set_selected_objects(objects)

        self.update()

    def _set_selected_objects(self, objects):
        if self.level_ref.selected_objects == objects:
            return

        self.level_ref.selected_objects = objects

    def get_selected_objects(self) -> List[Union[LevelObject, EnemyObject]]:
        return self.level_ref.selected_objects

    def remove_selected_objects(self):
        for obj in self.level_ref.selected_objects:
            self.level_ref.level.remove_object(obj)

    def scroll_to_objects(self, objects: List[LevelObject]):
        if not objects:
            return

        min_x = min([obj.position.x for obj in objects]) * self.block_length
        min_y = min([obj.position.y for obj in objects]) * self.block_length

        self.parent().parent().ensureVisible(min_x, min_y)

    def level_safe_to_save(self) -> Tuple[bool, str, str]:
        is_safe = True
        reason = ""
        additional_info = ""

        if self.level_ref.level.too_many_level_objects():
            level = self._cuts_into_other_objects()

            is_safe = False
            reason = "Too many level objects."

            if level:
                additional_info = f"Would overwrite data of '{level}'."
            else:
                additional_info = (
                    "It wouldn't overwrite another level, " "but it might still overwrite other important data."
                )

        elif self.level_ref.level.too_many_enemies_or_items():
            level = self._cuts_into_other_enemies()

            is_safe = False
            reason = "Too many enemies or items."

            if level:
                additional_info = f"Would probably overwrite enemy/item data of '{level}'."
            else:
                additional_info = (
                    "It wouldn't overwrite enemy/item data of another level, "
                    "but it might still overwrite other important data."
                )

        return is_safe, reason, additional_info

    def _cuts_into_other_enemies(self) -> str:
        if self.level_ref is None:
            raise ValueError("Level is None")

        enemies_end = self.level_ref.level.enemies_end

        levels_by_enemy_offset = sorted(Level.offsets, key=lambda level: level.enemy_pointer)

        level_index = bisect_right([level.enemy_pointer for level in levels_by_enemy_offset], enemies_end) - 1

        found_level = levels_by_enemy_offset[level_index]

        if found_level.enemy_pointer == self.level_ref.level.enemy_offset:
            return ""
        else:
            return (
                f"World {found_level.display_information.locations[0].world} - {found_level.display_information.name}"
            )

    def _cuts_into_other_objects(self) -> str:
        if self.level_ref is None:
            raise ValueError("Level is None")

        end_of_level_objects = self.level_ref.level.objects_end

        level_index = (
            bisect_right(
                [level.generator_pointer - Level.HEADER_LENGTH for level in Level.sorted_offsets], end_of_level_objects
            )
            - 1
        )

        found_level = Level.sorted_offsets[level_index]

        if found_level.generator_pointer == self.level_ref.level.object_offset:
            return ""
        else:
            return (
                f"World {found_level.display_information.locations[0].world} - {found_level.display_information.name}"
            )

    def add_jump(self):
        self.level_ref.level.add_jump()

    def object_at(self, x: int, y: int) -> Optional[Union[LevelObject, EnemyObject]]:
        """
        Returns an enemy or level object at the position. The x and y is relative to the View (for example, when you
        receive a mouse event) and will be converted into level coordinates internally.

        :param int x: X position on the View, where the object is queried at.
        :param int y: Y position on the View, where the object is queried at.

        :return: An enemy/level object, or None, if none is at the position.
        """
        level_x, level_y = self._to_level_point(x, y)

        return self.level_ref.level.object_at(level_x, level_y)

    def _to_level_point(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        level_x = screen_x // self.block_length
        level_y = screen_y // self.block_length

        return level_x, level_y

    def create_object_at(self, x: int, y: int, domain: int = 0, object_index: int = 0):
        level_x, level_y = self._to_level_point(x, y)

        self.level_ref.level.create_object_at(int(level_x), int(level_y), domain, object_index)

        self.update()

    def create_enemy_at(self, x: int, y: int):
        level_x, level_y = self._to_level_point(x, y)

        self.level_ref.level.create_enemy_at(level_x, level_y)

    def add_object(self, domain: int, obj_index: int, x: int, y: int, length: int, index: int = -1):
        level_x, level_y = self._to_level_point(x, y)

        self.level_ref.level.add_object(domain, obj_index, level_x, level_y, length, index)

    def add_enemy(self, enemy_index: int, x: int, y: int, index: int):
        level_x, level_y = self._to_level_point(x, y)

        self.level_ref.level.add_enemy(enemy_index, level_x, level_y, index)

    def replace_object(self, obj: LevelObject, domain: int, obj_index: int, length: Optional[int]):
        self.remove_object(obj)

        new_obj = self.level_ref.level.add_object(
            domain, obj_index, obj.position.x, obj.position.y, length, obj.index_in_level
        )
        new_obj.selected = obj.selected

    def replace_enemy(self, old_enemy: EnemyObject, enemy_index: int):
        index_in_level = self.level_ref.level.index_of(old_enemy)

        self.remove_object(old_enemy)

        new_enemy = self.level_ref.level.add_enemy(
            enemy_index, old_enemy.position.x, old_enemy.position.y, index_in_level
        )

        new_enemy.selected = old_enemy.selected

    def remove_object(self, obj):
        self.level_ref.level.remove_object(obj)

    def remove_jump(self, index: int):
        del self.level_ref.level.jumps[index]

        self.update()

    def paste_objects_at(
        self,
        paste_data: Tuple[List[Union[LevelObject, EnemyObject]], Tuple[int, int]],
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):
        if x is None or y is None:
            level_x, level_y = self.last_mouse_position
        else:
            level_x, level_y = self._to_level_point(x, y)

        objects, origin = paste_data

        ori_x, ori_y = origin

        pasted_objects = []

        for obj in objects:
            offset_x, offset_y = obj.position.x - ori_x, obj.position.y - ori_y

            try:
                pasted_objects.append(self.level_ref.level.paste_object_at(level_x + offset_x, level_y + offset_y, obj))
            except ValueError:
                warn("Tried pasting outside of level.", RuntimeWarning)

        self.select_objects(pasted_objects)

    def get_object_names(self):
        return self.level_ref.level.get_object_names()

    def make_screenshot(self) -> QPixmap:
        assert self.level_ref is not None

        return self.grab()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/level-object"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        x, y = self._to_level_point(*event.position().toPoint().toTuple())

        level_object = self._object_from_mime_data(event.mimeData())

        level_object.position = Position(x, y)

        self.currently_dragged_object = level_object

        self.repaint()

    def dragLeaveEvent(self, event):
        self.currently_dragged_object = None

        self.repaint()

    @undoable
    def dropEvent(self, event):
        x, y = self._to_level_point(*event.position().toPoint().toTuple())

        level_object = self._object_from_mime_data(event.mimeData())

        if isinstance(level_object, LevelObject):
            self.level_ref.level.add_object(level_object.domain, level_object.obj_index, x, y, None)
        else:
            self.level_ref.level.add_enemy(level_object.obj_index, x, y)

        event.accept()

        self.currently_dragged_object = None

        self.level_ref.data_changed.emit()

    def _object_from_mime_data(self, mime_data: QMimeData) -> Union[LevelObject, EnemyObject]:
        object_type, *object_bytes = mime_data.data("application/level-object")

        if object_type == b"\x00":
            domain = int.from_bytes(object_bytes[0], "big") >> 5
            object_index = int.from_bytes(object_bytes[2], "big")

            return self.level_ref.level.object_factory.from_properties(domain, object_index, 0, 0, None, 999)
        else:
            enemy_id = int.from_bytes(object_bytes[0], "big")

            return self.level_ref.level.enemy_item_factory.from_properties(enemy_id, 0, 0)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        if self.level_ref is None:
            return

        self.level_drawer.block_length = self.block_length

        self.level_drawer.draw(painter, self.level_ref.level)

        self.selection_square.draw(painter)

        if self.currently_dragged_object is not None:
            self.currently_dragged_object.draw(painter, self.block_length, self.transparency)
