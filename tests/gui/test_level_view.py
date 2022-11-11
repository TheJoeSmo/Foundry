import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import Qt, QWheelEvent

from foundry.core.geometry import Point
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.level.util import DisplayInformation
from foundry.game.level.util import Level as LevelInformationState
from foundry.gui.HeaderEditor import (
    HeaderEditor,
    header_state_to_level_header,
    level_to_header_state,
)
from foundry.gui.LevelView import LevelView
from foundry.gui.settings import FileSettings
from foundry.smb3parse.objects.tileset import PLAINS_OBJECT_SET


@pytest.fixture
def empty_file_settings() -> FileSettings:
    return FileSettings(levels=[LevelInformationState(DisplayInformation("Test", "Desc.", []), 0, 0, 1, 30, 15)])


@pytest.fixture
def level_view(main_window, qtbot):
    return main_window.level_view


@pytest.mark.parametrize(
    "coordinates, obj_index, domain, tileset_number",
    [
        (Point(0, 0), 0x03, 0x00, PLAINS_OBJECT_SET),  # background symbols
        (Point(361, 283), 0xE2, 0x00, PLAINS_OBJECT_SET),  # background cloud
        (Point(233, 409), 0x72, 0x00, None),  # goomba
    ],
)
def test_object_at(level_view: LevelView, qtbot, coordinates, obj_index, domain, tileset_number):
    level_object = level_view.object_at(coordinates)

    assert level_object
    assert level_object.obj_index == obj_index
    if isinstance(level_object, LevelObject):
        assert level_object.domain == domain
        assert level_object.tileset.number == tileset_number


def test_level_larger(level_view, empty_file_settings: FileSettings):
    # GIVEN level_view and a header editor
    header_editor = HeaderEditor(
        None, level_to_header_state(level_view.level_ref.level, empty_file_settings), empty_file_settings
    )

    def update_level_header(state):
        level_view.level_ref.level.header_bytes = header_state_to_level_header(state)
        level_view.level_ref.level._parse_header()
        level_view.level_ref.data_changed.emit()

    header_editor.state_changed.connect(update_level_header)

    # INCREASE header size
    original_size = level_view.size()
    header_editor.level_length += 1

    # THEN the level_view should be larger as well
    assert level_view.size().width() > original_size.width()
    assert level_view.size().height() >= original_size.height()


@pytest.mark.parametrize("scroll_amount", [0, 100])
@pytest.mark.parametrize("coordinates", [Point(233, 409)])  # goomba
@pytest.mark.parametrize("wheel_delta, type_change", [(10, 1), (-10, -1)])  # scroll wheel up  # scroll wheel down
def test_wheel_event(scroll_amount, coordinates, wheel_delta, type_change, main_window, qtbot):
    # GIVEN a level view and a cursor point over an object
    level_view = main_window.level_view
    object_under_cursor = level_view.object_at(coordinates)
    original_type = object_under_cursor.type

    main_window.user_settings.object_scroll_enabled = True

    # WHEN level view is scrolled horizontally, the object is selected and the scroll wheel is used on it
    main_window.scroll_panel.horizontalScrollBar().setMaximum(level_view.width())
    main_window.scroll_panel.horizontalScrollBar().setValue(scroll_amount)

    main_window.show()
    qtbot.waitExposed(main_window)

    main_window.hide()

    qtbot.mouseClick(level_view, Qt.MouseButton.LeftButton, pos=QPoint(coordinates.x, coordinates.y))
    assert object_under_cursor.selected

    event = QWheelEvent(
        QPoint(coordinates.x, coordinates.y),
        QPoint(-1, -1),
        QPoint(0, wheel_delta),
        QPoint(0, wheel_delta),
        Qt.MouseButton.LeftButton,
        Qt.NoModifier,
        Qt.ScrollEnd,
        False,
    )

    assert level_view.wheelEvent(event)

    # THEN the type of the object should have changed
    new_type = level_view.object_at(coordinates).type

    assert new_type == original_type + type_change, (original_type, new_type)
