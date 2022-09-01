from typing import final

from pytest import raises

from foundry.core.namespace import (
    DEFAULT_ARGUMENT,
    PARENT_ARGUMENT,
    TYPE_INFO_ARGUMENT,
    IntegerValidator,
    Namespace,
    StringValidator,
    TupleValidator,
    Validator,
)
from tests.core.namespace.test_validator import TestValidator


def test_tuple_of_same_type():
    IntegerTupleValidator = TupleValidator.generate_class((IntegerValidator, IntegerValidator, IntegerValidator))
    assert list(
        IntegerTupleValidator.validate(  # type: ignore
            {
                TYPE_INFO_ARGUMENT: "DEFAULT",
                DEFAULT_ARGUMENT: [1, {TYPE_INFO_ARGUMENT: "FROM NAMESPACE", "name": "test", "path": ""}, 3],
                PARENT_ARGUMENT: Namespace(
                    elements={"test": IntegerValidator(2)}, validators=IntegerTupleValidator.type_manager
                ),
            }
        )
    ) == [1, 2, 3]


def test_tuple_of_different_type():
    IntegerTupleValidator = TupleValidator.generate_class((StringValidator, IntegerValidator, IntegerValidator))
    assert list(
        IntegerTupleValidator.validate(  # type: ignore
            {
                TYPE_INFO_ARGUMENT: "DEFAULT",
                DEFAULT_ARGUMENT: ["abc", {TYPE_INFO_ARGUMENT: "FROM NAMESPACE", "name": "test", "path": ""}, 3],
                PARENT_ARGUMENT: Namespace(
                    elements={"test": IntegerValidator(2)}, validators=IntegerTupleValidator.type_manager
                ),
            }
        )
    ) == ["abc", 2, 3]


def test_tuple_of_malformed_type():
    IntegerTupleValidator = TupleValidator.generate_class((IntegerValidator, IntegerValidator, IntegerValidator))
    with raises((TypeError, ValueError)):
        IntegerTupleValidator.validate(  # type: ignore
            {
                TYPE_INFO_ARGUMENT: "DEFAULT",
                DEFAULT_ARGUMENT: ["abc", {TYPE_INFO_ARGUMENT: "FROM NAMESPACE", "name": "test", "path": ""}, 3],
                PARENT_ARGUMENT: Namespace(
                    elements={"test": IntegerValidator(2)}, validators=IntegerTupleValidator.type_manager
                ),
            }
        )


class TestTupleValidator(TestValidator):
    __test_class__ = TupleValidator.generate_class((Validator,))
    __parent_class__: tuple[type[Validator], ...] = (Validator,)

    def test_type_manager(self):
        for parent in self.__parent_class__:
            assert set(parent.type_manager.types.keys()).issubset(set(self.__test_class__.type_manager.types.keys()))


@final
class TestTupleIntegerValidator(TestTupleValidator):
    __test_class__ = TupleValidator.generate_class((IntegerValidator,))
    __parent_class__ = (IntegerValidator,)

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
class TestTupleStringValidator(TestTupleValidator):
    __test_class__ = TupleValidator.generate_class((StringValidator,))
    __parent_class__ = (StringValidator,)

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
