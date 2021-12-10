from hypothesis import given

from foundry.core.warnings.InvalidObjectWarning import InvalidObjectWarning
from tests.core.warnings.conftest import object_like


def test_initalization():
    InvalidObjectWarning()


@given(object_like())
def test_check_object(object_like):
    assert InvalidObjectWarning().check_object(object_like)


@given(object_like())
def test_get_message(object_like):
    assert isinstance(InvalidObjectWarning().get_message(object_like), str)
