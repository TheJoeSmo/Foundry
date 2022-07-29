"""
Module defines an abstract class that represents a code edit in ROM.

This CodeEdit will self verify that that the target memory location is correct
by checking the surrounding code to make sure it matches.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from foundry.smb3parse.util.rom import Rom

D = TypeVar("D")


@dataclass
class CodeEdit(ABC, Generic[D]):
    """
    Represents an area to edit to the ROM code.

    Attributes
    ----------
    rom: Rom
        The ROM to edit.
    address: int
        The address of the edit.
    length: int
        The length of the edit.
    prefix: int
        The ROM data just before the edit.  This is used for checking the validity of the
        target location.  This is useful for when a code edit has been made that has shifted
        the code and the target address is no longer valid.  This will help protect invalid
        writes in that case.
    postfix: int
        The ROM data just after the edit.  This is used for checking the validity of the target
        location.  This is useful for when a code edit has been made that has shifted the code and
        the target address is no longer valid.  This will help protect invalid writes in that case.

    Notes
    -----
    This class handles reading and writing the data of a specific code area for
    possible code edits.  It will also check the ROM to see if the target
    modification area has shifted due to other code modifications.

    This is an abstract class.  Implementing classes will need to define the
    read and write routines based on the type of code edit that needs to be
    done.  The read/write routines use the Generic data type 'D' for their
    operations.

    Generic type 'D' is the abstract representation of the edit value and not
    the literal data values (though they could be the same in some cases).
    See read/write for more details.

    A potential improvement in the future would be to check if the target
    address is valid during initialization and if it isn't, search the adjacent
    code areas (maybe 500 bytes or user specified) and try to find a matching
    prefix/postfix with the correct offsets.  This would let this adapt to
    ROMs with code shifting modifications rather than rejecting them.

    The above paragraph is particularly true for expanded ROMs where bank 30/31
    will always be shifted so edits in those banks will fail more often than
    others.  Another possible enhancement might be to read the ROM header as
    well to detect if the ROM is expanded to see if edits in banks 30/31 need
    to be shifted (instead of searched) as this would provide more accurate and
    quicker results.  A search could be done secondary after the shift if the
    target code areas isn't found in the shifted target location.
    """

    rom: Rom
    address: int
    length: int
    prefix: bytearray
    postfix: bytearray

    def _valid_affix(self, test_address: int, data: bytearray) -> bool:
        """
        Verifies that the specified affix matches the ROM.
        """
        if len(data) == 0:
            return True
        return data == self.rom.read(test_address, len(data))

    def is_valid(self) -> bool:
        """
        Verifies that both the prefix and postfix are valid.

        Notes
        -----
        This function can also be overwritten if only certain values are valid
        so that the value of the target area is also checked if that is
        important.
        """
        if not self._valid_affix(self.address - len(self.prefix), self.prefix):
            return False
        return self._valid_affix(self.address + self.length, self.postfix)

    @abstractmethod
    def read(self) -> D | None:
        """
        Read the abstract representation of the target edit area.

        Notes
        -----
        The Generic return type 'D' here is the abstract representation of the
        code edit, not the actual data of the edit, though in some situations
        these might be identical.  For example, if we are checking if the
        players lives decrease when they die, the return value might be a
        string "infinite lives" or "vanilla" or True/False while the actual
        code edit might be the presence of an DEC NUM_LIVES instruction or a
        NOP section removing that code.

        This is an Optional[D] because if the code area is invalid, no value
        might be returned.
        """

    @abstractmethod
    def write(self, option: D):
        """
        Read the abstract representation of the target edit area.

        Notes
        -----
        The Generic option type 'D' here is the abstract representation of the
        code edit, not the actual data of the edit, though in some situations
        these might be identical (see the read instruction documentation for
        an example).

        The implementation of this function is responsible for taking the
        abstract input and generating the corresponding code edit.
        """
