from collections.abc import Callable
from typing import Any

from PySide6.QtGui import QAction, QIcon, Qt
from PySide6.QtWidgets import QMainWindow, QToolBar, QWidget


def create_toolbar(
    parent: QMainWindow, name: str, widgets: list[QWidget] | None = None, area: Qt.ToolBarArea | None = None
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
    toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
    toolbar.setOrientation(Qt.Orientation.Horizontal)
    toolbar.setFloatable(True)
    toolbar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea | Qt.ToolBarArea.RightToolBarArea)

    if widgets is not None:
        for widget in widgets:
            toolbar.addWidget(widget)

    if area is not None:
        parent.addToolBar(area, toolbar)

    return toolbar


class Toolbar(QToolBar):
    """
    An extension of the regular `QToolBar`.
    """

    def add_action(self, text: str, *args: Callable[[], Any], icon: QIcon | None = None) -> QAction:
        """
        Adds a toolbar option with `text` that will call `*args` when selected.

        Parameters
        ----------
        text : str
            The text that will be displayed next to the option to select.
        icon : QIcon | None, optional
            The icon that will be displayed next to the option, by default None will be displayed.

        Returns
        -------
        QAction
            The action associated with the toolbar option generated.
        """
        action = self.addAction(icon, text) if icon else self.addAction(text)
        for arg in args:
            action.triggered.connect(arg)  # type: ignore
        return action
