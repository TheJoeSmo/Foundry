from foundry.core.graphics_page.GraphicsPage import GraphicsPage
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import COLORS_PER_PALETTE
from foundry.core.palette.Palette import MutablePalette
from foundry.core.palette.PaletteGroup import (
    MutablePaletteGroup,
    MutablePaletteGroupProtocol,
)
from foundry.core.player_animations import (
    PLAYER_FRAME_PAGE_OFFSET,
    PLAYER_FRAME_START,
    PLAYER_FRAMES,
    PLAYER_POWER_UPS,
    PLAYER_POWER_UPS_PALETTE_COUNT,
    PLAYER_POWER_UPS_PALETTES,
    PLAYER_SUIT_PAGE_OFFSET,
    SPRITES_PER_FRAME,
)
from foundry.core.player_animations.PlayerAnimation import PlayerAnimation
from foundry.core.player_animations.PlayerAnimationData import PlayerAnimationData
from foundry.game.File import ROM


def load_animations_graphic_set(animation: PlayerAnimation, power_up: int, offsets: list[int]) -> GraphicsSet:
    return GraphicsSet(
        (
            GraphicsPage(animation.offset + offsets[power_up]),
            GraphicsPage(animation.offset + offsets[power_up]),
            GraphicsPage(animation.offset + offsets[power_up]),
            GraphicsPage(animation.offset + offsets[power_up]),
        )
    )


def get_animations_palette_index(is_mario: bool, power_up: int) -> int:
    if (power_up == 1 or power_up == 0 or power_up == 3) and not is_mario:
        return 1
    elif (power_up == 1 or power_up == 0 or power_up == 3) and is_mario:
        return 0
    elif power_up == 3:
        return 4
    else:
        return power_up


def load_player_animation(
    animation: PlayerAnimation,
    palette_group: MutablePaletteGroupProtocol,
    is_mario: bool,
    power_up: int,
    offsets: list[int],
    is_kicking: bool = False,
):
    return PlayerAnimationData(
        animation,
        load_animations_graphic_set(animation, power_up, offsets),
        palette_group,
        get_animations_palette_index(is_mario, power_up),
        is_kicking=is_kicking,
    )


def load_player_animation_data(
    animations: list[PlayerAnimation],
    palette_group: MutablePaletteGroupProtocol,
    is_mario: bool,
    power_up: int,
    offsets: list[int],
) -> list[PlayerAnimationData]:
    animation_data: list[PlayerAnimationData] = []
    for idx, animation in enumerate(animations):
        animation_data.append(load_player_animation(animation, palette_group, is_mario, power_up, offsets, idx == 0x2D))
    return animation_data


def load_power_up_palettes() -> MutablePaletteGroupProtocol:
    return MutablePaletteGroup(
        [
            MutablePalette.from_rom(PLAYER_POWER_UPS_PALETTES + address * COLORS_PER_PALETTE)
            for address in range(PLAYER_POWER_UPS_PALETTE_COUNT)
        ]
    )


def load_power_up_offsets() -> list[int]:
    return list(o for o in ROM().bulk_read(PLAYER_POWER_UPS, PLAYER_SUIT_PAGE_OFFSET))


def load_player_animations() -> list[PlayerAnimation]:
    frame_data = ROM().bulk_read(SPRITES_PER_FRAME * PLAYER_FRAMES, PLAYER_FRAME_START)
    offset_data = ROM().bulk_read(PLAYER_FRAMES, PLAYER_FRAME_PAGE_OFFSET)
    return load_animations(frame_data, offset_data)


def load_animations(frame_data: bytes, offset_data: bytes) -> list[PlayerAnimation]:
    animations = []
    for i in range(PLAYER_FRAMES):
        animations.append(PlayerAnimation(bytearray(f - 1 for f in frame_data[i * 6 : (i + 1) * 6]), offset_data[i]))
    return animations


def save_player_animations_to_rom(
    power_up_offsets: bytes, palette_group: bytes, animations: bytes, page_offsets: bytes
):
    rom = ROM()
    rom.bulk_write(bytearray(animations), PLAYER_FRAME_START)
    rom.bulk_write(bytearray(page_offsets), PLAYER_FRAME_PAGE_OFFSET)
    rom.bulk_write(bytearray(palette_group), PLAYER_POWER_UPS_PALETTES)
    rom.bulk_write(bytearray(power_up_offsets), PLAYER_SUIT_PAGE_OFFSET)
