from pydantic import ValidationError
from pytest import raises

from foundry.core.namespace.Namespace import Namespace
from foundry.core.namespace.Path import Path
from foundry.core.namespace.PydanticPath import PydanticPath


def test_pydantic_path_name_empty():
    assert Path() == PydanticPath(use_parent=False, path="").to_path()


def test_pydantic_path_short_simple():
    assert Path.from_string("a") == PydanticPath(use_parent=False, path="a").to_path()


def test_pydantic_path_simple():
    assert Path.from_string("hello") == PydanticPath(use_parent=False, path="hello").to_path()


def test_pydantic_path_simple_caps():
    assert Path.from_string("HELLO") == PydanticPath(use_parent=False, path="HELLO").to_path()


def test_pydantic_path_with_underscore_start():
    assert Path.from_string("_hello") == PydanticPath(use_parent=False, path="_hello").to_path()


def test_pydantic_path_with_dot():
    assert Path.from_string("hello.world") == PydanticPath(use_parent=False, path="hello.world").to_path()


def test_pydantic_path_with_incomplete_dot():
    with raises(ValidationError):
        PydanticPath(use_parent=False, path="hello.world.")


def test_pydantic_path_with_invalid_string():
    with raises(ValidationError):
        PydanticPath(use_parent=False, path="hello@world")


def test_pydantic_path_with_invalid_middle_name():
    with raises(ValidationError):
        PydanticPath(use_parent=False, path="hello..world")


def test_pydantic_path_no_parent():
    with raises(ValidationError):
        PydanticPath(path="foo")


def test_pydantic_path_namespace_validation_root():
    namespace = Namespace(children={"foo": Namespace()})

    assert Path() == PydanticPath(parent=namespace, path="").to_path()


def test_pydantic_path_namespace_validation_simple():
    namespace = Namespace(children={"foo": Namespace()})

    assert Path.from_string("foo") == PydanticPath(parent=namespace, path="foo").to_path()


def test_pydantic_path_int():
    with raises(ValidationError):
        PydanticPath(use_parent=False, path=1)  # type: ignore
