from bisect import bisect_right
from warnings import warn

from attr import evolve
from PySide6.QtCore import QMimeData, QSize, Signal, SignalInstance
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
    Qt,
    QWheelEvent,
)
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from foundry.core.geometry import Point, Size
from foundry.core.gui import Click, Edge, MouseEvent, MouseWheelEvent
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.ObjectLike import (
    EXPANDS_BOTH,
    EXPANDS_HORIZ,
    EXPANDS_VERT,
)
from foundry.game.gfx.objects.util import (
    decrement_type,
    increment_type,
    resize_level_object,
)
from foundry.game.level.Level import Level
from foundry.game.level.LevelRef import LevelRef
from foundry.game.level.WorldMap import WorldMap
from foundry.gui.ContextMenu import ContextMenu
from foundry.gui.LevelDrawer import LevelDrawer
from foundry.gui.SelectionSquare import SelectionSquare
from foundry.gui.settings import FileSettings, ResizeModes, UserSettings

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
    object_created: SignalInstance = Signal(object)  # type: ignore

    user_settings: UserSettings
    resizing_happened: bool
    dragging_happened: bool
    last_mouse_position: Point
    resize_obj_start_point: Point
    drag_start_point: Point
    selection_square: SelectionSquare

    def __init__(
        self,
        parent: QWidget | None,
        level: LevelRef,
        context_menu: ContextMenu,
        file_settings: FileSettings,
        user_settings: UserSettings,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        self.file_settings = file_settings
        self.user_settings = user_settings

        self.level_ref: LevelRef = level
        self.level_ref.data_changed.connect(self.update)

        self.context_menu = context_menu

        self.level_drawer = LevelDrawer(self.user_settings)

        self.zoom = 1
        self.block_length = Block.SIDE_LENGTH * self.zoom

        self.changed = False

        self.selection_square = SelectionSquare()

        self.mouse_mode = MODE_FREE

        self.last_mouse_position = Point(0, 0)

        self.drag_start_point = Point(0, 0)

        self.dragging_happened = True

        self.resize_mouse_start_x = 0
        self.resize_obj_start_point = Point(0, 0)

        self.resizing_happened = False

        # dragged in from the object toolbar
        self.currently_dragged_object: LevelObject | EnemyObject | None = None

        self.setWhatsThis(
            "<b>PydanticLevel View</b><br/>"
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

    def mousePressEvent(self, event: QMouseEvent):
        mouse_event: MouseEvent = MouseEvent.from_qt(event)

        if mouse_event.click == Click.LEFT_CLICK:
            self._on_left_mouse_button_down(mouse_event)
        elif mouse_event.click == Click.RIGHT_CLICK:
            self._on_right_mouse_button_down(mouse_event)

    def mouseMoveEvent(self, event: QMouseEvent):
        mouse_event: MouseEvent = MouseEvent.from_qt(event)

        if self.mouse_mode == MODE_DRAG:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._dragging(mouse_event)

        elif self.mouse_mode in RESIZE_MODES:
            previously_selected_objects: list[LevelObject | EnemyObject] = self.level_ref.selected_objects

            self._resizing(mouse_event)
            self.level_ref.selected_objects = previously_selected_objects

        elif self.selection_square.is_active:
            self._set_selection_end(mouse_event.local_point)

        elif self.user_settings.resize_mode == ResizeModes.RESIZE_LEFT_CLICK:
            self._set_cursor_for_position(mouse_event)

        object_under_cursor: LevelObject | EnemyObject | None = self.object_at(mouse_event.local_point)

        if self.user_settings.object_tooltip_enabled and object_under_cursor is not None:
            self.setToolTip(str(object_under_cursor))
        else:
            self.setToolTip("")
            QToolTip.hideText()

    def _set_cursor_for_position(self, event: MouseEvent):
        level_object: LevelObject | EnemyObject | None = self.object_at(event.local_point)

        if level_object is not None:
            if isinstance(level_object, LevelObject):
                is_resizable = not level_object.is_single_block
            else:
                is_resizable = False

            edges = self._cursor_on_edge_of_object(level_object, event.local_point)

            if is_resizable and edges:
                if edges == Edge.RightEdge and level_object.expands() & EXPANDS_HORIZ:
                    cursor = Qt.CursorShape.SizeHorCursor
                elif edges == Edge.BottomEdge and level_object.expands() & EXPANDS_VERT:
                    cursor = Qt.CursorShape.SizeVerCursor
                elif (level_object.expands() & EXPANDS_BOTH) == EXPANDS_BOTH:
                    cursor = Qt.CursorShape.SizeFDiagCursor
                else:
                    return

                if self.mouse_mode not in RESIZE_MODES:
                    self.setCursor(cursor)

                return

        if self.mouse_mode not in RESIZE_MODES:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _cursor_on_edge_of_object(
        self, level_object: LevelObject | EnemyObject, point: Point, edge_width: int = 4
    ) -> int:
        right = level_object.rect.right * self.block_length
        bottom = level_object.rect.bottom * self.block_length

        on_right_edge = point.x in range(right - edge_width, right)
        on_bottom_edge = point.y in range(bottom - edge_width, bottom)

        edges: int = 0
        if on_right_edge:
            edges |= Edge.RightEdge

        if on_bottom_edge:
            edges |= Edge.BottomEdge

        return edges

    def mouseReleaseEvent(self, event: QMouseEvent):
        mouse_event: MouseEvent = MouseEvent.from_qt(event)

        if mouse_event.click == Click.LEFT_CLICK:
            self._on_left_mouse_button_up(mouse_event)
        elif mouse_event.click == Click.RIGHT_CLICK:
            self._on_right_mouse_button_up(mouse_event)

    def wheelEvent(self, event: QWheelEvent):
        wheel_event: MouseWheelEvent = MouseWheelEvent.from_qt(event)

        if self.user_settings.object_scroll_enabled:
            obj_under_cursor: LevelObject | EnemyObject | None = self.object_at(wheel_event.local_point)

            if obj_under_cursor is None or isinstance(self.level_ref.level, WorldMap):
                return False

            # scrolling through the level could unintentionally change objects, if the cursor would wander onto them.
            # this is annoying (to me) so only change already selected objects
            if obj_under_cursor not in self.level_ref.selected_objects:
                return False

            self._change_object_on_mouse_wheel(wheel_event.local_point, wheel_event.delta)

        return self.user_settings.object_scroll_enabled

    @undoable
    def _change_object_on_mouse_wheel(self, point: Point, y_delta: int) -> None:
        obj: LevelObject | EnemyObject | None = self.object_at(point)

        if obj is None:
            return
        if y_delta > 0:
            increment_type(obj)
        else:
            decrement_type(obj)
        obj.selected = True

    def sizeHint(self) -> QSize:
        if not self.level_ref:
            return super().sizeHint()
        else:
            return (self.level_ref.level.size * self.block_length).to_qt()

    def update(self):
        self.resize(self.sizeHint())

        super().update()

    def _on_right_mouse_button_down(self, event: MouseEvent):
        if self.mouse_mode == MODE_DRAG:
            return

        self.last_mouse_position = self._to_level_point(event.local_point)
        if self._select_objects_on_click(event) and self.user_settings.resize_mode == ResizeModes.RESIZE_RIGHT_CLICK:
            self._try_start_resize(MODE_RESIZE_DIAG, event)

    def _try_start_resize(self, resize_mode: int, event: MouseEvent):
        if resize_mode not in RESIZE_MODES:
            return

        point: Point = self._to_level_point(event.local_point)
        self.mouse_mode: int = resize_mode

        self.resize_mouse_start_x = point.x

        obj: LevelObject | EnemyObject | None = self.object_at(point)
        if obj is not None:
            self.resize_obj_start_point = obj.position

    def _resizing(self, event: MouseEvent) -> None:
        self.resizing_happened = True

        if isinstance(self.level_ref.level, WorldMap):
            return

        point: Point = self._to_level_point(event.local_point)
        point_difference: Point = Point(0, 0)

        if self.mouse_mode & MODE_RESIZE_HORIZ:
            point_difference = evolve(point_difference, x=point.x - self.resize_obj_start_point.x)

        if self.mouse_mode & MODE_RESIZE_VERT:
            point_difference = evolve(point_difference, y=point.y - self.resize_obj_start_point.y)

        self.last_mouse_position = point

        selected_objects = self.get_selected_objects()

        for obj in selected_objects:
            resize_level_object(obj, point_difference)

            self.level_ref.level.changed = True

        self.update()

    def _on_right_mouse_button_up(self, event: MouseEvent):
        if self.resizing_happened:
            self._on_resize_happened_mouse_up(event)
        else:
            if self.get_selected_objects():
                menu = self.context_menu.as_object_menu()
            else:
                menu = self.context_menu.as_background_menu()

            self.context_menu.set_position(event.local_point.to_qt())
            menu.popup(event.global_point.to_qt())

        self.resizing_happened = False
        self.mouse_mode = MODE_FREE
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _stop_resize(self):
        self.level_ref.save_level_state()
        self.resizing_happened = False
        self.mouse_mode = MODE_FREE
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _on_left_mouse_button_down(self, event: MouseEvent):
        if self._select_objects_on_click(event):
            obj: LevelObject | EnemyObject | None = self.object_at(event.local_point)

            if obj is not None:
                edge: int = self._cursor_on_edge_of_object(obj, event.local_point)

                if self.user_settings.resize_mode == ResizeModes.RESIZE_LEFT_CLICK and edge:

                    self._try_start_resize(self._resize_mode_from_edge(edge), event)
                else:
                    self.drag_start_point = obj.position
        else:
            self._start_selection_square(event.local_point)

    def _on_resize_happened_mouse_up(self, event: MouseEvent) -> None:
        point: Point = self._to_level_point(event.local_point)
        if self.resize_mouse_start_x != point.x:
            self._stop_resize()

    @staticmethod
    def _resize_mode_from_edge(edge: int):
        mode = 0

        if edge & Edge.RightEdge:
            mode |= MODE_RESIZE_HORIZ

        if edge & Edge.BottomEdge:
            mode |= MODE_RESIZE_VERT

        return mode

    def _dragging(self, event: MouseEvent):
        self.dragging_happened = True

        point: Point = self._to_level_point(event.local_point)
        point_difference: Point = point - self.last_mouse_position

        self.last_mouse_position = point

        for obj in self.get_selected_objects():
            obj.move_by(point_difference)

            self.level_ref.level.changed = True

        self.update()

    def _on_left_mouse_button_up(self, event: MouseEvent):
        if self.resizing_happened:
            self._on_resize_happened_mouse_up(event)
        elif self.mouse_mode == MODE_DRAG and self.dragging_happened:
            obj: LevelObject | EnemyObject | None = self.object_at(event.local_point)

            if obj is not None:
                if self.drag_start_point != obj.position:
                    self._stop_drag()
                else:
                    self.dragging_happened = False
        else:
            self._stop_selection_square()

        self.mouse_mode = MODE_FREE
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _stop_drag(self):
        if self.dragging_happened:
            self.level_ref.save_level_state()

        self.dragging_happened = False

    def _select_objects_on_click(self, event: MouseEvent) -> bool:
        self.last_mouse_position = self._to_level_point(event.local_point)

        clicked_object: LevelObject | EnemyObject | None = self.object_at(event.local_point)
        clicked_on_background: bool = clicked_object is None

        if clicked_on_background and not event.shift:
            self._select_object(None)
        else:
            self.mouse_mode = MODE_DRAG

            selected_objects: list[LevelObject | EnemyObject] = self.get_selected_objects()
            if not selected_objects or (not event.shift and not event.control):
                self._select_object([clicked_object])
            else:
                self._select_object([clicked_object] + selected_objects)
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

    def _start_selection_square(self, point: Point):
        self.selection_square.start(point)

    def _set_selection_end(self, point: Point):
        if not self.selection_square.is_active:
            return

        self.selection_square.set_current_end(point)

        sel_rect = self.selection_square.get_adjusted_rect(Size(self.block_length, self.block_length))
        touched_objects: list[LevelObject | EnemyObject] = [
            obj for obj in self.level_ref.level.get_all_objects() if sel_rect.intersects(obj.rect)
        ]

        if touched_objects != self.level_ref.selected_objects:
            self._set_selected_objects(touched_objects)

        self.update()

    def _stop_selection_square(self):
        self.selection_square.stop()

        self.update()

    def select_all(self):
        self.select_objects(self.level_ref.level.get_all_objects())

    def _select_object(self, objects: list | None):
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

    def get_selected_objects(self) -> list[LevelObject | EnemyObject]:
        return self.level_ref.selected_objects

    def remove_selected_objects(self):
        for obj in self.level_ref.selected_objects:
            self.level_ref.level.remove_object(obj)

    def scroll_to_objects(self, objects: list[LevelObject]):
        if not objects:
            return

        min_x = min(obj.position.x for obj in objects) * self.block_length
        min_y = min(obj.position.y for obj in objects) * self.block_length

        self.parent().parent().ensureVisible(min_x, min_y)

    def level_safe_to_save(self) -> tuple[bool, str, str]:
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
            raise ValueError("PydanticLevel is None")

        enemies_end = self.level_ref.level.enemies_end

        levels_by_enemy_offset = sorted(self.file_settings.levels, key=lambda level: level.enemy_pointer)

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
            raise ValueError("PydanticLevel is None")

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

    def object_at(self, point: Point) -> LevelObject | EnemyObject | None:
        """
        Returns an object at the supplied point relative to the level view.

        Parameters
        ----------
        point : Point
            The point of the object to return.

        Returns
        -------
        LevelObject | EnemyObject | None
            The object, if one is found at the supplied point.
        """
        point = self._to_level_point(point)

        return self.level_ref.level.object_at(point)

    def _to_level_point(self, point: Point) -> Point:
        return Point(point.x // self.block_length, point.y // self.block_length)

    def create_object_at(self, point: Point, domain: int = 0, object_index: int = 0) -> None:
        self.level_ref.level.create_object_at(self._to_level_point(point), domain, object_index)
        self.update()

    def create_enemy_at(self, point: Point):
        self.level_ref.level.create_enemy_at(self._to_level_point(point))

    def add_object(self, domain: int, obj_index: int, point: Point, length: int, index: int = -1) -> None:
        self.level_ref.level.add_object(domain, obj_index, self._to_level_point(point), length, index)

    def add_enemy(self, enemy_index: int, point: Point, index: int) -> None:
        self.level_ref.level.add_enemy(enemy_index, self._to_level_point(point), index)

    def replace_object(self, obj: LevelObject, domain: int, obj_index: int, length: int | None):
        self.remove_object(obj)

        new_obj = self.level_ref.level.add_object(domain, obj_index, obj.position, length, obj.index_in_level)
        new_obj.selected = obj.selected

    def replace_enemy(self, old_enemy: EnemyObject, enemy_index: int):
        index_in_level = self.level_ref.level.index_of(old_enemy)

        self.remove_object(old_enemy)

        new_enemy: EnemyObject = self.level_ref.level.add_enemy(enemy_index, old_enemy.position, index_in_level)
        new_enemy.selected = old_enemy.selected

    def remove_object(self, obj):
        self.level_ref.level.remove_object(obj)

    def remove_jump(self, index: int):
        del self.level_ref.level.jumps[index]

        self.update()

    def paste_objects_at(self, objects: list[LevelObject | EnemyObject], origin: Point, point: Point | None = None):
        if point is None:
            point = self.last_mouse_position
        else:
            point = self._to_level_point(point)

        pasted_objects = []

        for obj in objects:
            offset_point = obj.position - origin

            try:
                pasted_objects.append(self.level_ref.level.paste_object_at(point + offset_point, obj))
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
        level_object: LevelObject | EnemyObject = self._object_from_mime_data(event.mimeData())
        level_object.position = self._to_level_point(Point.from_qt(event.position()))

        self.currently_dragged_object = level_object
        self.repaint()

    def dragLeaveEvent(self, event):
        self.currently_dragged_object = None

        self.repaint()

    @undoable
    def dropEvent(self, event: QDropEvent):
        point: Point = self._to_level_point(Point.from_qt(event.position()))
        level_object: LevelObject | EnemyObject = self._object_from_mime_data(event.mimeData())

        if isinstance(level_object, LevelObject):
            self.level_ref.level.add_object(level_object.domain, level_object.obj_index, point, None)
        else:
            self.level_ref.level.add_enemy(level_object.obj_index, point)

        event.accept()

        self.currently_dragged_object = None

        self.object_created.emit(level_object)
        self.level_ref.data_changed.emit()

    def _object_from_mime_data(self, mime_data: QMimeData) -> LevelObject | EnemyObject:
        object_type, *object_bytes = mime_data.data("application/level-object")

        if object_type == b"\x00":
            domain = int.from_bytes(object_bytes[0], "big") >> 5
            object_index = int.from_bytes(object_bytes[2], "big")

            return self.level_ref.level.object_factory.from_properties(domain, object_index, Point(0, 0), None, 999)
        else:
            enemy_id = int.from_bytes(object_bytes[0], "big")

            return self.level_ref.level.enemy_item_factory.from_properties(enemy_id, Point(0, 0))

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        if self.level_ref is None:
            return

        self.level_drawer.block_length = self.block_length

        self.level_drawer.draw(painter, self.level_ref.level)

        self.selection_square.draw(painter)

        if self.currently_dragged_object is not None:
            self.currently_dragged_object.draw(painter, self.block_length, self.user_settings.block_transparency)
