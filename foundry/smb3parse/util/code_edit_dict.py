""" Concrete implementation of the CodeEdit class using a dictionary lookup.

This CodeEdit uses a dictionary as the edit values.  The keys represent the
abstract option and the values are the byte data needing to be programmed
into memory.
"""
from typing import Any

from foundry.smb3parse.util.code_edit import CodeEdit
from foundry.smb3parse.util.rom import Rom


class CodeEditDict(CodeEdit[Any]):
    """Represents a code edit that is specified by a dictionary.

    The user passes in a dictionary of abstract labels (Any) in the keys and
    the corresponding bytearray to be written to memory in the value of the
    dictionary.  The user can then request a read/write using the abstract
    key name.
    """

    _options: dict

    def __init__(self, rom: Rom, start_address: int, length: int, prefix: bytearray, options: dict, postfix: bytearray):
        """Initialize the CodeEdit area and sets the valid dictionary values

        options: dict
            * Needs to be of types: [Any, bytearray]
            * all of the values(bytearray) should be the same length
            * values(bytearray) are what will be written to memory or used
                to find the current setting
            * values(bytearray) need to be same length as length parameter
            * Duplicates in values will return first found entry on read
        """
        super().__init__(rom, start_address, length, prefix, postfix)
        self._options = options

    def is_valid(self):
        """Check to see if the current ROM code area is valid.

        This calls the super() valid so the prefix and postfix are checked to
        see if they are valid.  Additionally this will check to see if the
        value at the code edit location is in the provided dictionary.
        """
        if not super().is_valid():
            return False
        return self.read() is not None

    def read(self) -> Any | None:
        """Returns the abstract representation of target code area.

        This will read the current value in the ROM at the target address
        location and covert it to the corresponding abstract representation
        provided by the user during initialization.  If a matching abstract
        value isn't found, None is returned.
        """
        rom_value = self.rom.read(self.address, self.length)
        for key, value in self._options.items():
            if rom_value == value:
                return key
        return None

    def write(self, option: Any):
        """Requests a code edit by an abstract representation/name.

        This will take the specified data, look it up in the provided
        dictionary and write the corresponding bytearray into the ROM at the
        target address location.  If there is no matching abstract value in
        the dictionary, the write is rejected.
        """
        try:
            value = self._options[option]
            if len(value) is self.length:
                self.rom.write(self.address, value)
        except KeyError:
            pass

    def is_option(self, option: Any) -> bool:
        return option in self._options.keys()
