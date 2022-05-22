from PySide6.QtGui import QColor
from pytest import fixture

from foundry.core.palette import Color, ColorPalette, Palette, PaletteGroup


@fixture
def simple_color_palette():
    return ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9)))


def test_color_initialization_simple():
    Color(0, 1, 2)


def test_color_initialization_with_alpha():
    Color(0, 1, 2, 3)


def test_color_initialization_minimum():
    Color(0, 0, 0, 0)


def test_color_initialization_maximum():
    Color(255, 255, 255, 255)


def test_color_qcolor():
    assert Color(0, 1, 2, 3).qcolor == QColor(0, 1, 2, 3)


def test_color_validation_simple():
    assert Color(0, 1, 2) == Color.validate({"red": 0, "green": 1, "blue": 2})


def test_color_validation_with_alpha():
    assert Color(0, 1, 2, 3) == Color.validate({"red": 0, "green": 1, "blue": 2, "alpha": 3})


def test_color_palette_initialization():
    ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9)))


def test_color_pallete_length():
    assert 3 == len(ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9))))


def test_color_palette_get_item():
    color_palette = ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9)))
    assert Color(0, 1, 2) == color_palette[0]
    assert Color(3, 4, 5) == color_palette[1]
    assert Color(6, 7, 8, 9) == color_palette[2]


def test_color_palette_iter():
    i = iter(ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9))))
    assert Color(0, 1, 2) == next(i)
    assert Color(3, 4, 5) == next(i)
    assert Color(6, 7, 8, 9) == next(i)


def test_color_palette_default_color():
    color_palette = ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9)))
    assert color_palette.default_color in color_palette


def test_palette_initialization(simple_color_palette):
    Palette((0, 1, 2), simple_color_palette)


def test_palette_initialization_from_default():
    Palette((0, 1, 2, 3))


def test_palette_colors(simple_color_palette):
    assert [simple_color_palette[0], simple_color_palette[1], simple_color_palette[2]] == Palette(
        (0, 1, 2), simple_color_palette
    ).colors


def test_palette_qcolors(simple_color_palette):
    assert [simple_color_palette[0].qcolor, simple_color_palette[1].qcolor, simple_color_palette[2].qcolor] == Palette(
        (0, 1, 2), simple_color_palette
    ).qcolors


def test_palette_get_item(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)
    assert 0 == palette[0]
    assert 2 == palette[1]
    assert 1 == palette[2]


def test_palette_iter(simple_color_palette):
    i = iter(Palette((0, 2, 1), simple_color_palette))
    assert 0 == next(i)
    assert 2 == next(i)
    assert 1 == next(i)


def test_palette_find_palette_mutations_equal(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)

    assert {} == palette.find_palette_mutations(palette)


def test_palette_find_palette_mutations_simple(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)

    assert {0: 1} == palette.find_palette_mutations(Palette((1, 2, 1), simple_color_palette))


def test_palette_find_palette_mutations_complex(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)

    assert {0: 1, 1: 0, 2: 2} == palette.find_palette_mutations(Palette((1, 0, 2), simple_color_palette))


def test_palette_from_palette_empty(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)
    palette = Palette.from_palette(palette, {})

    assert Palette((0, 2, 1), simple_color_palette) == palette


def test_palette_from_palette_simple(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)
    palette = Palette.from_palette(palette, {0: 1})

    assert Palette((1, 2, 1), simple_color_palette) == palette


def test_palette_from_palette_normal(simple_color_palette):
    palette = Palette((0, 2, 1), simple_color_palette)
    palette = Palette.from_palette(palette, {0: 1, 2: 0})

    assert Palette((1, 2, 0), simple_color_palette) == palette


def test_palette_group_initialization():
    PaletteGroup((Palette((0, 1, 2)), Palette((3, 4, 5)), Palette((6, 7, 8)), Palette((9, 10, 11))))


def test_palette_group_get_item():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((3, 4, 5)), Palette((6, 7, 8)), Palette((9, 10, 11))))
    assert Palette((0, 1, 2)) == palette_group[0]
    assert Palette((3, 4, 5)) == palette_group[1]
    assert Palette((6, 7, 8)) == palette_group[2]
    assert Palette((9, 10, 11)) == palette_group[3]


def test_palette_group_iter():
    i = iter(PaletteGroup((Palette((0, 1, 2)), Palette((3, 4, 5)), Palette((6, 7, 8)), Palette((9, 10, 11)))))
    assert Palette((0, 1, 2)) == next(i)
    assert Palette((3, 4, 5)) == next(i)
    assert Palette((6, 7, 8)) == next(i)
    assert Palette((9, 10, 11)) == next(i)


def test_palette_group_background_color():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8))))
    assert palette_group[0].colors[0] == palette_group.background_color


def test_palette_group_background_qcolor():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8))))
    assert palette_group[0].qcolors[0] == palette_group.background_qcolor


def test_palette_group_from_palette_group_simple():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8))))
    palette_group = PaletteGroup.from_palette_group(palette_group, {0: {1: 2}})

    assert (
        PaletteGroup((Palette((0, 2, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8)))) == palette_group
    )


def test_palette_group_from_palette_group_complex():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8))))
    palette_group = PaletteGroup.from_palette_group(palette_group, {0: {1: 2, 2: 1}, 2: {1: 2}})

    assert (
        PaletteGroup((Palette((0, 2, 1)), Palette((0, 3, 4)), Palette((0, 2, 6)), Palette((0, 7, 8)))) == palette_group
    )


def test_palette_group_from_palette_group_background_color_simple():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8))))
    palette_group = PaletteGroup.from_palette_group(palette_group, {0: {0: 9}})

    assert (
        PaletteGroup((Palette((9, 1, 2)), Palette((9, 3, 4)), Palette((9, 5, 6)), Palette((9, 7, 8)))) == palette_group
    )


def test_palette_group_from_palette_group_background_color_complex():
    palette_group = PaletteGroup((Palette((0, 1, 2)), Palette((0, 3, 4)), Palette((0, 5, 6)), Palette((0, 7, 8))))
    palette_group = PaletteGroup.from_palette_group(palette_group, {0: {0: 9, 2: 1}, 2: {1: 2}})

    assert (
        PaletteGroup((Palette((9, 1, 1)), Palette((9, 3, 4)), Palette((9, 2, 6)), Palette((9, 7, 8)))) == palette_group
    )
