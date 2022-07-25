from pytest import raises

from foundry.core.namespace import IntegerValidator, Namespace, TypeHandler, Validator


class NamespaceValidatorTypeOnly(Validator):
    @classmethod
    def validate_by_type(cls, v):
        return True


class NamespaceValidatorTypeOnlyDefault(NamespaceValidatorTypeOnly):
    __type_default__ = "FROM NAMESPACE"


class NamespaceValidatorExtendedSimple(Validator):
    def simple(*_):
        return True

    __validator_handler__ = TypeHandler({"TEST": simple})  # type: ignore


class NamespaceValidatorExtendedOverwrite(NamespaceValidatorExtendedSimple):
    def overwrite(*_):
        return False

    __validator_handler__ = TypeHandler({"TEST": overwrite})  # type: ignore


class NamespaceValidatorExtendedAlternative(NamespaceValidatorExtendedSimple):
    __validator_handler__ = TypeHandler({"ALT": lambda *_: True})


class NamespaceValidatorExtendedMultiple(NamespaceValidatorExtendedAlternative, NamespaceValidatorExtendedSimple):
    pass


def test_validate_type():
    assert NamespaceValidatorTypeOnly.validate_type({"type": "FROM NAMESPACE"})


def test_validate_type_no_dict_with_int():
    with raises(TypeError):
        NamespaceValidatorTypeOnly.validate_type(1)


def test_validate_type_no_dict_with_str():
    with raises(TypeError):
        NamespaceValidatorTypeOnly.validate_type("test")


def test_validate_type_no_dict_with_list():
    with raises(TypeError):
        NamespaceValidatorTypeOnly.validate_type(["FROM NAMESPACE"])


def test_validate_type_no_type_no_default():
    with raises(TypeError):
        NamespaceValidatorTypeOnly.validate_type({})


def test_validate_type_no_type_with_default():
    assert NamespaceValidatorTypeOnlyDefault.validate_type({})


def test_validate_type_invalid_type_str():
    with raises(TypeError):
        NamespaceValidatorTypeOnly.validate_type({"type": ""})


def test_validate_by_type_validator_handler_extended_simple():
    assert NamespaceValidatorExtendedSimple.validate_by_type({"type": "TEST"})


def test_validate_type_validator_handler_extended_simple():
    assert NamespaceValidatorExtendedSimple.validate_type({"type": "TEST"})


def test_validate_by_type_validator_handler_extended_overwrite():
    assert not NamespaceValidatorExtendedOverwrite.validate_by_type({"type": "TEST"})


def test_validate_type_validator_handler_extended_overwrite():
    assert not NamespaceValidatorExtendedOverwrite.validate_type({"type": "TEST"})


def test_validate_by_type_validator_handler_extended_multiple():
    assert NamespaceValidatorExtendedMultiple.validate_by_type({"type": "TEST"})
    assert NamespaceValidatorExtendedMultiple.validate_by_type({"type": "ALT"})


def test_validate_type_validator_handler_extended_multiple():
    assert NamespaceValidatorExtendedMultiple.validate_type({"type": "TEST"})
    assert NamespaceValidatorExtendedMultiple.validate_type({"type": "ALT"})


def test_validate_from_namespace_no_parent():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(IntegerValidator, {})


def test_validate_from_namespace_parent_int():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(IntegerValidator, {"parent": IntegerValidator(1)})


def test_validate_from_namespace_parent_str():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(IntegerValidator, {"parent": ""})


def test_validate_from_namespace_parent_list():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator,
            {"parent": [Namespace(elements={"test": IntegerValidator(1)})], "name": "test", "path": ""},
        )


def test_validate_from_namespace_no_name():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "path": ""}
        )


def test_validate_from_namespace_name_int():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": 1, "path": ""}
        )


def test_validate_from_namespace_name_list():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator,
            {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": ["t", "e", "s", "t"], "path": ""},
        )


def test_validate_from_namespace_no_path():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test"}
        )


def test_validate_from_namespace_path_int():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test", "path": 1}
        )


def test_validate_from_namespace_path_list():
    with raises(TypeError):
        IntegerValidator.validate_from_namespace(
            IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test", "path": []}
        )


def test_validate_from_namespace():
    assert (
        IntegerValidator.validate_from_namespace(
            IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test", "path": ""}
        )
        == 1
    )
