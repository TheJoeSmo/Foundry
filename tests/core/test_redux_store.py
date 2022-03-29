""" Test of the ReduxStore """
import unittest

from foundry.core.redux_store import Action, ReduxStore, StateNoneError


class _TestReduxStore(ReduxStore[int]):
    """Create a concrete implementation for testing."""

    def _reduce(self, state: int, action: Action) -> int:
        """Implement abstract function."""
        return state + 1


class TestStringMethods(unittest.TestCase):
    """Define a test class, required for self.assertRaises"""

    def test_none_state(self):
        """verify that a StateNoneError is thrown on a None state initialization"""
        with self.assertRaises(StateNoneError):
            _TestReduxStore(None)
