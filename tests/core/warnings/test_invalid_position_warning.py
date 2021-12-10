from hypothesis import given
from hypothesis.strategies import builds, integers

from foundry.core.warnings.InvalidPositionWarning import InvalidPositionWarning
from tests.core.warnings.conftest import object_like


def positional_warning():
    return builds(InvalidPositionWarning, integers(), integers(), integers(), integers())


def test_initalization():
    InvalidPositionWarning()


@given(object_like(), positional_warning())
def test_check_object_no_level(object_like, warning):
    assert isinstance(warning.check_object(object_like), bool)


@given(object_like(), positional_warning())
def test_get_message(object_like, warning):
    if warning.check_object(object_like):
        assert isinstance(warning.get_message(object_like), str)
