from foundry.game.ObjectDefinitions import (
    TilesetDefinition,
    get_object_metadata,
    tileset_to_definition_index,
)
from foundry.smb3parse.constants import TILESET_ENDINGS, TILESET_NAMES


class Tileset:
    def __init__(self, tileset: int):
        self.number = tileset

        self.name = TILESET_NAMES[self.number]

        self.definitions = get_object_metadata().__root__[tileset_to_definition_index[self.number]]

    def object_type(self, domain: int, index: int) -> int:
        domain_offset = domain * 0x1F

        if index <= 0x0F:
            return index + domain_offset
        else:
            return (index >> 4) + domain_offset + 16 - 1

    def get_definition_of(self, object_id: int) -> TilesetDefinition:
        return self.definitions.__root__[object_id]

    def get_ending_offset(self) -> int:
        return TILESET_ENDINGS[self.number]

    def get_object_byte_length(self, domain: int, object_id: int) -> int:
        definition = self.get_definition_of(self.object_type(domain, object_id))
        if definition.is_4byte:
            return 4
        else:
            return 3
