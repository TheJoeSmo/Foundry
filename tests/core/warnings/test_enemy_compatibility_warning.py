from hypothesis import given

from foundry.core.warnings.EnemyCompatibilityWarning import EnemyCompatibilityWarning
from tests.core.warnings.conftest import object_like


def test_initalization():
    EnemyCompatibilityWarning()


@given(object_like())
def test_get_message(object_like):
    assert isinstance(EnemyCompatibilityWarning().get_message(object_like), str)
