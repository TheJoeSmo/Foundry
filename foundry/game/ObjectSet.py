from foundry.game.ObjectDefinitions import ObjectDefinition, load_object_definitions
from foundry.smb3parse.constants import TILESET_ENDINGS, TILESET_NAMES
from foundry.smb3parse.objects.object_set import ENEMY_ITEM_OBJECT_SET


class ObjectSet:
    def __init__(self, object_set_number: int):
        self.number = object_set_number

        if self.number == ENEMY_ITEM_OBJECT_SET:
            self.name = "Enemy Object Set"
        else:
            self.name = TILESET_NAMES[self.number]

        self.definitions = load_object_definitions(self.number)

    def object_type(self, domain: int, index: int) -> int:
        if self.number == ENEMY_ITEM_OBJECT_SET:
            return index

        if index <= 0x0F:
            return index + domain
        else:
            return (index >> 4) + domain + 16 - 1

    def get_definition_of(self, object_id: int) -> ObjectDefinition:
        return self.definitions[object_id]

    def get_ending_offset(self) -> int:
        if self.number == ENEMY_ITEM_OBJECT_SET:
            raise ValueError(f"This method shouldn't be called for the {self.name}")

        return TILESET_ENDINGS[self.number]

    def get_object_byte_length(self, domain: int, object_id: int) -> int:
        if self.number == ENEMY_ITEM_OBJECT_SET:
            raise ValueError(f"This method shouldn't be called for the {self.name}")

        definition = self.get_definition_of(self.object_type(domain, object_id))
        if definition.is_4byte:
            return 4
        else:
            return 3
