from typing import List, Optional, Tuple
from warnings import warn

from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QColor, QImage, QPainter, Qt

from foundry.core.graphics_set.GraphicsSet import GraphicsSetProtocol
from foundry.core.palette.PaletteGroup import MutablePaletteGroup
from foundry.core.point.Point import MutablePoint, PointProtocol
from foundry.core.size.Size import MutableSize, SizeProtocol
from foundry.game.File import ROM
from foundry.game.gfx.drawable.Block import Block, get_block
from foundry.game.gfx.objects.GeneratorObject import GeneratorObject
from foundry.game.gfx.objects.ObjectLike import (
    EXPANDS_BOTH,
    EXPANDS_HORIZ,
    EXPANDS_NOT,
    EXPANDS_VERT,
)
from foundry.game.ObjectDefinitions import EndType, GeneratorType, TilesetDefinition
from foundry.game.ObjectSet import ObjectSet
from foundry.smb3parse.objects.object_set import PLAINS_OBJECT_SET

SKY = 0
GROUND = 27

ENDING_STR = {
    EndType.UNIFORM: "Uniform",
    EndType.END_ON_TOP_OR_LEFT: "Top or Left",
    EndType.END_ON_BOTTOM_OR_RIGHT: "Bottom or Right",
    EndType.TWO_ENDS: "Top & Bottom/Left & Right",
}

ORIENTATION_TO_STR = {
    GeneratorType.HORIZONTAL: "Horizontal",
    GeneratorType.VERTICAL: "Vertical",
    GeneratorType.DIAG_DOWN_LEFT: "Diagonal ↙",
    GeneratorType.DESERT_PIPE_BOX: "Desert Pipe Box",
    GeneratorType.DIAG_DOWN_RIGHT: "Diagonal ↘",
    GeneratorType.DIAG_UP_RIGHT: "Diagonal ↗",
    GeneratorType.HORIZ_TO_GROUND: "Horizontal to the Ground",
    GeneratorType.HORIZONTAL_2: "Horizontal Alternative",
    GeneratorType.DIAG_WEIRD: "Diagonal Weird",  # up left?
    GeneratorType.SINGLE_BLOCK_OBJECT: "Single Block",
    GeneratorType.CENTERED: "Centered",
    GeneratorType.PYRAMID_TO_GROUND: "Pyramid to Ground",
    GeneratorType.PYRAMID_2: "Pyramid Alternative",
    GeneratorType.TO_THE_SKY: "To the Sky",
    GeneratorType.ENDING: "Ending",
}

# todo what is this, exactly?
ENDING_OBJECT_OFFSET = 0x1C8F9

# not all objects provide a block index for blank block
BLANK = -1

SCREEN_HEIGHT = 15
SCREEN_WIDTH = 16

MASK_COLOR = [0xFF, 0x33, 0xFF]


