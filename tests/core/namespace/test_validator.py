from pytest import raises

from foundry.core.namespace import (
    PARENT_ARGUMENT,
    IntegerValidator,
    Namespace,
    Validator,
)
from tests.core.namespace.test_validator_helper import TestValidatorHelper


class TestValidator(TestValidatorHelper):
    __test_class__ = Validator

    def test_has_valid_names(self):
        for name in self.__test_class__.__names__[1:]:
            assert self.__test_class__.is_valid_type_name(name)

    def test_default_name_cannot_be_defined_by_user(self):
        assert not self.__test_class__.is_valid_type_name(self.__test_class__.default_name)

    def test_include_validators(self):
        assert self.__test_class__.type_handler.types.items() >= self.__test_class__.__validator_handler__.types.items()

    def test_exposes_all_names(self):
        assert all(name in self.__test_class__.type_manager.types for name in self.__test_class__.__names__)

    def test_can_get_itself_from_type_handler(self):
        assert self.__test_class__.get_type_handler_from_parent(Namespace(validators=self.__test_class__.type_manager))

    def test_get_type_handler_from_parent_not_present(self):
        with raises(TypeError):
            self.__test_class__.get_type_handler_from_parent(Namespace())

    def test_validate_from_namespace_no_parent(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(IntegerValidator, {})

    def test_validate_from_namespace_parent_int(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(IntegerValidator, {"parent": IntegerValidator(1)})

    def test_validate_from_namespace_parent_str(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(IntegerValidator, {"parent": ""})

    def test_validate_from_namespace_parent_list(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator,
                {"parent": [Namespace(elements={"test": IntegerValidator(1)})], "name": "test", "path": ""},
            )

    def test_validate_from_namespace_no_name(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "path": ""}
            )

    def test_validate_from_namespace_name_int(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": 1, "path": ""}
            )

    def test_validate_from_namespace_name_list(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator,
                {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": ["t", "e", "s", "t"], "path": ""},
            )

    def test_validate_from_namespace_no_path(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator, {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test"}
            )

    def test_validate_from_namespace_path_int(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator,
                {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test", "path": 1},
            )

    def test_validate_from_namespace_path_list(self):
        with raises(TypeError):
            self.__test_class__.validate_from_namespace(
                IntegerValidator,
                {"parent": Namespace(elements={"test": IntegerValidator(1)}), "name": "test", "path": []},
            )

    def test_validate_from_namespace(self):
        assert (
            self.__test_class__.validate_from_namespace(
                IntegerValidator,
                {PARENT_ARGUMENT: Namespace(elements={"test": IntegerValidator(1)}), "name": "test", "path": ""},
            )
            == 1
        )

    def test_validate_by_type_type_not_provided(self):
        with raises(KeyError):
            self.__test_class__.validate_by_type(
                {
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": IntegerValidator(1)},
                        validators=IntegerValidator.type_manager,
                    ),
                    "name": "test",
                    "path": "",
                }
            )
