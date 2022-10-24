from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget


class Painter:
    """
    Creates a context manager for a QPainter to be applied on a QImage.

    If no context manger is provided for a QPainter, any error during its life-cycle could result in a crash.
    """

    def __init__(self, image: QImage | QWidget):
        self.image = image

    def __enter__(self) -> QPainter:
        self.painter = QPainter(self.image)
        return self.painter

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.painter.end()
