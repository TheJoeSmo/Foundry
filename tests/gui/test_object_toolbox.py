import pytest
from PySide6.QtWidgets import QVBoxLayout, QWidget

from foundry.core.geometry import Point
from foundry.game.gfx.objects.LevelObjectFactory import LevelObjectFactory
from foundry.gui.ObjectIcon import ObjectIcon
from foundry.gui.ObjectToolBox import ObjectToolBox
from foundry.smb3parse.objects.tileset import PLAINS_GRAPHICS_SET, PLAINS_OBJECT_SET


@pytest.mark.parametrize("domain, obj_index", [(0, 0xA0), (0, 0xA8)])
def test_object_icon(domain, obj_index, qtbot):
    factory: LevelObjectFactory = LevelObjectFactory(PLAINS_OBJECT_SET, PLAINS_GRAPHICS_SET, 0, [], False, True)

    level_object = factory.from_properties(domain, obj_index, Point(0, 0), None, 0)

    widget = QWidget()
    widget.setLayout(QVBoxLayout())

    widget.layout().addStretch()
    widget.layout().addWidget(ObjectIcon(None, level_object))
    widget.layout().addStretch()

    widget.show()
    widget.adjustSize()
    qtbot.waitExposed(widget)


def test_object_toolbar(qtbot):
    toolbar = ObjectToolBox(None)

    toolbar.update()

    toolbar.show()
