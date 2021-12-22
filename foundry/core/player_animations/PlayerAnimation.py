from attr import attrs


@attrs(slots=True, auto_attribs=True)
class PlayerAnimation:
    """
    A representation of a single player animation.

    Attributes
    ----------
    animations: bytearray
        The frames inside animation.
    offset: int
        The page offset of its graphics, which applies to each power up of the player's.
    """

    animations: bytearray
    offset: int

    def to_bytes(self) -> tuple[bytes, bytes]:
        return self.animations, bytes([self.offset & 0xFF])
