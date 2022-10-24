from collections.abc import Callable
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu


class Menu(QMenu):
    """
    An extension of the regular `QMenu`.
    """

    def add_action(self, text: str, *args: Callable[[], Any]) -> QAction:
        """
        Adds a menu option with `text` that will call `*args` when selected.

        Parameters
        ----------
        text : str
            The text that will be displayed next to option to select.

        Returns
        -------
        QAction
            The action associated with the menu option generated.
        """
        action = self.addAction(text)
        for arg in args:
            action.triggered.connect(arg)  # type: ignore
        return action
