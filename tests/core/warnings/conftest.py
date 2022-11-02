from contextlib import contextmanager

from hypothesis.strategies import builds, integers

from tests.core.warnings import ObjectLike


def object_like(min_x: int = 0, max_x: int = 512, min_y: int = 0, max_y: int = 512):
    return builds(ObjectLike, integers(min_x, max_x), integers(min_y, max_y))


@contextmanager
def level_contains():
    class Level:
        def get_rect(*args, **kwargs):
            class Rect:
                def __contains__(*args, **kwargs) -> bool:
                    return True

            return Rect()

    yield Level()


@contextmanager
def level_does_not_contains():
    class Level:
        def get_rect(*args, **kwargs):
            class Rect:
                def __contains__(*args, **kwargs) -> bool:
                    return False

            return Rect()

    yield Level()


@contextmanager
def level_has_next_area():
    class Level:
        has_next_area = True

    yield Level()


@contextmanager
def level_does_not_has_next_area():
    class Level:
        has_next_area = False

    yield Level()
