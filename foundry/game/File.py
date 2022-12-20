from collections.abc import Iterator, Sequence
from os.path import basename
from pathlib import Path
from random import getrandbits
from typing import ClassVar, Self, overload

from attr import attrs

from foundry.core import EndianType, FindableEndianMutableSequence
from foundry.gui.settings import FileSettings, load_file_settings, save_file_settings
from foundry.smb3parse.constants import BASE_OFFSET, PAGE_A000_ByTileset

WORLD_MAP_TSA_INDEX = 12
TSA_OS_LIST = PAGE_A000_ByTileset
TSA_TABLE_SIZE = 0x400
TSA_TABLE_INTERVAL = TSA_TABLE_SIZE + 0x1C00
MARKER_VALUE: bytes = bytes("SMB3FOUNDRY", "ascii")
NINTENDO_MARKER_VALUE: bytes = bytes("SUPER MARIO 3", "ascii")


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
    INES_HEADER_PREFIX: ClassVar[bytes]
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

    INES_HEADER_PREFIX: ClassVar[bytes] = bytes([0x4E, 0x45, 0x53, 0x1A])
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
    def from_data(cls, data: bytes, path: str | None = None) -> Self:
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
        if INESHeader.INES_HEADER_PREFIX != data[:4] or len(data) < 0x10:
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


def generate_identity(data: bytearray) -> int | None:
    """
    Generates a identification tag for a file.  This enables the file to be references later on.

    This tag will include the ROM_MARKER value and eight random bytes that serve as the ID of the file.

    Returns
    -------
    int | None
        The ID of the file, if the tag was successfully generated and applied.
    """
    nintendo_offset: int = data.find(NINTENDO_MARKER_VALUE)
    if nintendo_offset == -1:
        return None

    # 8 random bytes to be used as the id.
    identity: int = getrandbits(64)
    data[nintendo_offset : nintendo_offset + len(MARKER_VALUE)] = identity.to_bytes(8, "little")
    return identity


def determine_identity(data: bytearray) -> int | None:
    """
    Determines the ID of a bytearray which represents the file.

    Returns
    -------
    int | None
        The ID of the file, if one can exist.
    """
    identity: int = data.find(MARKER_VALUE)

    return (
        generate_identity(data)
        if identity == -1
        else int.from_bytes(
            data[identity + len(MARKER_VALUE) : identity + len(MARKER_VALUE) + 8],
            "little",
        )
    )


