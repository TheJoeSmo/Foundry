from pytest import mark

from foundry.core.geometry import Line, Point


class TestLine:
    __test_class__ = Line

    @mark.parametrize(
        "p1,p2,p3,r",
        [
            (Point(0, 0), Point(0, 0), Point(0, 0), True),
            (Point(0, 0), Point(0, 0), Point(1, 1), False),
            (Point(1, 1), Point(1, 1), Point(1, 1), True),
            (Point(1, 1), Point(1, 1), Point(0, 0), False),
            (Point(0, 0), Point(1, 1), Point(0, 0), True),
            (Point(0, 0), Point(1, 1), Point(1, 1), True),
            (Point(0, 0), Point(1, 1), Point(2, 2), False),
            (Point(0, 0), Point(2, 2), Point(1, 1), True),
            (Point(0, 0), Point(2, 2), Point(0, 1), False),
            (Point(0, 0), Point(2, 2), Point(1, 0), False),
            (Point(0, 0), Point(2, 2), Point(1, 2), False),
            (Point(0, 0), Point(2, 2), Point(2, 1), False),
            (Point(1, 1), Point(0, 0), Point(0, 0), True),
            (Point(1, 1), Point(0, 0), Point(1, 1), True),
            (Point(2, 2), Point(0, 0), Point(1, 1), True),
        ],
    )
    def test_contains(self, p1: Point, p2: Point, p3: Point, r: bool) -> None:
        assert r == (p3 in self.__test_class__(p1, p2))

    @mark.parametrize(
        "p1,p2,p3,p4,r",
        [
            (Point(0, 0), Point(0, 0), Point(0, 0), Point(0, 0), True),
            (Point(1, 1), Point(1, 1), Point(1, 1), Point(1, 1), True),
            (Point(0, 0), Point(0, 0), Point(1, 1), Point(1, 1), False),
            (Point(1, 1), Point(1, 1), Point(0, 0), Point(0, 0), False),
            (Point(0, 0), Point(1, 1), Point(1, 1), Point(0, 0), True),
            (Point(1, 1), Point(0, 0), Point(0, 0), Point(1, 1), True),
            (Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3), False),
            (Point(1, 1), Point(0, 0), Point(3, 3), Point(2, 2), False),
            (Point(2, 1), Point(3, 3), Point(3, 3), Point(0, 0), True),
        ],
    )
    def test_intersects(self, p1: Point, p2: Point, p3: Point, p4: Point, r: bool) -> None:
        assert r == self.__test_class__(p1, p2).intersects(self.__test_class__(p3, p4))
        assert r == self.__test_class__(p3, p4).intersects(self.__test_class__(p1, p2))
