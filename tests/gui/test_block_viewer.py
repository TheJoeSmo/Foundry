import pytest

from foundry.gui.BlockViewer import BlockViewerController as BlockViewer


@pytest.fixture
def block_viewer(qtbot):
    block_viewer = BlockViewer(None)

    qtbot.addWidget(block_viewer)

    return block_viewer


def test_prev_tileset(block_viewer, qtbot):
    # GIVEN the block viewer at a specific object set, which is not the first
    block_viewer.next_os_action.trigger()

    current_tileset = block_viewer.bank_dropdown.currentIndex()
    first_tileset = 0

    assert current_tileset != first_tileset

    current_blocks_shown = block_viewer.view.grab().toImage()
    assert current_blocks_shown == block_viewer.view.grab().toImage()

    # WHEN the next object set action is triggered
    block_viewer.prev_os_action.trigger()

    # THEN the dropdown is updated and a different graphic is shown
    assert block_viewer.bank_dropdown.currentIndex() == current_tileset - 1
    assert block_viewer.view.grab() != current_blocks_shown


def test_next_tileset(block_viewer, qtbot):
    # GIVEN the block viewer at a specific object set, which is not the last
    current_tileset = block_viewer.bank_dropdown.currentIndex()
    last_tileset = block_viewer.bank_dropdown.count() - 1

    assert current_tileset != last_tileset

    current_blocks_shown = block_viewer.view.grab().toImage()
    assert current_blocks_shown == block_viewer.view.grab().toImage()

    # WHEN the next object set action is triggered
    block_viewer.next_os_action.trigger()

    # THEN the dropdown is updated and a different graphic is shown
    assert block_viewer.bank_dropdown.currentIndex() == current_tileset + 1
    assert block_viewer.view.grab() != current_blocks_shown


def test_zoom_out(block_viewer, qtbot):
    # GIVEN the block viewer at the default zoom level
    current_zoom_level = block_viewer.view.size().height() / 256

    # WHEN the zoom out action is called
    block_viewer.zoom_out_action.trigger()

    # THEN the new zoom level is 1 lower and the size of the bank is accordingly smaller
    new_zoom_level = block_viewer.view.size().height() / 256

    assert new_zoom_level == current_zoom_level - 1


def test_zoom_in(block_viewer, qtbot):
    # GIVEN the block viewer at the default zoom level
    current_zoom_level = block_viewer.view.size().height() / 256

    # WHEN the zoom in action is called
    block_viewer.zoom_in_action.trigger()

    # THEN the new zoom level is 1 higher and the size of the bank is accordingly larger
    new_zoom_level = block_viewer.view.size().height() / 256

    assert new_zoom_level == current_zoom_level + 1
