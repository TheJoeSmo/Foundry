from typing import Any

from attr import attrs, evolve, field
from numpy import full, pad
from numpy.typing import NDArray

from foundry.core.geometry import Point, Size


@attrs(slots=True, auto_attribs=True)
class PatternMatrix:
    """
    A matrix of pattern indexes that is intelligently resizes and mutates pattern index data.

    Attributes
    ----------
    size: Size
        The size of the matrix.
    default: int = 0
        The value that will be filled when a value is initialized.
    """

    size: Size
    default: int = 0
    patterns: NDArray[Any] = field(init=False)
    _size: Size = field(init=False, repr=False)

    def __attrs_post_init__(self):
        self.patterns = full((self.size.width, self.size.height), self.default)
        self._size = self.size

    def is_inside(self, point: Point) -> bool:
        """
        Determines if `point` is inside `size`.

        Parameters
        ----------
        point: Point
            The point to evaluate.

        Returns
        -------
        bool
            If `point` is inside the matrix.
        """
        return self.size.width > point.x and self.size.height > point.y

    def set_index(self, point: Point, pattern: int):
        """
        Sets the index of a pattern inside the matrix to the `pattern` at `point`.

        Parameters
        ----------
        point : Point
            The point inside the matrix to set.
        pattern : int
            The value of the pattern index.

        Raises
        ------
        IndexError
            If `point` is not inside the matrix.
        """
        if not self.is_inside(point):
            raise IndexError(f"{point} is not inside {self}")
        self.patterns[point.x][point.y] = pattern

    def get_index(self, point: Point) -> int:
        """
        Gets the index of a pattern inside the matrix to the `pattern` at `point`.

        Parameters
        ----------
        point : Point
            The point inside the matrix to get.

        Returns
        -------
        int
            The value of the pattern index at `point` inside the matrix.

        Raises
        ------
        IndexError
            If `point` is not inside the matrix.
        """
        if not self.is_inside(point):
            raise IndexError(f"{point} is not inside {self}")
        return self.patterns[point.x][point.y]

    def resize(self, size: Size):
        """
        Resizes the matrix to account for a different size.

        Parameters
        ----------
        size : Size
            The new size of the matrix.

        Notes
        -----
        When resizing to a smaller size, the data will still be stored.  If rexpanding to this size,
            the old data will be retained.
        When resizing to a larger width, the right will be expanded with `default`.
        When resizing to a larger height, the bottom will be expanded with `default`.

        Examples
        --------
        >>> a = PatternMatrix(Size(2, 2), 0)
        array([
            [0, 0],
            [0, 0]
        ])
        >>> a.default = 1
        >>> a.resize(Size(2, 1))
        array([[0, 0]])
        >>> a.resize(Size(2, 3))
        array([
            [0, 0],
            [0, 0],
            [1, 1]
        ])
        >>> a.default = 2
        >>> a.resize(Size(3, 3))
        array([
            [0, 0, 2],
            [0, 0, 2],
            [1, 1, 2]
        ])
        """
        self.size = size
        if size.width > self._size.width:
            self.patterns = pad(
                self.patterns, ((0, 0), (0, size.width - self._size.width)), constant_value=self.default
            )  # type: ignore
            self._size = evolve(self._size, width=size.width)
        if size.height > self._size.height:
            self.patterns = pad(
                self.patterns, ((0, size.height - self._size.height), (0, 0)), constant_value=self.default
            )  # type: ignore
            self._size = evolve(self._size, height=size.height)