class LevelObject(GeneratorObject):
    def __init__(
        self,
        data: bytearray,
        object_set: int,
        palette_group: MutablePaletteGroup,
        graphics_set: GraphicsSetProtocol,
        objects_ref: List["LevelObject"],
        is_vertical: bool,
        index: int,
        size_minimal: bool = False,
    ):
        self.object_set = ObjectSet(object_set)

        self.graphics_set = graphics_set
        self._position = MutablePoint(0, 0)
        self._ignore_rendered_position = False

        self.palette_group = tuple(tuple(c for c in pal) for pal in palette_group)

        self.index_in_level = index
        self.objects_ref = objects_ref
        self.vertical_level = is_vertical

        self.data = data

        self.selected = False

        self.size_minimal = size_minimal

        if self.size_minimal:
            self.ground_level = 0
        else:
            self.ground_level = GROUND

        self.render()

    @property
    def domain(self) -> int:
        return (self.data[0] & 0b1110_0000) >> 5

    @property
    def orientation(self) -> GeneratorType:
        return GeneratorType(self.definition.orientation)

    @property
    def ending(self) -> EndType:
        return EndType(self.definition.ending)

    @property
    def name(self) -> str:
        return self.definition.description

    @property
    def blocks(self) -> list[int]:
        return self.definition.blocks

    @property
    def size(self) -> int:
        return self.definition.size

    @property
    def is_4byte(self) -> bool:
        return self.size == 4

    @property
    def tsa_data(self) -> bytearray:
        return ROM.get_tsa_data(self.object_set.number)

    @property
    def is_single_block(self) -> bool:
        return self.obj_index <= 0x0F

    @property
    def type(self) -> int:
        domain_offset = self.domain * 0x1F

        if self.is_single_block:
            return self.obj_index + domain_offset
        else:
            return (self.obj_index >> 4) + domain_offset + 16 - 1

    @property
    def definition(self) -> TilesetDefinition:
        return self.object_set.get_definition_of(self.type)

    @property
    def obj_index(self) -> int:
        return self.data[2]

    @obj_index.setter
    def obj_index(self, value: int):
        self.data[2] = value

    @property
    def object_info(self):
        return self.object_set.number, self.domain, self.obj_index

    @property
    def length(self) -> int:
        if self.is_single_block:
            return 1
        if self.size == 3:
            return self.obj_index & 0x0F
        else:
            try:
                return self.data[3]
            except IndexError:
                return 0

    @length.setter
    def length(self, value: int):
        if not self.is_single_block:
            if not self.is_4byte:
                index = self.obj_index
                index &= 0xF0
                index |= value & 0x0F
                self.obj_index = index
            else:
                try:
                    self.data[3] = value
                except IndexError:
                    self.data.append(value)

    @property
    def secondary_length(self) -> int:
        if self.size == 3:
            return 1
        else:
            return self.obj_index & 0x0F

    @secondary_length.setter
    def secondary_length(self, value: int):
        if self.size >= 4:
            index = self.obj_index
            index &= 0xF0
            index |= value & 0x0F
            self.obj_index = index

    def render(self):
        self._render()

    def _render(self):
        try:
            self.index_in_level = self.objects_ref.index(self)
        except ValueError:
            # the object has not been added yet, so stick with the one given in the constructor
            pass

        blocks_to_draw = []

        if self.orientation == GeneratorType.TO_THE_SKY:
            for _ in range(self.position.y):
                blocks_to_draw.extend(self.blocks[0 : self.scale.width])

            blocks_to_draw.extend(self.blocks[-self.scale.width :])

        elif self.orientation == GeneratorType.DESERT_PIPE_BOX:
            # segments are the horizontal sections, which are 8 blocks long
            # two of those are drawn per length bit
            # rows are the 4 block high rows Mario can walk in

            is_pipe_box_type_b = self.obj_index // 0x10 == 4

            rows_per_box = self.scale.height
            lines_per_row = 4

            segment_width = self.scale.width
            segments = (self.length + 1) * 2

            for row_number in range(rows_per_box):
                for line in range(lines_per_row):
                    if is_pipe_box_type_b and row_number > 0 and line == 0:
                        # in pipebox type b we do not repeat the horizontal beams
                        line += 1

                    start = line * segment_width
                    stop = start + segment_width

                    for segment_number in range(segments):
                        blocks_to_draw.extend(self.blocks[start:stop])

            if is_pipe_box_type_b:
                # draw another open row
                start = segment_width
            else:
                # draw the first row again to close the box
                start = 0

            stop = start + segment_width

            for segment_number in range(segments):
                blocks_to_draw.extend(self.blocks[start:stop])

            # every line repeats the last block again for some reason
            for end_of_line in range(len(blocks_to_draw), 0, -(self.rendered_size.width - 1)):
                blocks_to_draw.insert(end_of_line, blocks_to_draw[end_of_line - 1])

        elif self.orientation in [
            GeneratorType.DIAG_DOWN_LEFT,
            GeneratorType.DIAG_DOWN_RIGHT,
            GeneratorType.DIAG_UP_RIGHT,
            GeneratorType.DIAG_WEIRD,
        ]:
            if self.ending == EndType.UNIFORM:
                left = [BLANK]
                right = [BLANK]
                slopes = self.blocks

            elif self.ending == EndType.END_ON_TOP_OR_LEFT:
                if self.orientation in [GeneratorType.DIAG_DOWN_RIGHT, GeneratorType.DIAG_UP_RIGHT]:
                    fill_block = self.blocks[0:1]
                    slopes = self.blocks[1:]

                    left = fill_block
                    right = [BLANK]
                elif self.orientation == GeneratorType.DIAG_DOWN_LEFT:
                    fill_block = self.blocks[-1:]
                    slopes = self.blocks[0:-1]

                    right = fill_block
                    left = [BLANK]

                else:
                    fill_block = self.blocks[0:1]
                    slopes = self.blocks[1:]

                    right = [BLANK]
                    left = fill_block

            elif self.ending == EndType.END_ON_BOTTOM_OR_RIGHT:
                fill_block = self.blocks[-1:]
                slopes = self.blocks[0:-1]

                left = [BLANK]
                right = fill_block
            else:
                # todo other two ends not used with diagonals?
                warn(f"{self.name} was not rendered.", RuntimeWarning)
                self.rendered_blocks = []
                return

            rows = []

            if self.scale.height > self.scale.width:
                slope_width = self.scale.width
            else:
                slope_width = len(slopes)

            for y in range(self.rendered_size.height):
                amount_right = (y // self.scale.height) * slope_width
                amount_left = self.rendered_size.width - slope_width - amount_right

                offset = y % self.scale.height

                rows.append(amount_left * left + slopes[offset : offset + slope_width] + amount_right * right)

            if self.orientation in [GeneratorType.DIAG_UP_RIGHT]:
                for row in rows:
                    row.reverse()

            if self.orientation in [GeneratorType.DIAG_DOWN_RIGHT, GeneratorType.DIAG_UP_RIGHT]:
                if not self.scale.height > self.scale.width:
                    rows.reverse()

            if self.orientation == GeneratorType.DIAG_DOWN_RIGHT and self.scale.height > self.scale.width:
                # special case for 60 degree platform wire down right
                for row in rows:
                    row.reverse()

            for row in rows:
                blocks_to_draw.extend(row)

        elif self.orientation in [GeneratorType.PYRAMID_TO_GROUND, GeneratorType.PYRAMID_2]:
            # since pyramids grow horizontally in both directions when extending
            # we need to check for new ground every time it grows
            rendered_size = self.rendered_size

            blank = self.blocks[0]
            left_slope = self.blocks[1]
            left_fill = self.blocks[2]
            right_fill = self.blocks[3]
            right_slope = self.blocks[4]

            for y in range(rendered_size.height):
                blank_blocks = (rendered_size.width // 2) - (y + 1)
                middle_blocks = y  # times two

                blocks_to_draw.extend(blank_blocks * [blank])

                blocks_to_draw.append(left_slope)
                blocks_to_draw.extend(middle_blocks * [left_fill] + middle_blocks * [right_fill])
                blocks_to_draw.append(right_slope)

                blocks_to_draw.extend(blank_blocks * [blank])

        elif self.orientation == GeneratorType.ENDING:
            page_width = 16
            page_limit = page_width - self.position.x % page_width

            for y in range(SKY, GROUND - 1):
                blocks_to_draw.append(self.blocks[0])
                blocks_to_draw.extend([self.blocks[1]] * (self.rendered_size.width))

            # todo magic number
            # ending graphics
            rom_offset = ENDING_OBJECT_OFFSET + self.object_set.get_ending_offset() * 0x60

            rom = ROM()

            ending_graphic_height = 6
            floor_height = 1

            y_offset = GROUND - floor_height - ending_graphic_height

            for y in range(ending_graphic_height):
                for x in range(page_width):
                    block_index = rom.get_byte(rom_offset + y * page_width + x - 1)

                    block_position = (y_offset + y) * (self.rendered_size.width + 1) + x + page_limit + 1
                    blocks_to_draw[block_position] = block_index

            # the ending object is seemingly always 1 block too wide (going into the next screen)
            for end_of_line in range(len(blocks_to_draw) - 1, 0, -(self.rendered_size.width + 1)):
                del blocks_to_draw[end_of_line]

        elif self.orientation == GeneratorType.VERTICAL:
            if self.ending == EndType.UNIFORM:
                for _ in range(self.length + 1):
                    for y in range(self.scale.height):
                        for x in range(self.rendered_size.width):
                            blocks_to_draw.append(self.blocks[y * self.scale.height + x % self.scale.width])

            elif self.ending == EndType.END_ON_TOP_OR_LEFT:
                # in case the drawn object is smaller than its actual size
                for y in range(min(self.scale.height, self.rendered_size.height)):
                    offset = y * self.scale.width
                    blocks_to_draw.extend(self.blocks[offset : offset + self.scale.width])

                additional_rows = self.rendered_size.height - self.scale.height

                # assume only the last row needs to repeat
                # todo true for giant blocks?
                if additional_rows > 0:
                    last_row = self.blocks[-self.scale.width :]

                    for _ in range(additional_rows):
                        blocks_to_draw.extend(last_row)

            elif self.ending == EndType.END_ON_BOTTOM_OR_RIGHT:
                additional_rows = self.rendered_size.height - self.scale.height

                # assume only the first row needs to repeat
                # todo true for giant blocks?
                if additional_rows > 0:
                    last_row = self.blocks[0 : self.scale.width]

                    for _ in range(additional_rows):
                        blocks_to_draw.extend(last_row)

                # in case the drawn object is smaller than its actual size
                for y in range(min(self.scale.height, self.rendered_size.height)):
                    offset = y * self.scale.width
                    blocks_to_draw.extend(self.blocks[offset : offset + self.scale.width])

            elif self.ending == EndType.TWO_ENDS:
                # object exists on ships
                top_row = self.blocks[0 : self.scale.width]
                bottom_row = self.blocks[-self.scale.width :]

                blocks_to_draw.extend(top_row)

                additional_rows = self.rendered_size.height - 2

                # repeat second to last row
                if additional_rows > 0:
                    for _ in range(additional_rows):
                        blocks_to_draw.extend(self.blocks[-2 * self.scale.width : -self.scale.width])

                if self.rendered_size.height > 1:
                    blocks_to_draw.extend(bottom_row)

        elif self.orientation in [GeneratorType.HORIZONTAL, GeneratorType.HORIZ_TO_GROUND, GeneratorType.HORIZONTAL_2]:
            if self.ending == EndType.UNIFORM and not self.is_4byte:
                for y in range(self.rendered_size.height):
                    if self.is_single_block:
                        blocks_to_draw.extend(self.blocks[: self.scale.width])
                    else:
                        blocks_to_draw.extend(
                            self.blocks[y * self.scale.width : (y + 1) * self.scale.width] * (self.length + 1)
                        )

            elif self.ending == EndType.UNIFORM and self.is_4byte:
                # 4 byte objects
                top = self.blocks[0:1]
                bottom = self.blocks[-1:]

                if self.orientation == GeneratorType.HORIZONTAL_2:
                    for _ in range(0, self.rendered_size.height - 1):
                        blocks_to_draw.extend(self.rendered_size.width * top)

                    blocks_to_draw.extend(self.rendered_size.width * bottom)
                else:
                    blocks_to_draw.extend(self.rendered_size.width * top)

                    for _ in range(1, self.rendered_size.height):
                        blocks_to_draw.extend(self.rendered_size.width * bottom)

            elif self.ending == EndType.END_ON_TOP_OR_LEFT:
                for y in range(self.rendered_size.height):
                    offset = y * self.scale.width

                    blocks_to_draw.append(self.blocks[offset])

                    for x in range(1, self.rendered_size.width):
                        blocks_to_draw.append(self.blocks[offset + 1])

            elif self.ending == EndType.END_ON_BOTTOM_OR_RIGHT:
                for y in range(self.rendered_size.height):
                    offset = y * self.scale.width

                    for x in range(self.rendered_size.width - 1):
                        blocks_to_draw.append(self.blocks[offset])

                    blocks_to_draw.append(self.blocks[offset + self.scale.width - 1])

            elif self.ending == EndType.TWO_ENDS:
                if self.scale.width > len(self.blocks):
                    raise ValueError(f"{self} does not provide enough blocks to fill a row.")
                else:
                    start = 0
                    end = self.scale.width

                for y in range(self.scale.height):
                    new_start = y * self.scale.width
                    new_end = (y + 1) * self.scale.width

                    if new_end > len(self.blocks):
                        # repeat the last line of blocks to fill the object
                        pass
                    else:
                        start = new_start
                        end = new_end

                    left, *middle, right = self.blocks[start:end]

                    blocks_to_draw.append(left)
                    blocks_to_draw.extend(middle * (self.rendered_size.width - 2))
                    blocks_to_draw.append(right)

                if not len(blocks_to_draw) % self.scale.height == 0:
                    warn(f"Blocks to draw are not divisible by height. {self}", RuntimeWarning)

                new_width = int(len(blocks_to_draw) / self.scale.height)

                top_row = blocks_to_draw[0:new_width]
                middle_blocks = blocks_to_draw[new_width : new_width * 2]
                bottom_row = blocks_to_draw[-new_width:]

                blocks_to_draw = top_row

                for y in range(1, self.rendered_size.height - 1):
                    blocks_to_draw.extend(middle_blocks)

                if self.rendered_size.height > 1:
                    blocks_to_draw.extend(bottom_row)
        else:
            if not self.orientation == GeneratorType.SINGLE_BLOCK_OBJECT:
                warn(f"Didn't render {self.name}", RuntimeWarning)
                # breakpoint()

            if self.name.lower() == "black boss room background":
                blocks_to_draw = SCREEN_WIDTH * SCREEN_HEIGHT * [self.blocks[0]]

        # for not yet implemented objects and single block objects
        if blocks_to_draw:
            self.rendered_blocks = blocks_to_draw
        else:
            self.rendered_blocks = self.blocks

        self.rect = QRect(
            self.rendered_position.x, self.rendered_position.y, self.rendered_size.width, self.rendered_size.height
        )

    def draw(self, painter: QPainter, block_length, transparent, blocks: Optional[list[Block]] = None):
        size = self.rendered_size
        size.width = max(size.width, 1)

        for index, block_index in enumerate(self.rendered_blocks):
            if block_index == BLANK:
                continue

            x = self.rendered_position.x + index % size.width
            y = self.rendered_position.y + index // size.width

            self._draw_block(painter, block_index, x, y, block_length, transparent, blocks=blocks)

    def _draw_block(
        self, painter: QPainter, block_index, x, y, block_length, transparent, blocks: Optional[list[Block]] = None
    ):
        if blocks is not None:
            block = blocks[block_index if block_index <= 0xFF else ROM().get_byte(block_index)]
        else:
            block = get_block(
                block_index,
                self.palette_group,
                self.graphics_set,
                bytes(self.tsa_data),
            )

        block.draw(
            painter,
            x * block_length,
            y * block_length,
            block_length=block_length,
            selected=self.selected,
            transparent=transparent,
        )

    def move_by(self, dx: int, dy: int):
        self.position = MutablePoint(self.position.x + dx, self.position.y + dy)

    @property
    def position(self) -> PointProtocol:
        y = self.data[0] & 0b0001_1111
        x = self.data[1]

        if self.vertical_level:
            offset = (x // SCREEN_WIDTH) * SCREEN_HEIGHT

            y += offset
            x %= SCREEN_WIDTH

        return MutablePoint(x, y)

    @position.setter
    def position(self, position: PointProtocol) -> None:
        x, y = position.x, position.y

        # todo also check for the upper bounds
        x = max(0, x)

        if self.vertical_level:
            # todo from vertical to non-vertical is bugged, because it
            # seems like you can't convert the coordinates 1:1
            # there seems to be ambiguity

            offset = y // SCREEN_HEIGHT

            x += offset * SCREEN_WIDTH
            y %= SCREEN_HEIGHT

        self.data[0] = (self.data[0] & 0b1110_0000) + y
        self.data[1] = x

        self._render()

    @property
    def rendered_position(self) -> PointProtocol:
        if self._ignore_rendered_position:
            return MutablePoint(0, 0)
        elif self.orientation == GeneratorType.TO_THE_SKY:
            return MutablePoint(self.position.x, SKY)
        elif self.orientation in [GeneratorType.DIAG_UP_RIGHT]:
            return MutablePoint(self.position.x, self.position.y - self.rendered_size.height + 1)
        elif self.orientation in [GeneratorType.DIAG_DOWN_LEFT]:
            if self.object_set.number == 3 or self.object_set.number == 14:  # Sky or Hilly tileset
                return MutablePoint(
                    self.position.x - (self.rendered_size.width - self.scale.width + 1), self.position.y
                )
            else:
                return MutablePoint(self.position.x - (self.rendered_size.width - self.scale.width), self.position.y)

        elif self.orientation in [GeneratorType.PYRAMID_TO_GROUND, GeneratorType.PYRAMID_2]:
            return MutablePoint(self.position.x - (self.rendered_size.width // 2) + 1, self.position.y)
        elif self.name.lower() == "black boss room background":
            return MutablePoint(self.position.x // SCREEN_WIDTH * SCREEN_WIDTH, 0)
        return self.position

    @property
    def scale(self) -> SizeProtocol:
        return MutableSize(self.definition.bmp_width, self.definition.bmp_height)

    @property
    def rendered_size(self) -> SizeProtocol:
        if self.orientation == GeneratorType.TO_THE_SKY:
            return MutableSize(self.scale.width, self.position.y + self.scale.height - 1)
        elif self.orientation == GeneratorType.DESERT_PIPE_BOX:
            segments = (self.length + 1) * 2
            return MutableSize(segments * self.scale.width + 1, 4 * self.scale.height)
        elif self.orientation in [
            GeneratorType.DIAG_DOWN_LEFT,
            GeneratorType.DIAG_DOWN_RIGHT,
            GeneratorType.DIAG_UP_RIGHT,
            GeneratorType.DIAG_WEIRD,
        ]:
            if self.ending == EndType.UNIFORM:
                return MutableSize((self.length + 1) * self.scale.width, (self.length + 1) * self.scale.height)
            elif self.ending == EndType.END_ON_TOP_OR_LEFT:
                return MutableSize((self.length + 1) * (self.scale.width - 1), (self.length + 1))
            else:
                return MutableSize((self.length + 1) * (self.scale.width - 1), (self.length + 1) * self.scale.height)
        elif self.orientation in [GeneratorType.PYRAMID_TO_GROUND, GeneratorType.PYRAMID_2]:
            size = MutableSize(1, 1)
            for y in range(self.position.y, self.ground_level):
                size = MutableSize(2 * (y - self.position.y), (y - self.position.y))
                bottom_row = QRect(self.position.x, y, size.width, 1)
                if any(
                    [
                        bottom_row.intersects(obj.get_rect()) and y == obj.get_rect().top()
                        for obj in self.objects_ref[0 : self.index_in_level]
                    ]
                ):
                    break
            return size
        elif self.orientation == GeneratorType.ENDING:
            page_width = 16
            page_limit = page_width - self.position.x % page_width
            return MutableSize(page_width + page_limit, (GROUND - 1) - SKY)
        elif self.orientation == GeneratorType.VERTICAL:
            size = MutableSize(self.scale.width, self.length + 1)

            if self.ending == EndType.UNIFORM:
                if self.is_4byte:
                    # there is one VERTICAL 4-byte object: Vertically oriented X-blocks
                    # the width is the primary expansion
                    size.width = (self.obj_index & 0x0F) + 1

                # adjust height for giant blocks, so that the rect is correct
                size.height *= self.scale.height
            return size
        elif self.orientation in [GeneratorType.HORIZONTAL, GeneratorType.HORIZ_TO_GROUND, GeneratorType.HORIZONTAL_2]:
            size = MutableSize(self.length + 1, self.scale.height)

            downwards_extending_vine = 1, 0, 0x06
            wooden_sky_pole = 4, 0, 0x04

            if self.object_info in [downwards_extending_vine, wooden_sky_pole]:
                size.width -= 1
            if self.orientation == GeneratorType.HORIZ_TO_GROUND:
                # to the ground only, until it hits something
                for y in range(self.position.y, self.ground_level):
                    bottom_row = QRect(self.position.x, y, size.width, 1)

                    if any(
                        [
                            bottom_row.intersects(obj.get_rect()) and y == obj.get_rect().top()
                            for obj in self.objects_ref[0 : self.index_in_level]
                        ]
                    ):
                        size.height = y - self.position.y
                        break
                else:
                    # nothing underneath this object, extend to the ground
                    size.height = self.ground_level - self.position.y

                if self.is_single_block:
                    size.width = self.length

                size.height = max(min(self.scale.height, 2), size.height)

            elif self.orientation == GeneratorType.HORIZONTAL_2 and self.ending == EndType.TWO_ENDS:
                # floating platforms seem to just be one shorter for some reason
                size.width -= 1
            else:
                size.height = self.scale.height * (self.secondary_length)

            if self.ending == EndType.UNIFORM and not self.is_4byte:
                size.width *= self.scale.width  # in case of giant blocks
            elif self.ending == EndType.UNIFORM and self.is_4byte:
                size.height = self.scale.height + self.secondary_length

                # ceilings are one shorter than normal
                if self.scale.height > self.scale.width:
                    size.height -= 1

            elif self.ending == EndType.TWO_ENDS:
                if self.orientation == GeneratorType.HORIZONTAL and self.is_4byte:
                    # flat ground objects have an artificial limit of 2 lines
                    if (
                        self.object_set.number == PLAINS_OBJECT_SET
                        and self.domain == 0
                        and self.obj_index in range(0xC0, 0xE0)
                    ):
                        size.height = min(2, self.secondary_length + 1)
                    else:
                        size.height = self.secondary_length + 1
            return size
        elif self.name.lower() == "black boss room background":
            return MutableSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        return self.scale

    @property
    def horizontally_expands(self) -> bool:
        return bool(self.expands() & EXPANDS_HORIZ)

    @property
    def vertically_expands(self) -> bool:
        return bool(self.expands() & EXPANDS_VERT)

    def expands(self):
        expands = EXPANDS_NOT

        if self.is_single_block:
            return expands

        if self.is_4byte:
            expands |= EXPANDS_BOTH

        elif self.orientation in [
            GeneratorType.HORIZONTAL,
            GeneratorType.HORIZONTAL_2,
            GeneratorType.HORIZ_TO_GROUND,
        ] or self.orientation in [
            GeneratorType.DIAG_DOWN_LEFT,
            GeneratorType.DIAG_DOWN_RIGHT,
            GeneratorType.DIAG_UP_RIGHT,
            GeneratorType.DIAG_WEIRD,
        ]:
            expands |= EXPANDS_HORIZ

        elif self.orientation in [GeneratorType.VERTICAL, GeneratorType.DIAG_WEIRD]:
            expands |= EXPANDS_VERT

        return expands

    def primary_expansion(self):
        if self.orientation in [
            GeneratorType.HORIZONTAL,
            GeneratorType.HORIZONTAL_2,
            GeneratorType.HORIZ_TO_GROUND,
        ] or self.orientation in [
            GeneratorType.DIAG_DOWN_LEFT,
            GeneratorType.DIAG_DOWN_RIGHT,
            GeneratorType.DIAG_UP_RIGHT,
            GeneratorType.DIAG_WEIRD,
        ]:
            if self.is_4byte:
                return EXPANDS_VERT
            else:
                return EXPANDS_HORIZ
        elif self.orientation in [GeneratorType.VERTICAL]:
            if self.is_4byte:
                return EXPANDS_HORIZ
            else:
                return EXPANDS_VERT
        else:
            return EXPANDS_BOTH

    def __contains__(self, item: Tuple[int, int]) -> bool:
        x, y = item

        return self.point_in(x, y)

    def point_in(self, x: int, y: int) -> bool:
        return self.rect.contains(x, y)

    def get_status_info(self) -> List[tuple]:
        return [
            ("x", self.rendered_position.x),
            ("y", self.rendered_position.y),
            ("Width", self.rendered_size.width),
            ("Height", self.rendered_size.height),
            ("Orientation", ORIENTATION_TO_STR[self.orientation]),
            ("Ending", ENDING_STR[self.ending]),
        ]

    def display_size(self, zoom_factor: int = 1):
        return (
            QSize(self.rendered_size.width * Block.SIDE_LENGTH, self.rendered_size.height * Block.SIDE_LENGTH)
            * zoom_factor
        )

    def as_image(self) -> QImage:
        self._ignore_rendered_position = True

        image = QImage(
            QSize(self.rendered_size.width * Block.SIDE_LENGTH, self.rendered_size.height * Block.SIDE_LENGTH),
            QImage.Format_RGB888,
        )

        bg_color = QColor(*MASK_COLOR).rgb()

        image.fill(bg_color)
        mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
        image.setAlphaChannel(mask)

        painter = QPainter(image)

        self.draw(painter, Block.SIDE_LENGTH, True)

        self._ignore_rendered_position = False

        return image

    def to_bytes(self) -> bytearray:
        data = bytearray()

        if self.vertical_level:
            # todo from vertical to non-vertical is bugged, because it
            # seems like you can't convert the coordinates 1:1
            # there seems to be ambiguity

            offset = self.position.y // SCREEN_HEIGHT

            x_position = self.position.x + offset * SCREEN_WIDTH
            y_position = self.position.y % SCREEN_HEIGHT
        else:
            x_position = self.position.x
            y_position = self.position.y

        if self.orientation in [GeneratorType.PYRAMID_TO_GROUND, GeneratorType.PYRAMID_2]:
            x_position = self.rendered_position.x - 1 + self.rendered_size.width // 2

        data.append((self.domain << 5) | y_position)
        data.append(x_position)

        data.append(self.obj_index)

        if self.is_4byte:
            data.append(self.length)

        return data

    def __repr__(self) -> str:
        return f"LevelObject {self.name} at {self.position.x}, {self.position.y}"

    def __eq__(self, other):
        if not isinstance(other, LevelObject):
            return False
        else:
            return self.to_bytes() == other.to_bytes()

    def __lt__(self, other):
        return self.index_in_level < other.index_in_level
