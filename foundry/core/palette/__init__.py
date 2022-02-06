from PySide6.QtGui import QColor

from foundry import data_dir, root_dir
from foundry.smb3parse.constants import BASE_OFFSET, Palette_By_Tileset, PalSet_Maps

MAP_PALETTE_ADDRESS = PalSet_Maps
PRG_SIZE = 0x2000
PALETTE_PRG_NO = 22
PALETTE_BASE_ADDRESS = BASE_OFFSET + PALETTE_PRG_NO * PRG_SIZE
PALETTE_OFFSET_LIST = Palette_By_Tileset
PALETTE_OFFSET_SIZE = 2  # bytes
PALETTE_GROUPS_PER_OBJECT_SET = 8
ENEMY_PALETTE_GROUPS_PER_OBJECT_SET = 4
PALETTES_PER_PALETTES_GROUP = 4
COLORS_PER_PALETTE = 4
COLOR_SIZE = 1  # byte
PALETTE_DATA_SIZE = (
    (PALETTE_GROUPS_PER_OBJECT_SET + ENEMY_PALETTE_GROUPS_PER_OBJECT_SET)
    * PALETTES_PER_PALETTES_GROUP
    * COLORS_PER_PALETTE
)
COLOR_COUNT = 64
BYTES_IN_COLOR = 3 + 1  # bytes + separator
PALETTE_FILE_PATH = data_dir / "palette.json"
palette_file = root_dir.joinpath("data", "Default.pal")

PALETTE_FILE_COLOR_OFFSET = 0x18
offset = 0x18  # first color point
NESPalette: list[QColor] = []
with open(palette_file, "rb") as f:
    color_data = f.read()

for i in range(COLOR_COUNT):
    NESPalette.append(QColor(color_data[offset], color_data[offset + 1], color_data[offset + 2]))

    offset += BYTES_IN_COLOR
