from pydantic import ValidationError
from pytest import raises

from foundry.core.namespace.Namespace import Namespace
from foundry.core.namespace.NamespaceElement import NamespaceElement


def test_namespace_element_simple():
    namespace = Namespace(elements={"foo": 1})

    assert 1 == NamespaceElement(parent=namespace, name="foo", type_=int).element


def test_namespace_element_complex():
    namespace = Namespace(elements={"foo": 1, "bar": 2, "foo_bar": 3})

    assert 1 == NamespaceElement(parent=namespace, name="foo", type_=int).element
    assert 2 == NamespaceElement(parent=namespace, name="bar", type_=int).element
    assert 3 == NamespaceElement(parent=namespace, name="foo_bar", type_=int).element


def test_namespace_element_name_with_dot():
    namespace = Namespace(elements={"foo": 1})

    with raises(ValidationError):
        NamespaceElement(parent=namespace, name="foo.bar", type_=int).element


def test_namespace_element_name_with_special_characters():
    namespace = Namespace(elements={"foo": 1})

    with raises(ValidationError):
        NamespaceElement(parent=namespace, name="foo&bar", type_=int).element


def test_namespace_element_does_not_exist():
    namespace = Namespace(elements={"foo": 1})

    with raises(ValidationError):
        NamespaceElement(parent=namespace, name="bar", type_=int).element


def test_namespace_element_wrong_type():
    namespace = Namespace(elements={"foo": "a"})

    with raises(ValidationError):
        NamespaceElement(parent=namespace, name="foo", type_=int).element  # type: ignore
