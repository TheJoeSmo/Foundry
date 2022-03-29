<<<<<<< HEAD
""" Test of the ReduxStore """
=======
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
import unittest

from foundry.core.redux_store import ReduxStore, Action, StateNoneError

class _TestReduxStore(ReduxStore[int]):
<<<<<<< HEAD
    """ Create a concrete implementation for testing. """
    def _reduce(self, state:int, action: Action) -> int:
        """ Implement abstract function. """
        return state + 1

class TestStringMethods(unittest.TestCase):
    """ Define a test class, required for self.assertRaises """
    def test_none_state(self):
        """ verify that a StateNoneError is thrown on a None state initialization """
=======
    def _reduce(self, state:int, action: Action) -> int:
        return state + 1

class TestStringMethods(unittest.TestCase):
    def test_none_state(self):
>>>>>>> 4de0dfbe5e948636f50ce1cc3dffb39f29eb4fac
        with self.assertRaises(StateNoneError):
            _TestReduxStore(None)
