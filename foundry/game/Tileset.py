from foundry.game.ObjectDefinitions import (
    TilesetDefinition,
    get_object_metadata,
    tileset_to_definition_index,
)
from foundry.smb3parse.constants import TILESET_ENDINGS, TILESET_NAMES


class Tileset:
    """
    Class representing a tileset in Super Mario Bros. 3.
    """

    def __init__(self, tileset: int) -> None:
        """
        Constructs a Tileset object.

        Parameters
        ----------
        tileset : int
            The number representing the tileset.
        """
        self.number = tileset

        self.name = TILESET_NAMES[self.number]

        self.definitions = get_object_metadata().__root__[tileset_to_definition_index[self.number]]

    def object_type(self, domain: int, index: int) -> int:
        """
        Determines the object type based on domain and index.

        Parameters
        ----------
        domain : int
            The domain number.
        index : int
            The object index.

        Returns
        -------
        int
            The object type.
        """
        domain_offset = domain * 0x1F

        if index <= 0x0F:
            return index + domain_offset
        else:
            return (index >> 4) + domain_offset + 16 - 1

    def get_definition_of(self, object_id: int) -> TilesetDefinition:
        """
        Gets the TilesetDefinition object of the specified object ID.

        Parameters
        ----------
        object_id : int
            The object ID.

        Returns
        -------
        TilesetDefinition
            The TilesetDefinition object of the specified object ID.
        """
        return self.definitions.__root__[object_id]

    def get_ending_offset(self) -> int:
        """
        Gets the ending offset of an object in a tileset.

        Returns
        -------
        int
            The ending offset of the object.
        """
        return TILESET_ENDINGS[self.number]

    def get_object_byte_length(self, domain: int, object_id: int) -> int:
        """
        Gets the byte length of the object.

        Parameters
        ----------
        domain : int
            The domain number.
        object_id : int
            The object ID.

        Returns
        -------
        int
            The byte length of the object.
        """
        return 4 if self.get_definition_of(self.object_type(domain, object_id)).is_4byte else 3
