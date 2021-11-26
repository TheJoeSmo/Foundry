from typing import Optional

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QMainWindow, QToolBar, QWidget


def create_toolbar(
    parent: QMainWindow, name: str, widgets: Optional[list[QWidget]] = None, area: Optional[Qt.ToolBarArea] = None
) -> QToolBar:
    """
    Creates a QToolbar with the default arguments for this repository.

    Theses arguments include context menu policy, size policy, orientation, and floatable.

    Parameters
    ----------
    parent : QMainWindow
        The parent of the toolbar
    name : str
        The name of the toolbar
    widgets: Optional[list[QWidget]]
        The widgets to attach to the toolbar

    Returns
    -------
    QToolBar
        with the default arguments
    """

    toolbar = QToolBar(name, parent)
    toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
    toolbar.setOrientation(Qt.Horizontal)
    toolbar.setFloatable(True)
    toolbar.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)

    if widgets is not None:
        for widget in widgets:
            toolbar.addWidget(widget)

    if area is not None:
        parent.addToolBar(area, toolbar)

    return toolbar
