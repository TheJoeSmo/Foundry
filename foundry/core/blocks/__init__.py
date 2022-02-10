from foundry.core.point.Point import Point, PointProtocol
from foundry.core.size.Size import Size, SizeProtocol

BLOCK_SIZE: SizeProtocol = Size(16, 16)

PATTERN_LOCATIONS: tuple[PointProtocol, PointProtocol, PointProtocol, PointProtocol] = (
    Point(0, 0),
    Point(8, 0),
    Point(0, 8),
    Point(8, 8),
)
