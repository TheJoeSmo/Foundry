from pytest import mark

from foundry.core.geometry import Point, Rect, Size


class TestRect:
    __test_class__ = Rect

    @mark.parametrize("p,s", [(Point(0, 0), Size(0, 0)), (Point(0, 0), Size(1, 1)), (Point(1, 1), Size(1, 1))])
    def test_initialization(self, p: Point, s: Size) -> None:
        self.__test_class__(p, s)

    @mark.parametrize(
        "r,r2,re",
        [
            (Rect(Point(0, 0), Size(0, 0)), Rect(Point(0, 0), Size(0, 0)), Rect(Point(0, 0), Size(0, 0))),
            (Rect(Point(1, 2), Size(3, 4)), Rect(Point(1, 2), Size(3, 4)), Rect(Point(2, 4), Size(6, 8))),
            (Rect(Point(4, 3), Size(2, 1)), Rect(Point(1, 2), Size(3, 4)), Rect(Point(5, 5), Size(5, 5))),
            (Rect(Point(4, 3), Size(2, 1)), Rect(Point(4, 3), Size(2, 1)), Rect(Point(8, 6), Size(4, 2))),
            (Rect(Point(4, 3), Size(2, 1)), Point(4, 3), Rect(Point(8, 6), Size(6, 4))),
        ],
    )
    def test_add(self, r: Rect, r2: Point | Rect, re: Rect) -> None:
        assert r + r2 == re

    @mark.parametrize(
        "r,r2,re",
        [
            (Rect(Point(0, 0), Size(0, 0)), Rect(Point(0, 0), Size(0, 0)), Rect(Point(0, 0), Size(0, 0))),
            (Rect(Point(1, 2), Size(3, 4)), Rect(Point(1, 2), Size(3, 4)), Rect(Point(0, 0), Size(0, 0))),
            (Rect(Point(4, 3), Size(2, 1)), Rect(Point(1, 2), Size(2, 1)), Rect(Point(3, 1), Size(0, 0))),
            (Rect(Point(4, 3), Size(2, 1)), Rect(Point(4, 3), Size(2, 1)), Rect(Point(0, 0), Size(0, 0))),
            (Rect(Point(4, 3), Size(2, 1)), Point(1, 1), Rect(Point(3, 2), Size(1, 0))),
        ],
    )
    def test_subtract(self, r: Rect, r2: Point | Rect, re: Rect) -> None:
        assert r - r2 == re

    @mark.parametrize(
        "re,t,b,l,r",
        [
            (Rect(Point(0, 0), Size(0, 0)), 0, 0, 0, 0),
            (Rect(Point(1, 1), Size(1, 1)), 2, 1, 1, 2),
            (Rect(Point(1, 1), Size(0, 1)), 2, 1, 1, 1),
            (Rect(Point(1, 1), Size(1, 0)), 1, 1, 1, 2),
        ],
    )
    def test_directions(self, re: Rect, t: int, b: int, l: int, r: int) -> None:  # noqa: E741
        assert re.top == t
        assert re.bottom == b
        assert re.left == l
        assert re.right == r

    @mark.parametrize(
        "r,tl,tr,bl,br",
        [
            (Rect(Point(0, 0), Size(0, 0)), Point(0, 0), Point(0, 0), Point(0, 0), Point(0, 0)),
            (Rect(Point(1, 1), Size(1, 1)), Point(1, 2), Point(2, 2), Point(1, 1), Point(2, 1)),
            (Rect(Point(1, 1), Size(0, 1)), Point(1, 2), Point(1, 2), Point(1, 1), Point(1, 1)),
            (Rect(Point(1, 1), Size(1, 0)), Point(1, 1), Point(2, 1), Point(1, 1), Point(2, 1)),
        ],
    )
    def test_corners(self, r: Rect, tl: Point, tr: Point, bl: Point, br: Point) -> None:
        assert r.upper_left_point == tl
        assert r.upper_right_point == tr
        assert r.lower_left_point == bl
        assert r.lower_right_point == br

    @mark.parametrize(
        "r,m",
        [
            (Rect(Point(0, 0), Size(2, 2)), Point(1, 1)),
            (Rect(Point(1, 1), Size(3, 3)), Point(2, 2)),
            (Rect(Point(2, 2), Size(2, 2)), Point(3, 3)),
            (Rect(Point(2, 2), Size(4, 4)), Point(4, 4)),
        ],
    )
    def test_mid_point(self, r: Rect, m: Point) -> None:
        assert r.mid_point == m

    @mark.parametrize(
        "r,r2,c",
        [
            (Rect(Point(1, 1), Size(1, 1)), Rect(Point(3, 3), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(1, 1)), Rect(Point(0, 1), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(1, 1)), Rect(Point(1, 0), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(1, 1)), Rect(Point(1, 1), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(0, 0), Size(1, 1)), True),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(0, 1), Size(1, 1)), True),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(1, 0), Size(1, 1)), True),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(1, 1), Size(1, 1)), True),
            (Rect(Point(0, 0), Size(1, 1)), Point(0, 0), True),
            (Rect(Point(0, 0), Size(1, 1)), Point(0, 1), True),
            (Rect(Point(0, 0), Size(1, 1)), Point(1, 0), True),
            (Rect(Point(0, 0), Size(1, 1)), Point(1, 1), True),
        ],
    )
    def test_contains(self, r: Rect, r2: Point | Rect, c: bool) -> None:
        assert r.contains(r2) == c

    @mark.parametrize(
        "r,r2,i",
        [
            (Rect(Point(0, 0), Size(1, 1)), Rect(Point(0, 1), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(1, 1)), Rect(Point(1, 0), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(1, 1)), Rect(Point(1, 1), Size(1, 1)), False),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(0, 1), Size(1, 2)), True),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(1, 0), Size(2, 1)), True),
            (Rect(Point(0, 0), Size(2, 2)), Rect(Point(1, 1), Size(2, 2)), True),
        ],
    )
    def test_intersects(self, r: Rect, r2: Rect, i: bool) -> None:
        assert r.intersects(r2) == i
