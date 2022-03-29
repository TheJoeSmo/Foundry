<<<<<<< HEAD
""" Concrete implementation of the CodeEdit class using a dictionary lookup.

This CodeEdit uses a dictionary as the edit values.  The keys represent the
abstract option and the values are the byte data needing to be programmed
into memory.
"""
=======
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
from typing import Any, Optional
from foundry.smb3parse.util.rom import Rom
from foundry.smb3parse.util.code_edit import CodeEdit

class CodeEditDict(CodeEdit[Any]):
<<<<<<< HEAD
    """ Represents a code edit that is specified by a dictionary.

    The user passes in a dictionary of abstract labels (Any) in the keys and
    the corresponding bytearray to be written to memory in the value of the
=======
    """ Represents a code edit that is specified by a dictionary. 
    
    The user passes in a dictionary of abstract labels (Any) in the keys and 
    the corresponding bytearray to be written to memory in the value of the 
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
    dictionary.  The user can then request a read/write using the abstract
    key name.
    """
    _options: dict

<<<<<<< HEAD
    def __init__(self, rom: Rom, start_address: int, length: int,
                 prefix: bytearray, options: dict, postfix: bytearray):
        """ Initialize the CodeEdit area and sets the valid dictionary values

        options: dict
            * Needs to be of types: [Any, bytearray]
            * all of the values(bytearray) should be the same length
            * values(bytearray) are what will be written to memory or used
=======
    def __init__(self, rom: Rom, start_address: int, length: int, prefix: bytearray, options: dict, postfix: bytearray):
        """ Initialize the CodeEdit area and sets the valid dictionary values

        options: dict 
            * Needs to be of types: [Any, bytearray]
            * all of the values(bytearray) should be the same length
            * values(bytearray) are what will be written to memory or used 
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
                to find the current setting
            * values(bytearray) need to be same length as length parameter
            * Duplicates in values will return first found entry on read
        """
        super().__init__(rom, start_address, length, prefix, postfix)
        self._options = options

    def is_valid(self):
<<<<<<< HEAD
        """ Check to see if the current ROM code area is valid.

        This calls the super() valid so the prefix and postfix are checked to
        see if they are valid.  Additionally this will check to see if the
        value at the code edit location is in the provided dictionary.
        """
        if not super().is_valid():
            return False
=======
        """ Check to see if the current ROM code area is valid. 
        
        This calls the super() valid so the prefix and postfix are checked to 
        see if they are valid.  Additionally this will check to see if the
        value at the code edit location is in the provided dictionary.  
        """
        if not super().is_valid(): return False
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
        return self.read() is not None

    def read(self) -> Optional[Any]:
        """ Returns the abstract representation of target code area.
<<<<<<< HEAD

        This will read the current value in the ROM at the target address
        location and covert it to the corresponding abstract representation
        provided by the user during initialization.  If a matching abstract
        value isn't found, None is returned.
        """
        rom_value = self.rom.read(self.address, self.length)
=======
        
        This will read the current value in the ROM at the target address
        location and covert it to the corresponding abstract representation
        provided by the user during initialization.  If a matching abstract 
        value isn't found, None is returned.
        """
        rom_value = self.rom.read(self.address, self.length) 
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
        for key, value in self._options.items():
            if rom_value == value:
                return key
        return None

<<<<<<< HEAD
    def write(self, option: Any):
        """ Requests a code edit by an abstract representation/name.

        This will take the specified data, look it up in the provided
        dictionary and write the corresponding bytearray into the ROM at the
        target address location.  If there is no matching abstract value in
        the dictionary, the write is rejected.
        """
        try:
            value = self._options[option]
=======
    def write(self, selection: Any):
        """ Requests a code edit by an abstract representation/name.
        
        This will take the specified selection, look it up in the provided 
        dictionary and write the corresponding bytearray into the ROM at the
        target address location.  If there is no matching abstract value in 
        the dictionary, the write is rejected.
        """
        try:
            value = self._options[selection]
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
            if len(value) is self.length:
                self.rom.write(self.address, value)
        except KeyError:
            pass
