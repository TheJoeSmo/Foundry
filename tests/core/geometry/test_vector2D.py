from attr import attrs
from pytest import mark, raises

from foundry.core.geometry import Vector2D


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class SimpleVector(Vector2D):
    a: int
    b: int

    def __eq__(self, other) -> bool:
        if not isinstance(other, SimpleVector):
            return False
        return self.a == other.a and self.b == other.b

    @property
    def i_component(self) -> int:
        return self.a

    @property
    def j_component(self) -> int:
        return self.b

    @classmethod
    def from_vector(cls, vector: Vector2D):
        return cls(vector.i_component, vector.j_component)

    @classmethod
    def from_components(cls, i_component: int, j_component: int):
        return cls(i_component, j_component)


class TestVector2D:
    __test_class__ = SimpleVector

    @mark.parametrize("i,j", [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (1, 2), (3, 1), (1, 3)])
    def test_components(self, i: int, j: int) -> None:
        obj = self.__test_class__(i, j)
        assert i == obj.i_component
        assert j == obj.j_component

    @mark.parametrize("i,j", [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (1, 2), (3, 1), (1, 3)])
    def test_from_components(self, i: int, j: int) -> None:
        obj = self.__test_class__(i, j)
        assert i == obj.i_component
        assert j == obj.j_component

    @mark.parametrize("i,j", [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (1, 2), (3, 1), (1, 3)])
    def test_from_vector(self, i: int, j: int) -> None:
        assert self.__test_class__(i, j) == self.__test_class__.from_vector(SimpleVector(i, j))

    @mark.parametrize("i,j", [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (1, 2), (3, 1), (1, 3)])
    def test_equal_equal(self, i: int, j: int) -> None:
        assert self.__test_class__(i, j) == self.__test_class__(i, j)

    @mark.parametrize("i,j,i2,j2", [(0, 0, 0, 1), (0, 0, 1, 0), (0, 1, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (0, 0, 1, 1)])
    def test_equal_not_equal(self, i: int, j: int, i2: int, j2: int) -> None:
        assert not self.__test_class__(i, j) == self.__test_class__(i2, j2)

    @mark.parametrize("i,j", [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (1, 2), (3, 1), (1, 3)])
    def test_not_equal_equal(self, i: int, j: int) -> None:
        assert not self.__test_class__(i, j) != self.__test_class__(i, j)

    @mark.parametrize("i,j,i2,j2", [(0, 0, 0, 1), (0, 0, 1, 0), (0, 1, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (0, 0, 1, 1)])
    def test_not_equal_not_equal(self, i: int, j: int, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) != self.__test_class__(i2, j2)

    @mark.parametrize("i,j,i2,j2", [(0b11, 0b101, 0b1, 0b10), (1, 1, 0, 0), (0, 0, 0, 0)])
    def test_right_shift(self, i: int, j: int, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) >> 1 == self.__test_class__(i2, j2)

    @mark.parametrize("i,j,i2,j2", [(0b11, 0b101, 0b110, 0b1010), (0b1, 0b1, 0b10, 0b10), (0, 0, 0, 0)])
    def test_left_shift(self, i: int, j: int, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) << 1 == self.__test_class__(i2, j2)

    @mark.parametrize("i,j,i2,j2", [(0, 0, 0, 0), (1, 1, 1, 1), (2, 3, 4, 9), (3, 2, 9, 4)])
    def test_power(self, i: int, j: int, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) ** 2 == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2", [(1, 2, SimpleVector(3, 4), 4, 6), (3, 4, SimpleVector(-1, -2), 2, 2), (1, 2, 3, 4, 5)]
    )
    def test_add(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) + v == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2", [(3, 4, SimpleVector(1, 2), 2, 2), (4, 3, SimpleVector(-1, -2), 5, 5), (5, 4, 3, 2, 1)]
    )
    def test_subtract(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) - v == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2", [(1, 2, SimpleVector(3, 4), 3, 8), (1, 2, SimpleVector(4, 3), 4, 6), (1, 2, 3, 3, 6)]
    )
    def test_multiply(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) * v == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2", [(4, 2, SimpleVector(2, 1), 2, 2), (2, 4, SimpleVector(1, 2), 2, 2), (4, 2, 2, 2, 1)]
    )
    def test_divide(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) // v == self.__test_class__(i2, j2)

    @mark.parametrize("i,j,v", [(1, 1, SimpleVector(0, 1)), (1, 1, SimpleVector(1, 0)), (1, 1, 0)])
    def test_divide_zero_error(self, i: int, j: int, v: int | Vector2D) -> None:
        with raises(ZeroDivisionError):
            self.__test_class__(i, j) // v

    @mark.parametrize(
        "i,j,v,i2,j2",
        [
            (1, 2, SimpleVector(4, 4), 1, 2),
            (2, 1, SimpleVector(4, 4), 2, 1),
            (3, 7, SimpleVector(4, 2), 3, 1),
            (1, 2, 4, 1, 2),
        ],
    )
    def test_modulo(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) % v == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2",
        [
            (1, 1, SimpleVector(0, 0), 0, 0),
            (1, 1, SimpleVector(1, 0), 1, 0),
            (1, 1, SimpleVector(0, 1), 0, 1),
            (0, 0, SimpleVector(0, 0), 0, 0),
            (1, 0, 1, 1, 0),
            (0, 1, 1, 0, 1),
            (1, 1, 0, 0, 0),
        ],
    )
    def test_and(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) & v == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2",
        [
            (1, 1, SimpleVector(0, 0), 1, 1),
            (1, 1, SimpleVector(1, 0), 1, 1),
            (1, 1, SimpleVector(0, 1), 1, 1),
            (0, 0, SimpleVector(0, 0), 0, 0),
            (1, 0, 1, 1, 1),
            (0, 1, 1, 1, 1),
            (1, 1, 0, 1, 1),
            (1, 0, 0, 1, 0),
            (0, 1, 0, 0, 1),
        ],
    )
    def test_or(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) | v == self.__test_class__(i2, j2)

    @mark.parametrize(
        "i,j,v,i2,j2",
        [
            (1, 1, SimpleVector(0, 0), 1, 1),
            (1, 1, SimpleVector(1, 0), 0, 1),
            (1, 1, SimpleVector(0, 1), 1, 0),
            (0, 0, SimpleVector(0, 0), 0, 0),
            (1, 0, 1, 0, 1),
            (0, 1, 1, 1, 0),
            (1, 1, 0, 1, 1),
            (1, 0, 0, 1, 0),
            (0, 1, 0, 0, 1),
        ],
    )
    def test_xor(self, i: int, j: int, v: int | Vector2D, i2: int, j2: int) -> None:
        assert self.__test_class__(i, j) ^ v == self.__test_class__(i2, j2)
