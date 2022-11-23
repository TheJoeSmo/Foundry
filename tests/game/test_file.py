from hypothesis import given
from hypothesis.strategies import booleans, builds, integers
from pytest import fixture, mark, raises

from foundry.game.File import ROM, INESHeader, InvalidINESHeader


@fixture
def rom_header():
    return INESHeader(16, 16, 3, True, False)


@fixture
def expanded_rom_header():
    return INESHeader(32, 32, 3, True, False)


def headers():
    return builds(
        INESHeader, integers(min_value=2), integers(min_value=2), integers(min_value=0), booleans(), booleans()
    )


@given(integers(min_value=0), integers(min_value=0), integers(min_value=0), booleans(), booleans())
def test_initializiation(prg_size, chr_size, mapper, mirroring, memory_backed):
    INESHeader(prg_size, chr_size, mapper, mirroring, memory_backed)


@given(headers())
def test_vertical_mirroring(header: INESHeader):
    assert header.horizontal_mirroring != header.vertical_mirroring


@given(headers())
def test_more_program_banks_create_larger_file(header: INESHeader):
    assert (
        INESHeader(
            header.program_banks + 1,
            header.character_banks,
            header.mapper,
            header.horizontal_mirroring,
            header.battery_backed_ram,
        ).program_size
        > header.program_size
    )


@given(headers())
def test_program_bank_size(header: INESHeader):
    assert (
        INESHeader(
            header.program_banks + 1,
            header.character_banks,
            header.mapper,
            header.horizontal_mirroring,
            header.battery_backed_ram,
        ).program_size
        - header.program_size
        == INESHeader.PROGRAM_BANK_SIZE
    )


@given(headers())
def test_more_character_banks_create_larger_file(header: INESHeader):
    assert (
        INESHeader(
            header.program_banks,
            header.character_banks + 1,
            header.mapper,
            header.horizontal_mirroring,
            header.battery_backed_ram,
        ).character_size
        > header.character_size
    )


@given(headers())
def test_character_bank_size(header: INESHeader):
    assert (
        INESHeader(
            header.program_banks,
            header.character_banks + 1,
            header.mapper,
            header.horizontal_mirroring,
            header.battery_backed_ram,
        ).character_size
        - header.character_size
        == INESHeader.CHARACTER_BANK_SIZE
    )


def test_empty_data():
    with raises(InvalidINESHeader):
        INESHeader.from_data(b"")


def test_too_small_data():
    with raises(InvalidINESHeader):
        INESHeader.from_data(bytes([0x4E, 0x45, 0x53, 0x1A]))


def test_not_following_header():
    with raises(InvalidINESHeader):
        INESHeader.from_data(bytes([0x4D, 0x45, 0x53, 0x1A] + [0] * 100))


def test_program_address_start():
    assert 0 == INESHeader.program_address(INESHeader.INES_HEADER_SIZE)


def test_address_is_global_at_zero():
    assert not INESHeader.address_is_global(0, 10)


def test_address_is_global_at_border():
    assert not INESHeader.address_is_global(8 * INESHeader.PROGRAM_BANK_SIZE, 10)


def test_address_is_global_at_border_and_one():
    assert INESHeader.address_is_global(9 * INESHeader.PROGRAM_BANK_SIZE + INESHeader.INES_HEADER_SIZE + 1, 10)


def test_address_is_global_at_end_of_file():
    assert INESHeader.address_is_global(10 * INESHeader.PROGRAM_BANK_SIZE + INESHeader.INES_HEADER_SIZE - 1, 10)


@given(integers(min_value=0))
def test_relative_address(address: int):
    assert INESHeader.program_address(address) & (INESHeader.PROGRAM_BANK_SIZE - 1) == INESHeader.relative_address(
        address
    )


def test_normalized_address_from_expanded_rom_low_bound(expanded_rom_header: INESHeader):
    assert 0x7C000 + 0x10 == expanded_rom_header.normalized_address(0x3C010, 16)


def test_normalized_address_from_expanded_rom_tsa_data_offset_normal(rom_header: INESHeader):
    assert 0x3C3F9 == rom_header.normalized_address(0x3C3F9, 16)


def test_normalized_address_from_expanded_rom_tsa_data_offset_expanded(expanded_rom_header: INESHeader):
    assert 0x7C3F9 == expanded_rom_header.normalized_address(0x3C3F9, 16)


