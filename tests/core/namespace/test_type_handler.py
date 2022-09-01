from pytest import fixture, raises

from foundry.core.namespace import (
    PARENT_ARGUMENT,
    Namespace,
    TypeHandler,
    TypeInformation,
    TypeNotFoundException,
    ValidatorCallableInformation,
    _TypeHandlerManager,
)


@fixture(scope="session")
def meta_validator_function():
    def validate(cls, *args):
        return cls(*args)

    return validate


@fixture(scope="session")
def meta_validator_true_function():
    def validate(cls, *args):
        return True

    return validate


@fixture(scope="session")
def meta_validator_false_function():
    def validate(cls, *args):
        return False

    return validate


@fixture(scope="session")
def meta_validator_return_if_has_parent():
    def validate(cls, v):
        return PARENT_ARGUMENT in v

    return validate


@fixture(scope="session")
def meta_validator_return_type_passed():
    def validate(cls, *args):
        return cls

    return validate


@fixture(scope="session")
def meta_validator(meta_validator_function):
    return ValidatorCallableInformation(meta_validator_function)


@fixture(scope="session")
def meta_validator_use_parent(meta_validator_function):
    return ValidatorCallableInformation(meta_validator_function, use_parent=True)


@fixture(scope="session")
def meta_validator_not_use_parent(meta_validator_function):
    return ValidatorCallableInformation(meta_validator_function, use_parent=False)


@fixture(scope="session")
def meta_validator_int(meta_validator_function):
    return ValidatorCallableInformation(meta_validator_function, type_suggestion=int)


@fixture(scope="session")
def meta_validator_true(meta_validator_true_function):
    return ValidatorCallableInformation(meta_validator_true_function)


@fixture(scope="session")
def meta_validate_false(meta_validator_false_function):
    return ValidatorCallableInformation(meta_validator_false_function)


@fixture(scope="session")
def meta_validate_parent_test_use_parent(meta_validator_return_if_has_parent):
    return ValidatorCallableInformation(meta_validator_return_if_has_parent, use_parent=True)


@fixture(scope="session")
def meta_validate_parent_test_not_use_parent(meta_validator_return_if_has_parent):
    return ValidatorCallableInformation(meta_validator_return_if_has_parent, use_parent=False)


@fixture(scope="session")
def meta_validator_return_type_int(meta_validator_return_type_passed):
    return ValidatorCallableInformation(meta_validator_return_type_passed, type_suggestion=int)


@fixture(scope="session")
def meta_validator_return_type_not_provided(meta_validator_return_type_passed):
    return ValidatorCallableInformation(meta_validator_return_type_passed)


def test_type_handler_initialize_empty():
    a = TypeHandler()
    assert a.types == {}
    assert a.default_type_suggestion is None
    b = TypeHandler()
    assert a.types is not b.types
    assert a.types == b.types


def test_type_handler_initialize_default_type_suggestion():
    a = TypeHandler(default_type_suggestion=int)
    assert a.types == {}
    assert a.default_type_suggestion is int


def test_type_handler_eq_empty():
    assert TypeHandler() == TypeHandler({})


def test_type_handler_eq_default_type_suggestion():
    assert TypeHandler() != TypeHandler(default_type_suggestion=int)


def test_type_handler_eq_simple(meta_validator_function, meta_validator):
    assert TypeHandler({"test": meta_validator_function}) == TypeHandler({"test": meta_validator})


def test_type_handler_eq_complex(meta_validator_true_function, meta_validator):
    assert TypeHandler({"test": meta_validator_true_function}).overwrite_from_parent(
        TypeHandler({"test": meta_validator})
    ) == TypeHandler({"test": meta_validator})


def test_type_handler_initialize_validator_mapping_functions(meta_validator_function):
    a = TypeHandler({"test": meta_validator_function})
    assert "test" in a.types
    assert a.default_type_suggestion is None


def test_type_handler_initialize_validators_mapping_validators(meta_validator):
    a = TypeHandler({"test": meta_validator})
    assert a.types == {"test": meta_validator}
    assert a.default_type_suggestion is None


def test_type_handler_initialize_validator_mapping_functions_default_type_suggestion(meta_validator_function):
    a = TypeHandler({"test": meta_validator_function}, default_type_suggestion=int)
    assert "test" in a.types
    assert a.default_type_suggestion is int


def test_type_handler_initialize_validators_mapping_validators_default_type_suggestion(meta_validator):
    a = TypeHandler({"test": meta_validator}, default_type_suggestion=int)
    assert a.types == {"test": meta_validator}
    assert a.default_type_suggestion is int


def test_type_handler_overwrite_from_parent_simple(meta_validator_true, meta_validate_false):
    parent = TypeHandler({"test": meta_validator_true, "other": meta_validate_false})
    child = TypeHandler({"test": meta_validate_false, "old_test": meta_validator_true})
    result = parent.overwrite_from_parent(child)
    assert (
        result.types.items()
        == {"test": meta_validate_false, "other": meta_validate_false, "old_test": meta_validator_true}.items()
    )
    assert result.default_type_suggestion is None


def test_type_handler_overwrite_from_parent_default_type_suggestion():
    parent = TypeHandler(default_type_suggestion=int)
    child = TypeHandler(default_type_suggestion=str)
    result = parent.overwrite_from_parent(child)
    assert result.types.items() == child.types.items()


