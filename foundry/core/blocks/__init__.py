from foundry.core.point.Point import Point
from foundry.core.size.Size import Size

BLOCK_SIZE: Size = Size(16, 16)

PATTERN_LOCATIONS: tuple[Point, Point, Point, Point] = (
    Point(0, 0),
    Point(8, 0),
    Point(0, 8),
    Point(8, 8),
)