def test_normalized_address_from_expanded_rom_high_bound(expanded_rom_header: INESHeader):
    assert 0x7FFFF + 0x10 == expanded_rom_header.normalized_address(0x3FFFF + 0x10, 16)


@given(integers(min_value=0), headers())
def test_normalized_address_with_same_size_do_not_change(address: int, header: INESHeader):
    assert address == header.normalized_address(address, header.program_size)


"""
Tests to ensure get and set item work properly
"""


@mark.parametrize(
    "index,expected",
    [
        (0, 0x4E),
        (0x2010, 0xA0),
        (0x3C010, 0x00),
        (0x4000F, 0xF7),
        (
            slice(0, 0x10),
            bytearray([0x4E, 0x45, 0x53, 0x1A, 0x10, 0x10, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
        ),
        (
            slice(0x2010, 0x2020),
            bytearray([0xA0, 0xD3, 0x7B, 0xA2, 0x21, 0xA3, 0xA0, 0xD3, 0xA6, 0xA3, 0xDE, 0xA3, 0xAE, 0xA4, 0x2D, 0xAD]),
        ),
        (
            slice(0x3C010, 0x3C020),
            bytearray([0x0, 0x60, 0xB0, 0x61, 0x60, 0x63, 0x10, 0x65, 0xC0, 0x66, 0x70, 0x68, 0x20, 0x6A, 0xD0, 0x6B]),
        ),
    ],
)
def test_getitem(rom_singleton: ROM, index: int | slice, expected: int | bytearray) -> None:
    assert expected == rom_singleton[index]


"""
Tests to ensure that the ROM is being read from properly.
"""


def test_get_byte_start(rom_singleton: ROM):
    assert 0x4E == rom_singleton.get_byte(0)


def test_get_byte_regular_program_bank(rom_singleton: ROM):
    assert 0xA0 == rom_singleton.get_byte(0x2010)


def test_get_byte_global_program_bank(rom_singleton: ROM):
    assert 0x00 == rom_singleton.get_byte(0x3C010)


def test_get_byte_end(rom_singleton: ROM):
    assert 0xF7 == rom_singleton.get_byte(0x3FFFF + 0x10)


def test_bulk_read_header(rom_singleton: ROM):
    assert bytes(
        [0x4E, 0x45, 0x53, 0x1A, 0x10, 0x10, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    ) == rom_singleton.bulk_read(0x10, 0)


def test_bulk_read_regular_program_bank(rom_singleton: ROM):
    assert bytes(
        [0xA0, 0xD3, 0x7B, 0xA2, 0x21, 0xA3, 0xA0, 0xD3, 0xA6, 0xA3, 0xDE, 0xA3, 0xAE, 0xA4, 0x2D, 0xAD]
    ) == rom_singleton.bulk_read(0x10, 0x2010)


def test_bulk_read_global_program_bank(rom_singleton: ROM):
    assert bytes(
        [0x0, 0x60, 0xB0, 0x61, 0x60, 0x63, 0x10, 0x65, 0xC0, 0x66, 0x70, 0x68, 0x20, 0x6A, 0xD0, 0x6B]
    ) == rom_singleton.bulk_read(0x10, 0x3C010)


def test_bulk_write_header(rom_singleton: ROM):
    rom_singleton.bulk_write(bytearray([0] * 0x10), 0)
    assert bytes([0] * 0x10) == rom_singleton.bulk_read(0x10, 0)


def test_bulk_write_regular_program_bank(rom_singleton: ROM):
    rom_singleton.bulk_write(bytearray([0] * 0x10), 0x2010)
    assert bytes([0] * 0x10) == rom_singleton.bulk_read(0x10, 0x2010)


def test_bulk_write_global_program_bank(rom_singleton: ROM):
    rom_singleton.bulk_write(bytearray([0] * 0x10), 0x3C010)
    assert bytes([0] * 0x10) == rom_singleton.bulk_read(0x10, 0x3C010)


def test_bulk_write_end(rom_singleton: ROM):
    rom_singleton.bulk_write(bytearray([0] * 0x10), 0x3FFFF)
    assert bytes([0] * 0x10) == rom_singleton.bulk_read(0x10, 0x3FFFF)


def test_tagged_file(rom_singleton: ROM):
    assert rom_singleton.rom_data.find(rom_singleton.MARKER_VALUE) > 0