class ROM(FindableEndianMutableSequence[int]):
    W_INIT_OS_LIST: list[int] = []

    def __init__(
        self, identity: int | None, path: Path, data: bytearray, name: str, header: INESHeader, settings: FileSettings
    ) -> None:
        self._id: int | None = identity
        self.path: Path = path
        self.rom_data: bytearray = data
        self.name: str = name
        self.header: INESHeader = header
        self.settings = settings

    @staticmethod
    def set_default(rom) -> None:
        global _ROM
        _ROM = rom

    @classmethod
    def as_default(cls) -> Self:
        if _ROM is None:
            raise ValueError("No ROM is set as default")
        return _ROM

    def copy(self) -> Self:
        return ROM(self._id, self.path, self.rom_data.copy(), self.name, self.header, self.settings)

    @classmethod
    def from_file(cls, path: Path, default: bool = True, set_identity: bool = True) -> Self:
        with open(path, "rb") as f:
            data: bytearray = bytearray(f.read())

        identity: int | None = determine_identity(data) if set_identity else None
        file: ROM = ROM(
            identity,
            path,
            data,
            basename(path),
            INESHeader.from_data(data),
            load_file_settings(str(identity)),
        )

        if default:
            ROM.set_default(file)

        return file

    @overload
    def __getitem__(self, index: int | tuple[int, bool]) -> int:
        pass

    @overload
    def __getitem__(self, index: slice | tuple[slice, bool]) -> bytearray:
        pass

    def __getitem__(self, index: int | tuple[int, bool] | slice | tuple[slice, bool]) -> int | bytearray:
        if isinstance(index, tuple):
            if len(index) != 2:
                raise NotImplementedError
            index_, graphics = index

            if graphics and isinstance(index_, int):
                return self.rom_data[self.header.normalized_address(index_)]
            elif graphics and isinstance(index_, slice):
                return self.rom_data[
                    slice(
                        self.header.normalized_address(index_.start),
                        self.header.normalized_address(index_.stop),
                        index_.step,
                    )
                ]
            elif not graphics:
                return self.rom_data[index_]
            else:
                raise NotImplementedError
        elif isinstance(index, int):
            if index > len(self.rom_data):
                raise IndexError(f"0x{index:08X} exceeds 0x{len(self.rom_data):08X}")
            return self.rom_data[index]
        elif isinstance(index, slice):
            if index.stop is not None and index.stop > len(self.rom_data):
                raise IndexError(f"0x{index.stop:08X} exceeds 0x{len(self.rom_data):08X}")
            return self.rom_data[index]
        else:
            raise NotImplementedError

    def __setitem__(self, key: int | slice, value: int | bytes | bytearray | Sequence[int]) -> None:
        if isinstance(key, int):
            if isinstance(value, int):
                self.rom_data[key] = value
            else:
                self.rom_data[key : key + len(value)] = value
        elif isinstance(key, slice):
            if isinstance(value, int):
                self.rom_data[key] = self.from_endian(value, size=key.stop - key.start)
            else:
                for value_index, key_index in enumerate(range(key.start, key.stop, key.step or 1)):
                    self.rom_data[key_index] = value[value_index]
        else:
            raise NotImplementedError

    def __delitem__(self, key: int | slice) -> None:
        self[key] = 0x00

    def __iter__(self) -> Iterator[int]:
        return iter(self.rom_data)

    def __len__(self) -> int:
        return len(self.rom_data)

    def insert(self, index: int, value: int) -> None:
        if self[index] != 0x00:
            raise IndexError
        self[index] = value

    def endian(self, index: int, endian: EndianType = EndianType.LITTLE, size: int = 2, *args) -> int:
        """
        Provides an integer representation of data inside the file.

        Parameters
        ----------
        index : int
            The location to load the data
        endian : EndianType, optional
            The endian type, by default EndianType.LITTLE
        size : int, optional
            The count of bytes that the integer represents, by default 2

        Returns
        -------
        int
            The integer representation of data inside the file.

        Raises
        ------
        NotImplementedError
            If an invalid EndianType is provided.
        """
        if endian == EndianType.LITTLE:
            return int.from_bytes(self.rom_data[index : index + size], "little")
        elif endian == EndianType.BIG:
            return int.from_bytes(self.rom_data[index : index + size], "big")
        raise NotImplementedError

    @staticmethod
    def get_tsa_data(tileset: int) -> bytearray:
        rom = ROM.as_default()

        if tileset == 0:
            tsa_index = WORLD_MAP_TSA_INDEX
        else:
            tsa_index = rom[TSA_OS_LIST + tileset]

        tsa_start = BASE_OFFSET + tsa_index * TSA_TABLE_INTERVAL
        tsa_offset: int = rom.header.normalized_address(tsa_start)
        tsa_data = rom[tsa_offset : tsa_offset + TSA_TABLE_SIZE]

        assert len(tsa_data) == TSA_TABLE_SIZE
        return tsa_data

    @staticmethod
    def write_tsa_data(tileset: int, tsa_data: bytearray):
        rom = ROM.as_default()

        tsa_index = rom[TSA_OS_LIST + tileset]

        if tileset == 0:
            # todo why is the tsa index in the wrong (seemingly) false?
            tsa_index += 1

        tsa_start = BASE_OFFSET + tsa_index * TSA_TABLE_INTERVAL

        rom[tsa_start] = tsa_data

    @property
    def identifier(self) -> str:
        """
        Provides an identifier for the file.

        Returns
        -------
        str
            The identifier associated with this file.
        """
        return str(self._id) if self._id is not None else str(self.path)

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
    def save_to_file(path: Path, set_new_path=True):
        if _ROM is None:
            raise ValueError("ROM is not loaded")

        with open(path, "wb") as f:
            f.write(bytearray(_ROM.rom_data))

        save_file_settings(str(_ROM._id), _ROM._settings)

        if set_new_path:
            _ROM.path = path
            _ROM.name = basename(path)

    @staticmethod
    def is_loaded() -> bool:
        return _ROM is not None

    def bulk_write(self, data: bytearray, position: int):
        position = self.header.normalized_address(position)
        self.rom_data[position : position + len(data)] = data

    def write(self, offset: int, data: bytes):
        self.rom_data[offset : offset + len(data)] = data

    def find(self, byte: bytes, offset: int = 0) -> int:
        return self.rom_data.find(byte, offset)

    def save_to(self, path: str):
        with open(path, "wb") as file:
            file.write(self.rom_data)


_ROM: ROM | None = None
