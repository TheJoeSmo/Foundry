from pytest import raises

from foundry.core.namespace import (
    DEFAULT_ARGUMENT,
    PARENT_ARGUMENT,
    TYPE_INFO_ARGUMENT,
    FloatValidator,
    IntegerValidator,
    Namespace,
    NonNegativeIntegerValidator,
    SingleArgumentValidator,
    StringValidator,
)
from tests.core.namespace.test_validator import TestValidator


class TestSingleArgumentValidator(TestValidator):
    __test_class__ = SingleArgumentValidator

    def test_get_default_argument_simple(self):
        assert self.__test_class__.get_default_argument(1) == 1
        assert self.__test_class__.get_default_argument("abc") == "abc"
        assert self.__test_class__.get_default_argument(1.1) == 1.1

    def test_get_default_argument_dictionary(self):
        assert (
            self.__test_class__.get_default_argument(
                {
                    DEFAULT_ARGUMENT: 1,
                    TYPE_INFO_ARGUMENT: IntegerValidator.default_name,
                    PARENT_ARGUMENT: Namespace(validators=IntegerValidator.type_manager),
                }
            )
            == 1
        )
        assert (
            self.__test_class__.get_default_argument(
                {
                    DEFAULT_ARGUMENT: "abc",
                    TYPE_INFO_ARGUMENT: StringValidator.default_name,
                    PARENT_ARGUMENT: Namespace(validators=StringValidator.type_manager),
                }
            )
            == "abc"
        )
        assert (
            self.__test_class__.get_default_argument(
                {
                    DEFAULT_ARGUMENT: 1.1,
                    TYPE_INFO_ARGUMENT: FloatValidator.default_name,
                    PARENT_ARGUMENT: Namespace(validators=FloatValidator.type_manager),
                }
            )
            == 1.1
        )

    def test_get_default_argument_dictionary_malformed(self):
        with raises(TypeError):
            self.__test_class__.get_default_argument(
                {DEFAULT_ARGUMENT: 1, PARENT_ARGUMENT: Namespace(validators=IntegerValidator.type_manager)}
            )
        with raises(TypeError):
            self.__test_class__.get_default_argument(
                {DEFAULT_ARGUMENT: "abc", PARENT_ARGUMENT: Namespace(validators=StringValidator.type_manager)}
            )
        with raises(TypeError):
            self.__test_class__.get_default_argument(
                {DEFAULT_ARGUMENT: 1.1, PARENT_ARGUMENT: Namespace(validators=FloatValidator.type_manager)}
            )


class TestIntegerValidator(TestSingleArgumentValidator):
    __test_class__ = IntegerValidator

    def test_validate_primitive_simple(self):
        assert self.__test_class__.validate_primitive(1) == 1

    def test_validate_primitive(self):
        assert self.__test_class__.validate_primitive({TYPE_INFO_ARGUMENT: "DEFAULT", DEFAULT_ARGUMENT: 1}) == 1

    def test_validate_by_type(self):
        assert (
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": self.__test_class__(1)}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )
            == 1
        )


class TestNonNegativeIntegerValidator(TestIntegerValidator):
    __test_class__ = NonNegativeIntegerValidator

    def test_validate_primitive_not_allow_negative(self):
        with raises(ValueError):
            self.__test_class__.validate_primitive(-1)


class TestStringValidator(TestSingleArgumentValidator):
    __test_class__ = StringValidator

    def test_validate_primitive_simple(self):
        assert self.__test_class__.validate_primitive("abc") == "abc"

    def test_validate_primitive(self):
        assert self.__test_class__.validate_primitive({TYPE_INFO_ARGUMENT: "DEFAULT", DEFAULT_ARGUMENT: "abc"}) == "abc"

    def test_validate_by_type(self):
        assert (
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": self.__test_class__("abc")}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )
            == "abc"
        )


class TestFloatValidator(TestSingleArgumentValidator):
    __test_class__ = FloatValidator

    def test_validate_primitive_simple(self):
        assert self.__test_class__.validate_primitive(1.1) == 1.1

    def test_validate_primitive(self):
        assert self.__test_class__.validate_primitive({TYPE_INFO_ARGUMENT: "DEFAULT", DEFAULT_ARGUMENT: 1.1}) == 1.1

    def test_validate_by_type(self):
        assert (
            self.__test_class__.validate_by_type(
                {
                    TYPE_INFO_ARGUMENT: "FROM NAMESPACE",
                    PARENT_ARGUMENT: Namespace(
                        elements={"test": self.__test_class__(1.1)}, validators=self.__test_class__.type_manager
                    ),
                    "name": "test",
                    "path": "",
                }
            )
            == 1.1
        )
