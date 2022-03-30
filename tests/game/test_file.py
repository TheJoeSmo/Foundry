from hypothesis import given
from hypothesis.strategies import booleans, builds, integers
from pytest import fixture, raises

from foundry.game.File import INESHeader, InvalidINESHeader


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
        INESHeader.from_data(bytes())


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


def test_normalized_address_from_expanded_rom_high_bound(expanded_rom_header: INESHeader):
    assert 0x7FFFF + 0x10 == expanded_rom_header.normalized_address(0x3FFFF + 0x10, 16)


@given(integers(min_value=0), headers())
def test_normalized_address_with_same_size_do_not_change(address: int, header: INESHeader):
    assert address == header.normalized_address(address, header.program_size)
