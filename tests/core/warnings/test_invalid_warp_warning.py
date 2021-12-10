from hypothesis import given

from foundry.core.warnings.InvalidWarpWarning import InvalidWarpWarning
from tests.core.warnings.conftest import (
    level_does_not_has_next_area,
    level_has_next_area,
    object_like,
)


def test_initalization():
    InvalidWarpWarning()


@given(object_like())
def test_check_object_no_level(object_like):
    assert not InvalidWarpWarning().check_object(object_like)


@given(object_like())
def test_check_object_has_next_area(object_like):
    with level_has_next_area() as level:
        assert not InvalidWarpWarning().check_object(object_like, level=level)


@given(object_like())
def test_check_object_does_not_have_next_area(object_like):
    with level_does_not_has_next_area() as level:
        assert InvalidWarpWarning().check_object(object_like, level=level)


@given(object_like())
def test_get_message(object_like):
    assert isinstance(InvalidWarpWarning().get_message(object_like), str)
