from hypothesis import given

from foundry.core.warnings.Warning import Warning
from tests.core.warnings.conftest import object_like


def test_initalization():
    Warning()


@given(object_like())
def test_check_object(object_like):
    assert Warning().check_object(object_like)


@given(object_like())
def test_get_message(object_like):
    assert isinstance(Warning().get_message(object_like), str)
