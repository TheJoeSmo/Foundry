from collections.abc import Callable
from typing import Any


def range_validator(minimum: int | None = None, maximum: int | None = None) -> Callable[[Any, Any, int], int]:
    """
    A validator for an ~`attrs.attrs` dataclass that ensures an int is between a minimum and maximum value.

    Parameters
    ----------
    minimum : Optional[int]
        The minimum value that the value is permitted to be.  If minimum is None, then there will be no bound for the
        minimum value.  By default, None.
    maximum : Optional[int]
        The maximum value that the value is permitted to be.  If maximum is None, then there will be no bound for the
        maximum value.  By default, None.

    Returns
    -------
    Callable[[Any, Any, int], int]
        A callable that acts as the true validator with a predefined minimum and maximum value.
    """

    def range_validator(instance: Any, attribute: Any, value: int) -> int:
        """
        Validates a value is between a predefined minimum and maximum value.

        Parameters
        ----------
        instance : Any
            The instance that's being validated.
        attribute : Any
            The attribute that it's validating.
        value : int
            The value that is passed for it.

        Returns
        -------
        int
            The value that is passed for it.

        Raises
        ------
        ValueError
            Raised when the value is less than the minimum value.
        ValueError
            Raised when the value is greater than the maximum value.
        """
        if minimum is not None and value < minimum:
            raise ValueError(f"{value} is less than the minimum possible input {minimum}")
        if maximum is not None and value > maximum:
            raise ValueError(f"{value} is greater than the maximum possible input {maximum}")
        return value

    return range_validator
