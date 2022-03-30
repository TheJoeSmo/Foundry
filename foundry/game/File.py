from os.path import basename
from typing import ClassVar, List, Optional, Type, TypeVar

from attr import attrs

from foundry.smb3parse.constants import BASE_OFFSET, PAGE_A000_ByTileset
from foundry.smb3parse.util.rom import Rom

WORLD_COUNT = 9  # includes warp zone

# W = WORLD_MAP
# OS = OFFSET

OS_SIZE = 2  # byte

TSA_OS_LIST = PAGE_A000_ByTileset
TSA_TABLE_SIZE = 0x400
TSA_TABLE_INTERVAL = TSA_TABLE_SIZE + 0x1C00


Self = TypeVar("Self")


class InvalidINESHeader(TypeError):
    """
    An exception that is raised if a file does not follow an INES header when it is meant to.
    """

    def __init__(self, file_path: Optional[str] = None):
        if file_path:
            super().__init__(f"{file_path} does not follow the INES header format")
        super().__init__("Invalid INES header")


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True)
class INESHeader:
    """
    The representation of the header inside the ROM, following the INES format.
    Regarding the specifics of the INES format, more information can be found at
    `https://www.nesdev.org/wiki/INES`_.

    Attributes
    ----------
    INESHEADER_PREFIX: ClassVar[bytes]
        The required prefix for any INES header.
    BASE_PROGRAM_SIZE: ClassVar[int]
        The base program size for a standard copy of SMB3.
    PROGRAM_BANK_SIZE: ClassVar[int]
        The size of any program bank.
    CHARACTER_BANK_SIZE: ClassVar[int]
        The size of any character bank.
    INES_HEADER_SIZE
        The size of the INES header.
    program_banks: int
        The amount of 8kb banks of program data inside the file.
    character_banks: int
        The amount of 4kb banks of graphical data inside the file.
    mapper: int
        The memory mapper used by the file.
    horizontal_mirroring: bool
        If the file uses horizontal mirroring, otherwise it is assumed it uses vertical mirroring.
        See `https://www.nesdev.org/wiki/Mirroring#Nametable_Mirroring`_ for more information.
    battery_backed_ram: bool
        If the file contains battery-backed RAM between 0x6000 and 0x7FFF or any other form of persistent memory.
    """

    INESHEADER_PREFIX: ClassVar[bytes] = bytes([0x4E, 0x45, 0x53, 0x1A])
    BASE_PROGRAM_SIZE: ClassVar[int] = 0x40000
    PROGRAM_BANK_SIZE: ClassVar[int] = 0x4000
    CHARACTER_BANK_SIZE: ClassVar[int] = 0x2000
    INES_HEADER_SIZE: ClassVar[int] = 0x10

    program_banks: int
    character_banks: int
    mapper: int
    horizontal_mirroring: bool
    battery_backed_ram: bool

    @property
    def vertical_mirroring(self) -> bool:
        """
        Determines if the file uses vertical mirroring.
        See `https://www.nesdev.org/wiki/Mirroring#Nametable_Mirroring`_ for more information.

        Returns
        -------
        bool
            If the file uses vertical mirroring.
        """
        return not self.horizontal_mirroring

    @property
    def program_size(self) -> int:
        """
        The amount of space dedicated to program data.

        Returns
        -------
        int
            The amount of bytes provided for program banks.
        """
        return self.PROGRAM_BANK_SIZE * self.program_banks

    @property
    def character_size(self) -> int:
        """
        The amount of space dedicated to character data.

        Returns
        -------
        int
            The amount of bytes provided for character data.
        """
        return self.CHARACTER_BANK_SIZE * self.character_banks

    @classmethod
    def from_data(cls: Type[Self], data: bytes, path: Optional[str] = None) -> Self:
        """
        Generates an INES header from a file following the header.

        Parameters
        ----------
        data : bytes
            The data to generate the header from.
        path : Optional[str], optional
            The path used for better exception information, by default None

        Returns
        -------
        INESHeader
            The newly generated header.

        Raises
        ------
        InvalidINESHeader
            If the data does not follow an INES header.
        """
        if INESHeader.INESHEADER_PREFIX != data[:4] or len(data) < 0x10:
            raise InvalidINESHeader(path)

        return cls(data[4], data[5], (data[6] & 0xF0) >> 4, bool(data[6] & 0b01), bool(data[6] & 0b10))

    @staticmethod
    def program_address(address: int) -> int:
        """
        Provides the address shifted to make the start of the program data start at the first index.

        Parameters
        ----------
        address : int
            To shift to account for the size of the header.

        Returns
        -------
        int
            The absolute program address.
        """
        return address - INESHeader.INES_HEADER_SIZE

    @staticmethod
    def address_is_global(address: int, program_banks: int) -> bool:
        """
        Determines if the address is inside the last two, global, banks of SMB3.

        Parameters
        ----------
        address : int
            The address to check.
        program_banks : int
            The amount of program banks.

        Returns
        -------
        bool
            If the address is global.
        """
        return INESHeader.program_address(address) >= (program_banks - 1) * INESHeader.PROGRAM_BANK_SIZE

    @staticmethod
    def relative_address(address: int) -> int:
        """
        Provides the relative address that would be references inside the ROM.

        Parameters
        ----------
        address : int
            The absolute address.

        Returns
        -------
        int
            The relative address.
        """
        return INESHeader.program_address(address) & (INESHeader.PROGRAM_BANK_SIZE - 1)

    def normalized_address(self, address: int, program_size: int = BASE_PROGRAM_SIZE) -> int:
        """
        Finds an address that would better account for ROM expansions.

        Parameters
        ----------
        address : int
            The address to normalize.
        program_size : int, optional
            The program size of the original ROM, by default BASE_PROGRAM_SIZE

        Returns
        -------
        int
            The normalized address.
        """
        if self.program_size == program_size:
            return address
        return (
            self.program_size
            + self.relative_address(address)
            - INESHeader.PROGRAM_BANK_SIZE
            + INESHeader.INES_HEADER_SIZE
            if self.address_is_global(address, program_size)
            else self.program_address(address) + INESHeader.INES_HEADER_SIZE
        )


