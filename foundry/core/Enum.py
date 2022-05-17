from enum import Enum as _Enum


class Enum(_Enum):
    @classmethod
    def has_value(cls, value) -> bool:
        """
        A convenience method to quickly determine if a value is a valid enumeration.

        Parameters
        ----------
        value : str
            The value to check against the enumeration.

        Returns
        -------
        bool
            If the value is inside the enumeration.
        """

        return value in cls._value2member_map_
