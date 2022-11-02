from attr import attrs
from PySide6.QtGui import QColor, QPainter, QPen, Qt

from foundry.core.geometry import Point, Rect, Size

STROKE_COLOR = QColor(0x00, 0x00, 0x00, 0x80)


@attrs(slots=True, auto_attribs=True)
class SelectionSquare:
    start_point: Point = Point(0, 0)
    end_point: Point = Point(0, 0)
    is_active: bool = False
    should_draw: bool = False

    @property
    def rect(self) -> Rect:
        return Rect.from_points(self.start_point, self.end_point)

    def start(self, point: Point) -> None:
        self.is_active = True
        self.start_point = point

    def set_current_end(self, point: Point) -> None:
        if self.is_active:
            self.should_draw = True
            self.end_point = point

    def stop(self):
        self.is_active = False
        self.should_draw = False

    def get_adjusted_rect(self, scale_factor: Size) -> Rect:
        return self.rect // scale_factor

    def draw(self, painter: QPainter):
        if self.should_draw:
            pen: QPen = QPen(STROKE_COLOR)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rect.to_qt())