class ROM(Rom):
    MARKER_VALUE = bytes("SMB3FOUNDRY", "ascii")

    rom_data = bytearray()

    additional_data = ""

    path: str = ""
    name: str = ""
    header: INESHeader

    W_INIT_OS_LIST: List[int] = []

    def __init__(self, path: Optional[str] = None):
        if not ROM.rom_data:
            if path is None:
                raise ValueError("Rom was not loaded!")

            ROM.load_from_file(path)

        super(ROM, self).__init__(ROM.rom_data)

        self.position = 0

    @staticmethod
    def get_tsa_data(object_set: int) -> bytearray:
        rom = ROM()

        tsa_index = rom.int(TSA_OS_LIST + object_set)

        if object_set == 0:
            # todo why is the tsa index in the wrong (seemingly) false?
            tsa_index += 1

        tsa_start = BASE_OFFSET + tsa_index * TSA_TABLE_INTERVAL

        return rom.read(tsa_start, TSA_TABLE_SIZE)

    @staticmethod
    def write_tsa_data(object_set: int, tsa_data: bytearray):
        rom = ROM()

        tsa_index = rom.int(TSA_OS_LIST + object_set)

        if object_set == 0:
            # todo why is the tsa index in the wrong (seemingly) false?
            tsa_index += 1

        tsa_start = BASE_OFFSET + tsa_index * TSA_TABLE_INTERVAL

        rom.bulk_write(tsa_data, tsa_start)

    @staticmethod
    def load_from_file(path: str):
        with open(path, "rb") as rom:
            data = bytearray(rom.read())

        ROM.path = path
        ROM.name = basename(path)

        additional_data_start = data.find(ROM.MARKER_VALUE)

        if additional_data_start == -1:
            ROM.rom_data = data
            ROM.additional_data = ""
        else:
            ROM.rom_data = data[:additional_data_start]

            additional_data_start += len(ROM.MARKER_VALUE)

            ROM.additional_data = data[additional_data_start:].decode("utf-8")
        ROM.header = INESHeader.from_data(ROM.rom_data)

    @staticmethod
    def save_to_file(path: str, set_new_path=True):
        with open(path, "wb") as f:
            f.write(bytearray(ROM.rom_data))

        if ROM.additional_data:
            with open(path, "ab") as f:
                f.write(ROM.MARKER_VALUE)
                f.write(ROM.additional_data.encode("utf-8"))

        if set_new_path:
            ROM.path = path
            ROM.name = basename(path)

    @staticmethod
    def set_additional_data(additional_data):
        ROM.additional_data = additional_data

    @staticmethod
    def is_loaded() -> bool:
        return bool(ROM.path)

    def seek(self, position: int) -> int:
        if position > len(ROM.rom_data) or position < 0:
            return -1

        self.position = position

        return 0

    def get_byte(self, position: int = -1) -> int:
        if position >= 0:
            k = self.seek(position) >= 0
        else:
            k = self.position < len(ROM.rom_data)

        if k:
            return_byte = ROM.rom_data[self.position]
        else:
            return_byte = 0

        self.position += 1

        return return_byte

    def peek_byte(self, position: int = -1) -> int:
        old_position = self.position

        byte = self.get_byte(position)

        self.position = old_position

        return byte

    def bulk_read(self, count: int, position: int = -1) -> bytearray:
        if position >= 0:
            self.seek(position)
        else:
            position = self.position

        self.position += count

        return ROM.rom_data[position : position + count]

    def bulk_write(self, data: bytearray, position: int = -1):
        if position >= 0:
            self.seek(position)
        else:
            position = self.position

        self.position += len(data)

        ROM.rom_data[position : position + len(data)] = data