def test_type_handler_overwrite_from_parent_complex(meta_validator_true, meta_validate_false):
    parent = TypeHandler({"test": meta_validator_true, "other": meta_validate_false}, default_type_suggestion=int)
    child = TypeHandler({"test": meta_validate_false, "old_test": meta_validator_true}, default_type_suggestion=str)
    result = parent.overwrite_from_parent(child)
    assert (
        result.types.items()
        == {"test": meta_validate_false, "other": meta_validate_false, "old_test": meta_validator_true}.items()
    )
    assert result.default_type_suggestion is str


def test_type_handler_get_type_suggestion_from_class(meta_validator):
    assert (
        TypeHandler({"test": meta_validator}, default_type_suggestion=int).get_type_suggestion(TypeInformation("test"))
        is int
    )


def test_type_handler_get_type_suggestion_from_validator(meta_validator_int):
    assert (
        TypeHandler({"test": meta_validator_int}, default_type_suggestion=str).get_type_suggestion(
            TypeInformation("test")
        )
        is int
    )


def test_type_handler_get_type_suggestion_invalid():
    a = TypeHandler(default_type_suggestion=int)
    with raises(TypeNotFoundException):
        a.get_type_suggestion(TypeInformation("test"))


def test_type_handler_has_type_meta_validator_function(meta_validator_function):
    assert TypeHandler({"test": meta_validator_function}).has_type(TypeInformation("test"))


def test_type_handler_has_type_meta_validator(meta_validator):
    assert TypeHandler({"test": meta_validator}).has_type(TypeInformation("test"))


def test_type_handler_has_type_not():
    assert not TypeHandler().has_type(TypeInformation("test"))


def test_type_handler_get_if_validator_uses_parent_use_parent(meta_validator_use_parent):
    assert TypeHandler({"test": meta_validator_use_parent}).get_if_validator_uses_parent(TypeInformation("test"))


def test_type_handler_get_if_validator_uses_parent_not_use_parent(meta_validator_not_use_parent):
    assert not TypeHandler({"test": meta_validator_not_use_parent}).get_if_validator_uses_parent(
        TypeInformation("test")
    )


def test_type_handler_get_if_validator_uses_parent_invalid():
    a = TypeHandler()
    with raises(KeyError):
        a.get_if_validator_uses_parent(TypeInformation("test"))


def test_type_handler_get_validator_meta_validator_function(meta_validator_function):
    assert (
        TypeHandler({"test": meta_validator_function}).get_validator(TypeInformation("test")) is meta_validator_function
    )


def test_type_handler_get_validator_meta_validator(meta_validator):
    assert TypeHandler({"test": meta_validator}).get_validator(TypeInformation("test")) is meta_validator.validator


def test_type_handler_get_validator_invalid():
    a = TypeHandler()
    with raises(KeyError):
        a.get_validator(TypeInformation("test"))


def test_type_handler_validate_to_type_simple(meta_validator_true):
    bool_handler = TypeHandler({"test": meta_validator_true}, default_type_suggestion=bool)
    assert TypeHandler.validate_to_type(
        TypeInformation("bool", parent=Namespace(validators=_TypeHandlerManager({"bool": bool_handler}))),
        {"type": "test"},
    )


def test_type_handler_validate_to_type_use_parent(
    meta_validate_parent_test_use_parent, meta_validate_parent_test_not_use_parent
):
    bool_handler = TypeHandler(
        {"use parent": meta_validate_parent_test_use_parent, "no parent": meta_validate_parent_test_not_use_parent},
        default_type_suggestion=bool,
    )
    assert TypeHandler.validate_to_type(
        TypeInformation("bool", parent=Namespace(validators=_TypeHandlerManager({"bool": bool_handler}))),
        {"type": "use parent"},
    )
    assert not TypeHandler.validate_to_type(
        TypeInformation("bool", parent=Namespace(validators=_TypeHandlerManager({"bool": bool_handler}))),
        {"type": "no parent"},
    )


def test_type_handler_validate_to_type_passed(meta_validator_return_type_int, meta_validator_return_type_not_provided):
    handler = TypeHandler(
        {"int": meta_validator_return_type_int, "default": meta_validator_return_type_not_provided},
        default_type_suggestion=str,
    )
    assert (
        TypeHandler.validate_to_type(
            TypeInformation("types", parent=Namespace(validators=_TypeHandlerManager({"types": handler}))),
            {"type": "int"},
        )
        is int
    )
    assert (
        TypeHandler.validate_to_type(
            TypeInformation("types", parent=Namespace(validators=_TypeHandlerManager({"types": handler}))),
            {"type": "default"},
        )
        is str
    )


def test_type_handler_validate_to_type_invalid_no_type_passed():
    with raises(ValueError):
        TypeHandler.validate_to_type(
            TypeInformation("types", parent=Namespace(validators=_TypeHandlerManager({"types": TypeHandler()}))),
            {},
        )


def test_type_handler_validate_to_type_invalid_type_passed():
    with raises(TypeNotFoundException):
        TypeHandler.validate_to_type(
            TypeInformation("types", parent=Namespace(validators=_TypeHandlerManager({"types": TypeHandler()}))),
            {"type": "test"},
        )


def test_type_handler_validate_to_type_invalid_manager_passed():
    with raises(TypeError):
        TypeHandler.validate_to_type(TypeInformation("types"), {"type": "test"})


def test_type_handler_validate_to_type_invalid_no_type_suggestion(meta_validator_return_type_not_provided):
    handler = TypeHandler({"test": meta_validator_return_type_not_provided})
    with raises(ValueError):
        TypeHandler.validate_to_type(
            TypeInformation("types", parent=Namespace(validators=_TypeHandlerManager({"types": handler}))),
            {"type": "test"},
        )
