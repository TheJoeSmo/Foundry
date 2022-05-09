from PySide6.QtCore import QRect

from foundry.core.rect.Rect import Rect


def to_qrect(rect: Rect) -> QRect:
    """
    Generates a QRect from a Rect.

    Parameters
    ----------
    rect : Rect
        The rect to be converted to a Rect.

    Returns
    -------
    QRect
        The QRect derived from the Rect.
    """
    return QRect(rect.point.x, rect.point.y, rect.size.width, rect.size.height)
