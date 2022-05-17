from foundry.core.Enum import Enum


class FileType(str, Enum):
    """
    The type of file to be applied.
    """

    FROM_FILE = "FROM FILE"
    FROM_NAMESPACE = "FROM NAMESPACE"
