from pytest import raises

from foundry.core.namespace import Namespace, Path


def test_pydantic_path_name_empty():
    assert Path() == Path.validate(use_parent=False, path="")


def test_pydantic_path_short_simple():
    assert Path.from_string("a") == Path.validate(use_parent=False, path="a")


def test_pydantic_path_simple():
    assert Path.from_string("hello") == Path.validate(use_parent=False, path="hello")


def test_pydantic_path_simple_caps():
    assert Path.from_string("HELLO") == Path.validate(use_parent=False, path="HELLO")


def test_pydantic_path_with_underscore_start():
    assert Path.from_string("_hello") == Path.validate(use_parent=False, path="_hello")


def test_pydantic_path_with_dot():
    assert Path.from_string("hello.world") == Path.validate(use_parent=False, path="hello.world")


def test_pydantic_path_with_incomplete_dot():
    with raises(ValueError):
        Path.validate(use_parent=False, path="hello.world.")


def test_pydantic_path_with_invalid_string():
    with raises(ValueError):
        Path.validate(use_parent=False, path="hello@world")


def test_pydantic_path_with_invalid_middle_name():
    with raises(ValueError):
        Path.validate(use_parent=False, path="hello..world")


def test_pydantic_path_no_parent():
    with raises(ValueError):
        Path.validate(path="foo")


def test_pydantic_path_namespace_validation_root():
    namespace = Namespace(children={"foo": Namespace()})

    assert Path() == Path.validate(parent=namespace, path="")


def test_pydantic_path_namespace_validation_simple():
    namespace = Namespace(children={"foo": Namespace()})

    assert Path.from_string("foo") == Path.validate(parent=namespace, path="foo")


def test_pydantic_path_int():
    with raises(TypeError):
        Path.validate(use_parent=False, path=1)  # type: ignore
