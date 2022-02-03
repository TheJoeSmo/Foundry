from attr import attrs

from foundry.core.graphics_set.GraphicsSet import GraphicsSetProtocol
from foundry.core.palette.PaletteGroup import MutablePaletteGroupProtocol
from foundry.core.player_animations.PlayerAnimation import PlayerAnimation


@attrs(slots=True, auto_attribs=True)
class PlayerAnimationData:
    animation: PlayerAnimation
    graphics_set: GraphicsSetProtocol
    palette_group: MutablePaletteGroupProtocol
    palette_index: int
    is_kicking: bool = False

    @property
    def horizontal_flip(self) -> list[bool]:
        if self.frames[3] == self.frames[4]:
            return [False, True, False, False, True, False]
        else:
            return [False, False, False, False, False, False]

    @property
    def frames(self) -> list[int]:
        animation = self.animation.animations
        if self.is_kicking:
            return [animation[0], animation[1], animation[2], animation[3], animation[4], animation[5]]
        return list(animation)
