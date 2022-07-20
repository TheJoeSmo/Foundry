from pytest import fixture, mark, raises

from foundry.core.namespace import (
    DEFAULT_ARGUMENT,
    PARENT_ARGUMENT,
    TYPE_INFO_ARGUMENT,
    TYPE_INFO_ARGUMENTS,
    IntegerValidator,
    Namespace,
    TypeInformation,
    _ValidatorHelper,
)


class TestValidatorHelper:
    __test_class__ = _ValidatorHelper

    @fixture(scope="session")
    def int_namespace(self):
        return Namespace(validators=IntegerValidator.type_manager)

    @fixture(scope="session")
    def partial_int_argument(self, int_namespace):
        return {
            DEFAULT_ARGUMENT: 1,
            PARENT_ARGUMENT: int_namespace,
        }

    @fixture(scope="session")
    def int_arguments(self, partial_int_argument):
        return partial_int_argument | {TYPE_INFO_ARGUMENT: IntegerValidator.default_name}

    def test_is_valid_type_name(self):
        assert self.__test_class__.is_valid_type_name("int")
        assert self.__test_class__.is_valid_type_name("str")
        assert self.__test_class__.is_valid_type_name("fancy_integer")
        assert self.__test_class__.is_valid_type_name("fancy integer")
        assert not self.__test_class__.is_valid_type_name("__INTEGER__")

    def test_get_type_identity(self, int_arguments):
        assert self.__test_class__.get_type_identity(int_arguments) == IntegerValidator.default_name

    def test_get_type_identity_not_provided(self):
        with raises(KeyError):
            assert self.__test_class__.get_type_identity({})

    def test_get_parent_suggestion(self, int_namespace, int_arguments):
        assert self.__test_class__.get_parent_suggestion(int_arguments) == int_namespace

    def test_get_parent_suggestion_not_provided(self):
        assert self.__test_class__.get_parent_suggestion({}) is None

    @mark.parametrize("type_argument", TYPE_INFO_ARGUMENTS)
    def test_get_type_identity_suggestion_simple(self, type_argument, partial_int_argument):
        int_argument = partial_int_argument | {type_argument: IntegerValidator.default_name}
        assert self.__test_class__.get_type_identity_suggestion(int_argument) == IntegerValidator.default_name

    def test_get_type_identity_suggestion_not_provided(self, partial_int_argument):
        assert self.__test_class__.get_type_identity_suggestion(partial_int_argument) is None

    @mark.parametrize("invalid_argument", [set(), [], 1, 1.1])
    def test_get_type_identity_suggestion_invalid(self, partial_int_argument, invalid_argument):
        int_argument = partial_int_argument | {TYPE_INFO_ARGUMENT: invalid_argument}
        with raises(TypeError):
            self.__test_class__.get_type_identity_suggestion(int_argument)

    def test_get_type_information_simple_without_default(self, int_arguments, int_namespace):
        assert self.__test_class__.get_type_information(int_arguments) == TypeInformation(
            IntegerValidator.default_name, parent=int_namespace
        )

    def test_get_type_information_simple_with_default(self, int_arguments, int_namespace):
        assert self.__test_class__.get_type_information(
            int_arguments, TypeInformation(IntegerValidator.default_name)
        ) == TypeInformation(IntegerValidator.default_name, parent=int_namespace)

    def test_get_type_information_simple_not_provided_without_default(self, partial_int_argument):
        assert self.__test_class__.get_type_information(partial_int_argument) is None

    def test_get_type_information_simple_not_provided_with_default(self, partial_int_argument, int_namespace):
        value = self.__test_class__.get_type_information(
            partial_int_argument, TypeInformation(IntegerValidator.default_name)
        )
        assert value is not None
        assert value == TypeInformation(IntegerValidator.default_name, parent=int_namespace)
        assert value.parent == int_namespace
