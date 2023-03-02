from abc import ABC, abstractmethod

from PySide6.QtGui import QPainter

from foundry.core.geometry import Point, Rect, Size
from foundry.game.Definitions import Definition

EXPANDS_NOT = 0b00
EXPANDS_HORIZ = 0b01
EXPANDS_VERT = 0b10
EXPANDS_BOTH = EXPANDS_HORIZ | EXPANDS_VERT


class ObjectLike(ABC):
    """
    An abstract base class representing a generic game object.

    Attributes
    ----------
    obj_index : int
        The index of the object.
    name : str
        The name of the object.
    rect : Rect
        The bounding rectangle of the object.
    """

    obj_index: int
    name: str
    rect: Rect

    @abstractmethod
    def render(self) -> None:
        """
        Abstract method for rendering the object.
        """

    @abstractmethod
    def draw(self, painter: QPainter, zoom: int, transparent: bool) -> None:
        """
        Draws the object on a QPainter canvas.

        Parameters
        ----------
        painter : QPainter
            The QPainter canvas to draw on.
        zoom : int
            The zoom level to draw the object at.
        transparent : bool
            Whether or not the object should be drawn with transparency.
        """

    @abstractmethod
    def get_status_info(self) -> list[tuple]:
        """
        Abstract method for retrieving status information about the object.

        Returns
        -------
        status : list[tuple]
            A list of key-value pairs containing status information about the object.
        """

    @abstractmethod
    def move_by(self, point: Point) -> None:
        """
        Abstract method for moving the object by a given point.

        Parameters
        ----------
        point : Point
            The point to move the object by.
        """

    @property
    @abstractmethod
    def definition(self) -> Definition:
        """
        Abstract property for retrieving the object's definition.

        Returns
        -------
        definition : Definition
            The definition of the object.
        """

    @property
    @abstractmethod
    def point(self) -> Point:
        """
        Abstract property for retrieving the object's position.

        Returns
        -------
        point : Point
            The position of the object.
        """

    @point.setter
    @abstractmethod
    def point(self, point: Point) -> None:
        """
        Abstract property for setting the object's position.

        Parameters
        ----------
        point : Point
            The position to set the object to.
        """

    @abstractmethod
    def point_in(self, x: int, y: int) -> bool:
        """
        Abstract method for checking if a point is within the object's bounds.

        Parameters
        ----------
        x : int
            The x-coordinate of the point to check.
        y : int
            The y-coordinate of the point to check.

        Returns
        -------
        is_point_in : bool
            Whether the point is within the object's bounds.
        """

    def get_rect(self, block_length: int = 1) -> Rect:
        """
        Returns the object's bounding rectangle in pixels.

        Parameters
        ----------
        block_length : int, optional
            The length of a block in pixels, by default 1.

        Returns
        -------
        rect : Rect
            The bounding rectangle of the object in pixels.
        """
        return self.rect * Size(block_length, block_length)

    @abstractmethod
    def __contains__(self, item: Point) -> bool:
        """
        Abstract method for checking if a point is within the object's bounds.

        Parameters
        ----------
        point : Point
            The point to check.

        Returns
        -------
        is_point_in : bool
            Whether the point is within the object's bounds.
        """

    @abstractmethod
    def to_bytes(self) -> bytearray:
        """
        Abstract method to convert the object to a byte array representation.

        Returns
        -------
        bytearray
            A byte array representing the object.
        """

    def expands(self) -> int:
        """
        Returns whether the object expands horizontally, vertically, both or not at all.

        Returns
        -------
        int
            An integer value that represents the object's expansion direction. It can be EXPANDS_NOT,
            EXPANDS_HORIZ, EXPANDS_VERT, or EXPANDS_BOTH.
        """
        return EXPANDS_NOT

    def primary_expansion(self) -> int:
        """
        Returns the primary expansion direction of the object.

        Returns
        -------
        int
            An integer value that represents the primary expansion direction of the object. It can be
            EXPANDS_NOT, EXPANDS_HORIZ, EXPANDS_VERT, or EXPANDS_BOTH.
        """
        return EXPANDS_NOT
