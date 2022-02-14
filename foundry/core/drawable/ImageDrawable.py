from functools import cached_property
from typing import Optional

from attr import attrs
from pydantic import FilePath
from PySide6.QtGui import QColor, QImage, Qt

from foundry.core.drawable.Drawable import Drawable, DrawableProtocol
from foundry.core.point.Point import HashablePointProtocol
from foundry.core.rect.Rect import PydanticRect, Rect
from foundry.core.rect.util import to_qrect
from foundry.core.size.Size import Size, SizeProtocol
from foundry.game.gfx.drawable import MASK_COLOR


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class ImageDrawable:
    """
    A drawable for an image.
    """

    point_offset: HashablePointProtocol
    qimage: QImage
    image_offset: Optional[Rect] = None
    use_transparency: bool = True

    @property
    def size(self) -> SizeProtocol:
        return Size(self.image.width(), self.image.height())

    @cached_property
    def _image(self) -> QImage:
        image = self.qimage if self.image_offset is None else self.qimage.copy(to_qrect(self.image_offset))
        if self.use_transparency:
            mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
            image.setAlphaChannel(mask)
        return image

    def image(self, scale_factor: int = 1) -> QImage:
        return self._image.scaled(self.size.width * scale_factor, self.size.height * scale_factor)


class PydanticImageDrawable(Drawable):
    image: FilePath
    image_offset: Optional[PydanticRect] = None
    use_transparency: bool = True

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    @cached_property
    def drawable(self) -> DrawableProtocol:
        return ImageDrawable(
            self.point_offset.point,
            QImage(self.image),
            self.image_offset if self.image_offset is None else Rect.from_rect(self.image_offset.rect),
            self.use_transparency,
        )
