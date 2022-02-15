from PySide6.QtCore import QRect

from foundry.core.rect.Rect import RectProtocol


def to_qrect(rect: RectProtocol) -> QRect:
    """
    Generates a QRect from a RectProtocol.

    Parameters
    ----------
    rect : RectProtocol
        The rect to be converted to a Rect.

    Returns
    -------
    QRect
        The QRect derived from the RectProtocol.
    """
    return QRect(rect.point.x, rect.point.y, rect.size.width, rect.size.height)
