class Rom:
    def __init__(self, rom_data: bytearray):
        self._data = rom_data

    def read(self, offset: int, length: int) -> bytearray:
        return self._data[offset : offset + length]

    def write(self, offset: int, data: bytes):
        self._data[offset : offset + len(data)] = data

    def find(self, byte: bytes, offset: int = 0) -> int:
        return self._data.find(byte, offset)

    def int(self, offset: int) -> int:
        read_bytes = self.read(offset, 1)

        return read_bytes[0]

    def save_to(self, path: str):
        with open(path, "wb") as file:
            file.write(self._data)
