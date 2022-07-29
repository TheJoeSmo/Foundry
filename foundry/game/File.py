from os.path import basename
from random import getrandbits
from typing import ClassVar, TypeVar

from attr import attrs

from foundry.gui.settings import FileSettings, load_file_settings, save_file_settings
from foundry.smb3parse.constants import BASE_OFFSET, PAGE_A000_ByTileset
from foundry.smb3parse.util.rom import Rom

WORLD_COUNT = 9  # includes warp zone

# W = WORLD_MAP
# OS = OFFSET

OS_SIZE = 2  # byte

WORLD_MAP_TSA_INDEX = 12
TSA_OS_LIST = PAGE_A000_ByTileset
TSA_TABLE_SIZE = 0x400
TSA_TABLE_INTERVAL = TSA_TABLE_SIZE + 0x1C00


Self = TypeVar("Self")


class InvalidINESHeader(TypeError):
    """
    An exception that is raised if a file does not follow an INES header when it is meant to.
    """

    def __init__(self, file_path: str | None = None):
        if file_path:
            super().__init__(f"{file_path} does not follow the INES header format")
        super().__init__("Invalid INES header")


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True)
class INESHeader:
    """
    The representation of the header inside the ROM, following the INES format.
    Regarding the specifics of the INES format, more information can be found at
    `INES <https://www.nesdev.org/wiki/INES>`_.

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
        See `Nametable_Mirroring <https://www.nesdev.org/wiki/Mirroring#Nametable_Mirroring>`_
        for more information.
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
        See `Nametable_Mirroring <https://www.nesdev.org/wiki/Mirroring#Nametable_Mirroring>`_
        for more information.

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
    def from_data(cls: type[Self], data: bytes, path: str | None = None) -> Self:
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
            if self.address_is_global(address, program_size // INESHeader.PROGRAM_BANK_SIZE)
            else self.program_address(address) + INESHeader.INES_HEADER_SIZE
        )


class ROM(Rom):
    NINTENDO_MARKER_VALUE: ClassVar[bytes] = bytes("SUPER MARIO 3", "ascii")
    MARKER_VALUE: ClassVar[bytes] = bytes("SMB3FOUNDRY", "ascii")

    rom_data = bytearray()

    path: str = ""
    name: str = ""
    header: INESHeader
    _settings: FileSettings
    _id: int | None

    W_INIT_OS_LIST: list[int] = []

    def __init__(self, path: str | None = None):
        if not ROM.rom_data:
            if path is None:
                raise ValueError("Rom was not loaded!")

            ROM.load_from_file(path)

        super().__init__(ROM.rom_data)

        self.position = 0

    @staticmethod
    def get_tsa_data(object_set: int) -> bytearray:
        rom = ROM()

        if object_set == 0:
            tsa_index = WORLD_MAP_TSA_INDEX
        else:
            tsa_index = rom.get_byte(TSA_OS_LIST + object_set)

        tsa_start = BASE_OFFSET + tsa_index * TSA_TABLE_INTERVAL
        tsa_data = rom.bulk_read(TSA_TABLE_SIZE, rom.header.normalized_address(tsa_start))

        assert len(tsa_data) == TSA_TABLE_SIZE
        return tsa_data

    @staticmethod
    def write_tsa_data(object_set: int, tsa_data: bytearray):
        rom = ROM()

        tsa_index = rom.int(TSA_OS_LIST + object_set)

        if object_set == 0:
            # todo why is the tsa index in the wrong (seemingly) false?
            tsa_index += 1

        tsa_start = BASE_OFFSET + tsa_index * TSA_TABLE_INTERVAL

        rom.bulk_write(tsa_data, tsa_start)

    def generate_tag(self) -> int | None:
        """
        Generates a identification tag for a file.  This enables the file to be references later on.

        This tag will include the ROM_MARKER value and eight random bytes that serve as the ID of the file.

        Returns
        -------
        Optional[int]
            The ID of the file, if the tag was successfully generated and applied.
        """
        with open(self.path, "rb") as rom:
            data = bytearray(rom.read())

        nintendo_id_offset = data.find(self.NINTENDO_MARKER_VALUE)

        if nintendo_id_offset == -1:
            return None

        # 8 random bytes to be used as the id.
        rom_id = getrandbits(64)

        self.write(nintendo_id_offset, self.MARKER_VALUE + rom_id.to_bytes(8, "big"))

        return rom_id

    def get_id(self) -> int | None:
        """
        Determines the ID of the file.

        Returns
        -------
        Optional[int]
            The ID of the file, if one can exist.
        """
        with open(self.path, "rb") as rom:
            data = bytearray(rom.read())

        rom_id_start = data.find(self.MARKER_VALUE)

        return (
            self.generate_tag()
            if rom_id_start == -1
            else int.from_bytes(
                data[rom_id_start + len(self.MARKER_VALUE) : rom_id_start + len(self.MARKER_VALUE) + 8],
                "big",
            )
        )

    @property
    def identifier(self) -> str:
        """
        Provides an identifier for the file.

        Returns
        -------
        str
            The identifier associated with this file.
        """
        return str(self._id) if self._id is not None else self.path

    @property
    def settings(self) -> FileSettings:
        """
        Provides the settings for the file.

        Returns
        -------
        FileSettings
            The settings associated with this file.
        """
        return self._settings

    @settings.setter
    def settings(self, settings: FileSettings):
        self._settings = settings

    @staticmethod
    def load_from_file(path: str):
        with open(path, "rb") as rom:
            data = bytearray(rom.read())

        ROM.rom_data = data
        ROM.path = path
        ROM.name = basename(path)
        ROM._id = ROM().get_id()
        ROM._settings = load_file_settings(str(ROM._id))
        ROM.header = INESHeader.from_data(ROM.rom_data)

    @staticmethod
    def save_to_file(path: str, set_new_path=True):
        with open(path, "wb") as f:
            f.write(bytearray(ROM.rom_data))

        save_file_settings(str(ROM._id), ROM._settings)

        if set_new_path:
            ROM.path = path
            ROM.name = basename(path)

    @staticmethod
    def set_additional_data(additional_data):
        ROM.additional_data = additional_data

    @staticmethod
    def is_loaded() -> bool:
        return bool(ROM.path)

    def get_byte(self, position: int) -> int:
        position = self.header.normalized_address(position)

        if position > len(self.rom_data):
            raise IndexError(f"Cannot read index at 0x{position:X} from a file of size 0x{len(self.rom_data):X}")

        return self.rom_data[position]

    def bulk_read(self, count: int, position: int, *, is_graphics: bool = False) -> bytearray:
        if not is_graphics:
            position = self.header.normalized_address(position)

        if position + count > len(self.rom_data):
            raise IndexError(
                f"Cannot read index at 0x{position + count:X} from a file of size 0x{len(self.rom_data):X}"
            )

        return ROM.rom_data[position : position + count]

    def bulk_write(self, data: bytearray, position: int):
        position = self.header.normalized_address(position)
        self.rom_data[position : position + len(data)] = data
