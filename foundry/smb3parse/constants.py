from json import loads

from foundry import tileset_data_path

with open(tileset_data_path, "r") as data:
    _tileset_data = loads(data.read())

TILESET_LEVEL_OFFSET = [int(tileset["location"], 16) for tileset in _tileset_data]
TILESET_NAMES: list[str] = [tileset["name"] for tileset in _tileset_data]
TILESET_RANGES = [range(int(tileset["start"], 16), int(tileset["end"], 16)) for tileset in _tileset_data]
TILESET_ENDINGS: list[int] = [tileset["ending"] for tileset in _tileset_data]

BASE_OFFSET = 0x10  # the size of the rom header identifying the rom

TILE_LEVEL_1 = 0x03
TILE_LEVEL_2 = 0x04
TILE_LEVEL_3 = 0x05
TILE_LEVEL_4 = 0x06
TILE_LEVEL_5 = 0x07
TILE_LEVEL_6 = 0x08
TILE_LEVEL_7 = 0x09
TILE_LEVEL_8 = 0x0A
TILE_LEVEL_9 = 0x0B
TILE_LEVEL_10 = 0x0C
TILE_MUSHROOM_HOUSE_1 = 0x50
TILE_MUSHROOM_HOUSE_2 = 0xE0
TILE_STAR_1 = 0x55
TILE_STAR_2 = 0xE9
TILE_SPIRAL_TOWER_1 = 0x5F
TILE_SPIRAL_TOWER_2 = 0xDF
TILE_DUNGEON_1 = 0x67
TILE_DUNGEON_2 = 0xEB
TILE_QUICKSAND = 0x68
TILE_PYRAMID = 0x69
TILE_PIPE = 0xBC
TILE_POND = 0xBF
TILE_CASTLE_BOTTOM = 0xC9
TILE_BOWSER_CASTLE = 0xCC  # TILE_BOWSERCASTLELL
TILE_HAND_TRAP = 0xE6
TILE_SPADE_HOUSE = 0xE8

OBJ_AUTOSCROLL = 0xD3

POWERUP_MUSHROOM = 0x01
POWERUP_FIREFLOWER = 0x02
POWERUP_RACCOON = 0x03
POWERUP_FROG = 0x04
POWERUP_TANOOKI = 0x05
POWERUP_HAMMER = 0x06
POWERUP_ADDITION_JUDGEMS = 0x07
POWERUP_ADDITION_PWING = 0x08
POWERUP_ADDITION_STARMAN = 0x09

PAGE_A000_ByTileset = 0x3C3F9
PAGE_C000_ByTileset = 0x3C3E6

Level_BG_Pages1 = 0x3D772
Level_BG_Pages2 = 0x3D789

Palette_By_Tileset = 0x377E2
PalSet_Maps = 0x36BE2

Level_TilesetIdx_ByTileset = 0x10010

AScroll_HorizontalInitMove = 0x1ECC
AScroll_MoveEndLoopSelect = 0x13944
AScroll_MovePlayer = 0x13CB0
AScroll_Movement = 0x13959
AScroll_MovementLoop = 0x13B42
AScroll_MovementLoopStart = 0x13B39
AScroll_MovementLoopTicks = 0x13B70
AScroll_MovementRepeat = 0x13A47
AScroll_VelAccel = 0x13B35

Title_DebugMenu = 0x30CD9
Title_PrepForWorldMap = 0x30CCB

Map_ByRowType = 0x193EC
Map_ByScrCol = 0x193FE
Map_ByXHi_InitIndex = 0x193DA
Map_Completable_Tiles = 0x18457
Map_EnterSpecialTiles = 0x14DBF
Map_LevelLayouts = 0x19422
Map_ObjSets = 0x19410
Map_Tile_Layouts = 0x185A8
Tile_Attributes_TS0 = 0x18410
