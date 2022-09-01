from typing import final

from pytest import raises

from foundry.core.namespace import (
    DEFAULT_ARGUMENT,
    PARENT_ARGUMENT,
    TYPE_INFO_ARGUMENT,
    IntegerValidator,
    Namespace,
    SequenceValidator,
    StringValidator,
    Validator,
)
from tests.core.namespace.test_validator import TestValidator


class TestSequenceValidator(TestValidator):
    __test_class__ = SequenceValidator.generate_class(Validator)
    __parent_class__: type[Validator] = Validator

    def test_type_manager(self):
        assert set(self.__parent_class__.type_manager.types.keys()).issubset(
            set(self.__test_class__.type_manager.types.keys())
        )

    def test_empty_list(self):
        assert not list(
            self.__test_class__.validate(
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: [],
                    PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager),
                }
            )
        )  # type: ignore


@final
class TestSequenceIntegerValidator(TestSequenceValidator):
    __test_class__ = SequenceValidator.generate_class(IntegerValidator)
    __parent_class__ = IntegerValidator

    def test_validate_primitive(self):
        assert list(
            self.__test_class__.validate(  # type: ignore
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: [1],
                    PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager),
                }
            )
        ) == [
            1
        ]  # type: ignore

    def test_validate_primitive_malformed(self):
        with raises((TypeError, ValueError)):
            self.__test_class__.validate(  # type: ignore
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: ["abc"],
                    PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager),
                }
            )

    def test_validate_complex(self):
        assert list(
            self.__test_class__.validate(  # type: ignore
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: [1, {TYPE_INFO_ARGUMENT: "FROM NAMESPACE", "name": "test", "path": ""}, 3],
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": IntegerValidator(2)}, validators=self.__test_class__.type_manager
                    ),
                }
            )
        ) == [1, 2, 3]

    def test_validate_by_type_simple(self):
        assert list(
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": self.__test_class__([IntegerValidator(1)])},  # type: ignore
                        validators=self.__test_class__.type_manager,
                    ),
                    "name": "test",
                    "path": "",
                }
            )
        ) == [1]


@final
class TestSequenceStringValidator(TestSequenceValidator):
    __test_class__ = SequenceValidator.generate_class(StringValidator)
    __parent_class__ = StringValidator

    def test_validate_primitive(self):
        assert list(
            self.__test_class__.validate(  # type: ignore
                {
                    TYPE_INFO_ARGUMENT: "DEFAULT",
                    DEFAULT_ARGUMENT: [StringValidator("abc")],
                    PARENT_ARGUMENT: Namespace(validators=self.__test_class__.type_manager),
                }
            )
        ) == [
            "abc"
        ]  # type: ignore

    def test_validate_by_type_simple(self):
        assert list(
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": self.__test_class__([StringValidator("abc")])},  # type: ignore
                        validators=self.__test_class__.type_manager,
                    ),
                    "name": "test",
                    "path": "",
                }
            )
        ) == ["abc"]
