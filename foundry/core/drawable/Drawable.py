from pathlib import Path

from attr import attrs
from PySide6.QtGui import QColor, QImage, Qt

from foundry.core.blocks.BlockGroup import BlockGroup
from foundry.core.file import FilePath
from foundry.core.geometry import Point, Rect, Size
from foundry.core.namespace import (
    BoolValidator,
    ConcreteValidator,
    DefaultValidator,
    KeywordValidator,
    OptionalValidator,
    TypeInformation,
    custom_validator,
    validate,
)
from foundry.core.tiles import MASK_COLOR


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
@custom_validator("BLOCK GROUP", method_name="validate_from_block_group")
@custom_validator("FROM FILE", method_name="validate_from_file")
class Drawable(ConcreteValidator, KeywordValidator):
    __names__ = ("__DRAWABLE_VALIDATOR__", "drawable", "Drawable", "DRAWABLE")
    __required_validators__ = (OptionalValidator, DefaultValidator, FilePath, Point, Rect, BlockGroup)
    __type_default__ = TypeInformation("FROM FILE")

    base_image: QImage
    point_offset: Point = Point(0, 0)

    @property
    def size(self) -> Size:
        return Size.from_qsize(self.base_image.size())

    def image(self, scale_factor: int = 1) -> QImage:
        return self.base_image.scaled((self.size * scale_factor).qsize)

    @classmethod
    def from_block_group(cls, block_group: BlockGroup, point_offset: Point = Point(0, 0)):
        return cls(block_group.image(), point_offset)

    @classmethod
    @validate(block_group=BlockGroup, point_offset=DefaultValidator.generate_class(Point, Point(0, 0)))
    def validate_from_block_group(cls, block_group: BlockGroup, point_offset: Point):
        return cls.from_block_group(block_group, point_offset)

    @classmethod
    def from_image(
        cls,
        image: QImage,
        image_offset: Rect | None = None,
        use_transparency: bool = True,
        point_offset: Point = Point(0, 0),
    ):
        assert use_transparency
        image = image if image_offset is None else image.copy(image_offset.qrect)
        if use_transparency:
            mask: QImage = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskOutColor)
            image.setAlphaChannel(mask)
        return cls(image, point_offset)

    @classmethod
    def from_file(
        cls,
        path: Path,
        image_offset: Rect | None = None,
        use_transparency: bool = True,
        point_offset: Point = Point(0, 0),
    ):
        return cls.from_image(QImage(path), image_offset, use_transparency, point_offset)

    @classmethod
    @validate(
        path=FilePath,
        image_offset=OptionalValidator.generate_class(Rect),
        use_transparency=DefaultValidator.generate_class(BoolValidator, True),
        point_offset=DefaultValidator.generate_class(Point, Point(0, 0)),
    )
    def validate_from_file(cls, path: FilePath, image_offset: Rect | None, use_transparency: bool, point_offset: Point):
        return cls.from_file(path, image_offset, use_transparency, point_offset)
