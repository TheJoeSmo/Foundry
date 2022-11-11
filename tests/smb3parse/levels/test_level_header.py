import pytest
from hypothesis import given, strategies

from foundry.smb3parse.levels import (
    DEFAULT_HORIZONTAL_HEIGHT,
    DEFAULT_VERTICAL_WIDTH,
    HEADER_LENGTH,
    is_valid_level_length,
)
from foundry.smb3parse.levels.level_header import LevelHeader
from foundry.smb3parse.objects.tileset import (
    MAX_OBJECT_SET,
    MIN_OBJECT_SET,
    TilesetError,
    is_tileset_index,
)


@given(
    header_bytes=strategies.binary(min_size=9, max_size=9),
    tileset_number=strategies.integers(min_value=MIN_OBJECT_SET, max_value=MAX_OBJECT_SET),
)
def test_construction(header_bytes, tileset_number):
    level_header = LevelHeader(header_bytes, tileset_number)

    if level_header.is_vertical:
        assert level_header.width == DEFAULT_VERTICAL_WIDTH
        assert is_valid_level_length(level_header.height)
    else:
        assert is_valid_level_length(level_header.width)
        assert level_header.height == DEFAULT_HORIZONTAL_HEIGHT

    assert level_header.music_index in range(16)
    assert level_header.time_index in range(4)
    assert level_header.scroll_type_index in range(4)

    assert level_header.start_x_index in range(4)
    assert level_header.start_y_index in range(8)
    assert level_header.start_action in range(8)

    assert level_header.object_palette_index in range(8)
    assert level_header.enemy_palette_index in range(4)
    assert level_header.graphic_set_index in range(32)

    assert is_tileset_index(level_header.jump_tileset_number)


def test_value_error():
    with pytest.raises(ValueError, match="A level header is made up of"):
        LevelHeader(bytearray(HEADER_LENGTH + 1), MIN_OBJECT_SET)

    with pytest.raises(TilesetError):
        LevelHeader(bytearray(HEADER_LENGTH), MAX_OBJECT_SET + 1)


def test_level_1_1():
    tileset_number = 1
    level_header_bytes = bytearray([0x93, 0xBC, 0x06, 0xC0, 0xEA, 0x80, 0x81, 0x01, 0x00])

    level_header = LevelHeader(level_header_bytes, tileset_number)

    assert level_header.width == 0xB0  # blocks
    assert level_header.height == DEFAULT_HORIZONTAL_HEIGHT  # blocks

    assert level_header.music_index == 0
    assert level_header.time_index == 0
    assert level_header.scroll_type_index == 0

    assert not level_header.pipe_ends_level
    assert not level_header.is_vertical

    assert level_header.start_x_index == 0
    assert level_header.start_y_index == 7
    assert level_header.start_action == 0

    assert level_header.object_palette_index == 0
    assert level_header.enemy_palette_index == 0
    assert level_header.graphic_set_index == 1

    assert level_header.jump_enemy_address == 0xC016
    assert level_header.jump_level_address == 0x1FCA3


def test_level_1_1_bonus():
    tileset_number = 1
    level_header_bytes = bytearray([0x82, 0xBB, 0x27, 0xC5, 0x81, 0x85, 0xC1, 0x01, 0x01])

    level_header = LevelHeader(level_header_bytes, tileset_number)

    assert level_header.width == 0x20  # blocks
    assert level_header.height == DEFAULT_HORIZONTAL_HEIGHT  # blocks

    assert level_header.music_index == 1
    assert level_header.time_index == 0
    assert level_header.scroll_type_index == 2

    assert not level_header.pipe_ends_level
    assert not level_header.is_vertical

    assert level_header.start_x_index == 0
    assert level_header.start_y_index == 4
    assert level_header.start_action == 0

    assert level_header.object_palette_index == 5
    assert level_header.enemy_palette_index == 0
    assert level_header.graphic_set_index == 1

    assert level_header.jump_enemy_address == 0xC537
    assert level_header.jump_level_address == 0x1FB92


def test_level_7_1():
    tileset_number = 8
    level_header_bytes = bytearray([0x61, 0xAA, 0x4D, 0xC2, 0x07, 0x80, 0xB1, 0x08, 0x01])

    level_header = LevelHeader(level_header_bytes, tileset_number)

    assert level_header.width == DEFAULT_VERTICAL_WIDTH  # blocks
    assert level_header.height == 0x80  # blocks

    assert level_header.music_index == 1
    assert level_header.time_index == 0
    assert level_header.scroll_type_index == 1

    assert not level_header.pipe_ends_level
    assert level_header.is_vertical

    assert level_header.start_x_index == 0
    assert level_header.start_y_index == 0
    assert level_header.start_action == 0

    assert level_header.object_palette_index == 0
    assert level_header.enemy_palette_index == 0
    assert level_header.graphic_set_index == 8

    assert level_header.jump_enemy_address == 0xC25D
    assert level_header.jump_level_address == 0x1EA71
