from __future__ import annotations

from collections.abc import Callable, Sequence
from logging import Logger, NullHandler, getLogger
from typing import Generic, Literal, TypeVar

from attr import attrs, evolve
from PySide6.QtCore import Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMainWindow,
    QTabBar,
    QWidget,
)

from foundry.core.geometry import Point, Size
from foundry.core.gui import (
    BaseModel,
    Border,
    DialogControl,
    DialogEvent,
    FocusEvent,
    Key,
    KeyEvent,
    KeySequence,
    Modifier,
    MouseEvent,
    MouseWheelEvent,
    Object,
    Selection,
    SignalInstance,
    UndoRedoForwarder,
    UndoRedoRoot,
)

_T = TypeVar("_T")

LOGGER_NAME: Literal["GUI"] = "GUI"

log: Logger = getLogger(LOGGER_NAME)
log.addHandler(NullHandler())


class MainWindow(UndoRedoRoot, QMainWindow):
    pass


class Dialog(UndoRedoRoot, Object, QDialog):
    pass


class Widget(UndoRedoForwarder, Object, QWidget):
    pass


class Label(UndoRedoForwarder, Object, QLabel):
    pass


class TabBar(Object, QTabBar):
    tab_selected: SignalInstance[int]

    @property
    def selected_index(self) -> int:
        return self.currentIndex()

    @selected_index.setter
    def selected_index(self, index: int) -> None:
        self.setCurrentIndex(index)

    def initialize_state(self, model: BaseModel, tabs: Sequence[str] | None = None, *args, **kwargs) -> None:
        super().initialize_state(model, *args, tab=tabs, **kwargs)
        self.currentChanged.connect(self.tab_selected.emit)  # type: ignore

        if tabs is None:
            return

        for tab in tabs:
            self.add_tab(tab)

    def add_tab(self, label: str) -> int:
        index = self.count()
        self.addTab(label)
        return index


