from typing import Any, final

from pytest import raises

from foundry.core.namespace import (
    DEFAULT_ARGUMENT,
    NOT_PROVIDED_ARGUMENT,
    PARENT_ARGUMENT,
    TYPE_INFO_ARGUMENT,
    DefaultValidator,
    IntegerValidator,
    Namespace,
    StringValidator,
    Validator,
)
from tests.core.namespace.test_validator import TestValidator


class TestDefaultValidator(TestValidator):
    __test_class__ = DefaultValidator.generate_class(Validator, None)
    __parent_class__: type[Validator] = Validator
    __default_value__: Any = None

    def test_type_manager(self):
        assert set(self.__parent_class__.type_manager.types.keys()).issubset(
            set(self.__test_class__.type_manager.types.keys())
        )

    def test_validate_primitive_default(self):
        assert (
            self.__test_class__.validate(  # type: ignore
                {PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager), NOT_PROVIDED_ARGUMENT: None}
            )
            is self.__default_value__
        )


@final
class TestDefaultIntegerValidator(TestDefaultValidator):
    __test_class__ = DefaultValidator.generate_class(IntegerValidator, 42)
    __parent_class__ = IntegerValidator
    __default_value__ = 42

    def test_validate_primitive(self):
        assert (
            self.__test_class__.validate(  # type: ignore
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: IntegerValidator(1),
                    PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager),
                }
            )
            == 1
        )  # type: ignore

    def test_validate_malformed(self):
        with raises((TypeError, ValueError)):
            self.__test_class__.validate(  # type: ignore
                {DEFAULT_ARGUMENT: "abc", PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager)}
            )

    def test_validate_by_type_simple(self):
        assert (
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": IntegerValidator(1)}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )
            == 1
        )

    def test_validate_by_type_malformed(self):
        with raises((TypeError, ValueError)):
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": StringValidator("abc")}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )


@final
class TestDefaultStringValidator(TestDefaultValidator):
    __test_class__ = DefaultValidator.generate_class(StringValidator, "xyz")
    __parent_class__ = StringValidator
    __default_value__ = "xyz"

    def test_validate_primitive(self):
        assert (
            self.__test_class__.validate(  # type: ignore
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: StringValidator("abc"),
                    PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager),
                }
            )
            == "abc"
        )  # type: ignore

    def test_validate_by_type_simple(self):
        assert (
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": StringValidator("abc")}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )
            == "abc"
        )

    def test_validate_by_type_malformed(self):
        with raises((TypeError, ValueError)):
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": IntegerValidator(1)}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )
