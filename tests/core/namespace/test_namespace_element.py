from pytest import raises

from foundry.core.namespace import Namespace, validate_element


def test_namespace_element_simple():
    namespace = Namespace(elements={"foo": 1})

    assert 1 == validate_element(parent=namespace, name="foo", type=int)


def test_namespace_element_complex():
    namespace = Namespace(elements={"foo": 1, "bar": 2, "foo_bar": 3})

    assert 1 == validate_element(parent=namespace, name="foo", type=int)
    assert 2 == validate_element(parent=namespace, name="bar", type=int)
    assert 3 == validate_element(parent=namespace, name="foo_bar", type=int)


def test_namespace_element_name_with_dot():
    namespace = Namespace(elements={"foo": 1})

    with raises(ValueError):
        validate_element(parent=namespace, name="foo.bar", type=int)


def test_namespace_element_name_with_special_characters():
    namespace = Namespace(elements={"foo": 1})

    with raises(ValueError):
        validate_element(parent=namespace, name="foo&bar", type=int)


def test_namespace_element_does_not_exist():
    namespace = Namespace(elements={"foo": 1})

    with raises(ValueError):
        validate_element(parent=namespace, name="bar", type=int)


def test_namespace_element_wrong_type():
    namespace = Namespace(elements={"foo": "a"})

    with raises(ValueError):
        validate_element(parent=namespace, name="foo", type=int)
