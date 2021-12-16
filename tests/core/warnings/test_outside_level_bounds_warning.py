from hypothesis import given

from foundry.core.warnings.OutsideLevelBoundsWarning import OutsideLevelBoundsWarning
from tests.core.warnings.conftest import (
    level_contains,
    level_does_not_contains,
    object_like,
)


def test_initalization():
    OutsideLevelBoundsWarning()


@given(object_like())
def test_check_object_no_level(object_like):
    assert not OutsideLevelBoundsWarning().check_object(object_like)


@given(object_like())
def test_check_object_inside_rect(object_like):
    with level_contains() as level:
        assert not OutsideLevelBoundsWarning().check_object(object_like, level=level)


@given(object_like())
def test_check_object_not_inside_rect(object_like):
    with level_does_not_contains() as level:
        assert OutsideLevelBoundsWarning().check_object(object_like, level=level)


@given(object_like())
def test_get_message(object_like):
    assert isinstance(OutsideLevelBoundsWarning().get_message(object_like), str)
