from PySide6.QtCore import QPoint
from pytest import raises

from foundry.core.geometry import Point
from foundry.core.namespace import (
    PARENT_ARGUMENT,
    MissingTypeArgumentException,
    Namespace,
)

from .test_vector2D import TestVector2D


class TestPoint(TestVector2D):
    __test_class__ = Point

    def test_point_initialization_zero(self):
        p = Point(0, 0)
        assert p.x == 0
        assert p.y == 0

    def test_point_initialization_simple(self):
        p = Point(1, 2)
        assert p.x == 1
        assert p.y == 2

    def test_point_distance_from_origin_zero(self):
        assert Point(0, 0).distance_from_origin == 0

    def test_point_distance_from_origin_one(self):
        assert Point(1, 0).distance_from_origin == 1
        assert Point(0, 1).distance_from_origin == 1

    def test_point_distance_from_origin_simple(self):
        assert Point(3, 4).distance_from_origin == 5
        assert Point(4, 3).distance_from_origin == 5

    def test_point_distance_from_origin_complex(self):
        assert 6.4 <= Point(4, 5).distance_from_origin <= 6.5
        assert 6.4 <= Point(5, 4).distance_from_origin <= 6.5

    def test_point_distance_from_origin_negative(self):
        assert Point(4, 5).distance_from_origin == Point(-4, 5).distance_from_origin
        assert Point(4, 5).distance_from_origin == Point(-4, -5).distance_from_origin
        assert Point(4, 5).distance_from_origin == Point(4, -5).distance_from_origin

    def test_point_equal_equal(self):
        assert Point(0, 0) == Point(0, 0)
        assert Point(0, 1) == Point(0, 1)
        assert Point(1, 0) == Point(1, 0)

    def test_point_equal_not_equal(self):
        assert not Point(1, 1) == Point(2, 2)
        assert not Point(0, 1) == Point(1, 0)
        assert not Point(2, 3) == Point(3, 2)

    def test_point_not_equal_equal(self):
        assert not Point(0, 0) != Point(0, 0)
        assert not Point(0, 1) != Point(0, 1)
        assert not Point(1, 0) != Point(1, 0)

    def test_point_not_equal_not_equal(self):
        assert Point(1, 1) != Point(2, 2)
        assert Point(0, 1) != Point(1, 0)
        assert Point(2, 3) != Point(3, 2)

    def test_point_less_than_equal(self):
        assert not Point(0, 0) < Point(0, 0)
        assert not Point(1, 1) < Point(1, 1)

    def test_point_less_than_true(self):
        assert Point(0, 0) < Point(1, 1)
        assert Point(0, 0) < Point(-1, 1)

    def test_point_less_than_false(self):
        assert not Point(1, 1) < Point(0, 0)
        assert not Point(-1, 1) < Point(0, 0)

    def test_point_less_equal_than_equal(self):
        assert Point(0, 0) <= Point(0, 0)
        assert Point(1, 1) <= Point(1, 1)

    def test_point_less_equal_than_true(self):
        assert Point(0, 0) <= Point(1, 1)
        assert Point(0, 0) <= Point(-1, 1)

    def test_point_less_equal_than_false(self):
        assert not Point(1, 1) <= Point(0, 0)
        assert not Point(-1, 1) <= Point(0, 0)

    def test_point_great_than_equal(self):
        assert not Point(0, 0) > Point(0, 0)
        assert not Point(1, 1) > Point(1, 1)

    def test_point_great_than_true(self):
        assert not Point(0, 0) > Point(1, 1)
        assert not Point(0, 0) > Point(-1, 1)

    def test_point_great_than_false(self):
        assert Point(1, 1) > Point(0, 0)
        assert Point(-1, 1) > Point(0, 0)

    def test_point_great_equal_than_equal(self):
        assert Point(0, 0) >= Point(0, 0)
        assert Point(1, 1) >= Point(1, 1)

    def test_point_great_equal_than_true(self):
        assert not Point(0, 0) >= Point(1, 1)
        assert not Point(0, 0) >= Point(-1, 1)

    def test_point_great_equal_than_false(self):
        assert Point(1, 1) >= Point(0, 0)
        assert Point(-1, 1) >= Point(0, 0)

    def test_from_qt(self):
        assert Point(0, 0) == Point.from_qt(QPoint(0, 0))
        assert Point(1, 1) == Point.from_qt(QPoint(1, 1))
        assert Point(1, -1) == Point.from_qt(QPoint(1, -1))
        assert Point(-1, 1) == Point.from_qt(QPoint(-1, 1))

    def test_validate_point(self):
        assert Point(0, 0) == Point.validate(
            {"x": 0, "y": 0, PARENT_ARGUMENT: Namespace(validators=Point.type_manager)}
        )
        assert Point(1, 0) == Point.validate(
            {"x": 1, "y": 0, PARENT_ARGUMENT: Namespace(validators=Point.type_manager)}
        )
        assert Point(0, 1) == Point.validate(
            {"x": 0, "y": 1, PARENT_ARGUMENT: Namespace(validators=Point.type_manager)}
        )

    def test_validate_point_respect_namespace_validators(self):
        with raises(MissingTypeArgumentException):
            Point.validate({"x": 0, "y": 0, PARENT_ARGUMENT: Namespace()})
