from hypothesis import given
from hypothesis.strategies import builds, integers

from foundry.core.warnings.InvalidSizeWarning import InvalidSizeWarning
from tests.core.warnings.conftest import object_like


def size_warning():
    return builds(InvalidSizeWarning, integers(), integers(), integers(), integers())


def test_initalization():
    InvalidSizeWarning()


@given(object_like(), size_warning())
def test_check_object_no_level(object_like, warning):
    assert isinstance(warning.check_object(object_like), bool)


@given(object_like(), size_warning())
def test_get_message(object_like, warning):
    if warning.check_object(object_like):
        assert isinstance(warning.get_message(object_like), str)
