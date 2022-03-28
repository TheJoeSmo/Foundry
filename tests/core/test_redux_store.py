import unittest

from foundry.core.redux_store import ReduxStore, Action, StateNoneError

class _TestReduxStore(ReduxStore[int]):
    def _reduce(self, state:int, action: Action) -> int:
        return state + 1

class TestStringMethods(unittest.TestCase):
    def test_none_state(self):
        with self.assertRaises(StateNoneError):
            _TestReduxStore(None)