class DialogOption(UndoRedoForwarder, Object, QDialogButtonBox, Generic[_T]):
    dialog_event: SignalInstance[DialogEvent]

    @property
    def accept_suggestion(self) -> _T | None:
        return None if self._accept_suggestion is None else self._accept_suggestion()

    @property
    def reject_suggestion(self) -> _T | None:
        return None if self._reject_suggestion is None else self._reject_suggestion()

    @property
    def help_suggestion(self) -> _T | None:
        return self._help_suggestion() if self._help_suggestion is not None else None

    def _determine_button_and_call_correct_event(self, button: QAbstractButton) -> None:
        if button is self.button(QDialogButtonBox.Apply):
            self.accept_event()
        elif button is self.button(QDialogButtonBox.Cancel):
            self.reject_event()
        else:
            self.help_event()

    def accept_event(self) -> None:
        self.dialog_event.emit(DialogEvent(DialogControl.ACCEPT, self.accept_suggestion))

    def reject_event(self) -> None:
        self.dialog_event.emit(DialogEvent(DialogControl.REJECT, self.reject_suggestion))

    def help_event(self) -> None:
        self.dialog_event.emit(DialogEvent(DialogControl.HELP, self.help_suggestion))

    def initialize_state(
        self,
        model: BaseModel,
        buttons: Sequence[DialogControl] | None = None,
        accept_suggestion: Callable[[], _T | None] | None = None,
        reject_suggestion: Callable[[], _T | None] | None = None,
        help_suggestion: Callable[[], _T | None] | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().initialize_state(model, *args, **kwargs)
        self._accept_suggestion = accept_suggestion
        self._reject_suggestion = reject_suggestion
        self._help_suggestion = help_suggestion

        if buttons is not None:
            for button in buttons:
                match button:
                    case DialogControl.ACCEPT:
                        self.addButton(QDialogButtonBox.Apply)
                    case DialogControl.REJECT:
                        self.addButton(QDialogButtonBox.Cancel)
                    case DialogControl.HELP:
                        self.addButton(QDialogButtonBox.HelpRole)

        self.clicked.connect(self._determine_button_and_call_correct_event)  # type: ignore


class FocusHandler(Object):
    started_focus: SignalInstance[FocusEvent]
    stopped_focus: SignalInstance[FocusEvent]

    def start_focus(self, event: FocusEvent) -> None:
        log.debug(f"{self} focused {event}")

    def stop_focus(self, event: FocusEvent) -> None:
        log.debug(f"{self} unfocused {event}")

    def focusInEvent(self, event: QFocusEvent) -> None:
        focus_event: FocusEvent = FocusEvent.from_qt(event)
        self.start_focus(focus_event)
        self.started_focus.emit(focus_event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        focus_event: FocusEvent = FocusEvent.from_qt(event)
        self.stop_focus(focus_event)
        self.stopped_focus.emit(focus_event)


class KeyHandler(FocusHandler):
    key_clicked: SignalInstance[KeyEvent]
    key_released: SignalInstance[KeyEvent]
    key_events: dict[KeySequence, tuple[Callable, Callable | None]]
    active_key_events: set[KeySequence]

    def _handle_undo_key_event(self) -> None:
        if self.can_undo:
            self.undo()  # type: ignore

    def _handle_redo_key_event(self) -> None:
        if self.can_redo:
            self.redo()  # type: ignore

    def initialize_state(self, model: BaseModel, track_keyboard: bool = False, *args, **kwargs) -> None:
        super().initialize_state(model, *args, track_keyboard=track_keyboard, **kwargs)
        if track_keyboard:
            self.setFocusPolicy(Qt.StrongFocus)  # type: ignore
        self.key_events = {}
        self.active_key_events = set()
        self.register_key_sequence(KeySequence(Key.Z, Modifier.CONTROL), self._handle_undo_key_event)
        self.register_key_sequence(KeySequence(Key.Z, Modifier.SHIFT, Modifier.CONTROL), self._handle_redo_key_event)

    def register_key_sequence(self, sequence: KeySequence, clicked: Callable, released: Callable | None = None) -> None:
        self.key_events |= {sequence: (clicked, released)}

    def stop_focus(self, event: FocusEvent) -> None:
        super().stop_focus(event)
        self.active_key_events.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key_event: KeyEvent = KeyEvent.from_qt(event)
        log.debug(f"{self} clicked {key_event}, {event}")
        self.key_clicked.emit(key_event)
        for key_sequence, (handle_key_event, _) in self.key_events.items():
            if key_sequence not in self.active_key_events and key_sequence.check(key_event):
                handle_key_event()
                if self.key_events[key_sequence][1] is not None:
                    self.active_key_events.add(key_sequence)
        return super().keyPressEvent(event)  # type: ignore

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        key_event: KeyEvent = KeyEvent.from_qt(event)
        log.debug(f"{self} released {key_event}")
        self.key_released.emit(key_event)
        finished_key_events: set[KeySequence] = set()
        for key_sequence in self.active_key_events:
            if key_sequence.check(key_event):
                if (handle_key_event_release := self.key_events[key_sequence][1]) is not None:
                    handle_key_event_release()
                finished_key_events.add(key_sequence)
        self.active_key_events -= finished_key_events

        return super().keyReleaseEvent(event)  # type: ignore


class MouseHandler(Object):
    cursor_moved: SignalInstance[MouseEvent]
    clicked: SignalInstance[MouseEvent]
    click_released: SignalInstance[MouseEvent]
    double_clicked: SignalInstance[MouseEvent]
    wheel_moved: SignalInstance[MouseWheelEvent]

    def initialize_state(self, model: BaseModel, track_mouse: bool = False, *args, **kwargs) -> None:
        super().initialize_state(model, *args, track_mouse=track_mouse, **kwargs)
        self.setMouseTracking(track_mouse)  # type: ignore

    def wheelEvent(self, event: QWheelEvent) -> None:
        wheel_event: MouseWheelEvent = MouseWheelEvent.from_qt(event)
        log.debug(f"{self} mouse wheel moved {wheel_event}")
        self.wheel_moved.emit(wheel_event)
        return super().wheelEvent(event)  # type: ignore

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        log.debug(f"{self} double clicked {mouse_event}")
        self.double_clicked.emit(mouse_event)
        return super().mouseDoubleClickEvent(event)  # type: ignore

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        log.debug(f"{self} moved {mouse_event}")
        self.cursor_moved.emit(mouse_event)
        return super().mouseMoveEvent(event)  # type: ignore

    def mousePressEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        log.debug(f"{self} pressed {mouse_event}")
        self.clicked.emit(mouse_event)
        return super().mousePressEvent(event)  # type: ignore

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        log.debug(f"{self} released {mouse_event}")
        self.click_released.emit(mouse_event)
        return super().mouseReleaseEvent(event)  # type: ignore


class GridMouseHandler(MouseHandler):
    grid_size_updated: SignalInstance[Size]
    grid_scale_updated: SignalInstance[Size]
    cursor_moved_grid: SignalInstance[MouseEvent]
    clicked_grid: SignalInstance[MouseEvent]
    click_released_grid: SignalInstance[MouseEvent]
    double_clicked_grid: SignalInstance[MouseEvent]

    @property
    def grid_size(self) -> Size:
        return Size(1, 1)

    @property
    def grid_scale(self) -> Size:
        return Size(1, 1)

    def _convert_to_grid_condition(self, event: MouseEvent) -> bool:
        return self.grid_size != Size(1, 1)

    def _convert_to_grid(self, event: MouseEvent) -> MouseEvent:
        grid_size: Size = self.grid_size
        if grid_size is None:
            log.warning(f"{self} does not have a have a defined grid size, unable to convert {event}")
            return event
        return evolve(
            event,
            local_position=Point(
                max(0, min(grid_size.width, event.local_position.x // self.grid_scale.width)),
                max(0, min(grid_size.height, event.local_position.y // self.grid_scale.height)),
            ),
        )

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        if self._convert_to_grid_condition(mouse_event):
            self.double_clicked_grid.emit(self._convert_to_grid(mouse_event))
        return super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        if self._convert_to_grid_condition(mouse_event):
            self.cursor_moved_grid.emit(self._convert_to_grid(mouse_event))
        return super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        if self._convert_to_grid_condition(mouse_event):
            self.clicked_grid.emit(self._convert_to_grid(mouse_event))
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        mouse_event: MouseEvent = MouseEvent.from_qt(event)
        if self._convert_to_grid_condition(mouse_event):
            self.click_released_grid.emit(self._convert_to_grid(mouse_event))
        return super().mouseReleaseEvent(event)


class MouseAggregator(Object):
    cursor_moved: SignalInstance[MouseEventAggregate]
    clicked: SignalInstance[MouseEventAggregate]
    click_released: SignalInstance[MouseEventAggregate]
    double_clicked: SignalInstance[MouseEventAggregate]
    wheel_moved: SignalInstance[MouseEventAggregate]

    @property
    def aggregates(self) -> Sequence[MouseHandler | MouseAggregator]:
        return []

    def aggregate(self, index: int, aggregate_widget: MouseHandler) -> Callable[[MouseEvent], MouseEventAggregate]:
        def aggregate(event: MouseEvent) -> MouseEventAggregate:
            return MouseEventAggregate(index, aggregate_widget, event)

        return aggregate

    def connect_aggregates(self) -> None:
        for index, aggregate in enumerate(self.aggregates):
            self.cursor_moved.link(aggregate.cursor_moved, self.aggregate(index, aggregate))
            self.clicked.link(aggregate.clicked, self.aggregate(index, aggregate))
            self.click_released.link(aggregate.click_released, self.aggregate(index, aggregate))
            self.double_clicked.link(aggregate.double_clicked, self.aggregate(index, aggregate))
            self.wheel_moved.link(aggregate.wheel_moved, self.aggregate(index, aggregate))


MouseAggregate = TypeVar("MouseAggregate", bound=MouseHandler | MouseAggregator)
MouseEvent_ = TypeVar("MouseEvent_")
MouseWheelEvent_ = TypeVar("MouseWheelEvent_")


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class MouseEventAggregate(Generic[MouseAggregate, MouseEvent_]):
    index: int
    aggregate: MouseAggregate
    event: MouseEvent_

    def __str__(self) -> str:
        return f"<{self.index}, {self.aggregate}, {self.event}>"


def generate_border(selection: Selection) -> Border:
    match selection:
        case Selection.PRIMARY:
            return Border.SOLID
        case Selection.SECONDARY:
            return Border.DASHED
        case Selection.TERTIARY:
            return Border.ROUND_DASHED
        case Selection.UNDO | Selection.REDO:
            return Border.ROUND_DASHED
        case _:
            return Border.NONE
