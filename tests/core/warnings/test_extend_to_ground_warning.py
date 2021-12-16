from hypothesis import given

from foundry.core.warnings.ExtendToGroundWarning import ExtendToGroundWarning
from tests.core.warnings import ObjectLike
from tests.core.warnings.conftest import object_like


def test_initalization():
    ExtendToGroundWarning()


def test_find_warning():
    object_like = ObjectLike(y=2, rendered_height=25)
    assert ExtendToGroundWarning().check_object(object_like)  # type: ignore


def test_not_find_warning():
    object_like = ObjectLike(y=2, rendered_height=24)
    assert not ExtendToGroundWarning().check_object(object_like)  # type: ignore


@given(object_like())
def test_check_object_no_level(object_like):
    assert isinstance(ExtendToGroundWarning().check_object(object_like), bool)


@given(object_like())
def test_get_message(object_like):
    assert isinstance(ExtendToGroundWarning().get_message(object_like), str)
