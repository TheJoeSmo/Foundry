from foundry.game.ObjectDefinitions import (
    TilesetDefinition,
    object_metadata,
    object_set_to_definition,
)
from foundry.smb3parse.constants import TILESET_ENDINGS, TILESET_NAMES


class ObjectSet:
    def __init__(self, object_set_number: int):
        self.number = object_set_number

        self.name = TILESET_NAMES[self.number]

        self.definitions = object_metadata.__root__[object_set_to_definition[self.number]]

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
