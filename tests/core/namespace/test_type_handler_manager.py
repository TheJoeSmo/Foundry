from pytest import fixture

from foundry.core.namespace import TypeHandler, TypeHandlerManager


@fixture(scope="session")
def meta_validator_function():
    def validate(cls, *args):
        return cls(*args)

    return validate


@fixture(scope="session")
def int_handler(meta_validator_function):
    return TypeHandler({"default": meta_validator_function}, default_type_suggestion=int)


@fixture(scope="session")
def str_handler(meta_validator_function):
    return TypeHandler({"default": meta_validator_function}, default_type_suggestion=int)


@fixture(scope="session")
def int_extra_handler(meta_validator_function):
    return TypeHandler({"extra": meta_validator_function}, default_type_suggestion=int)


def test_type_handler_manager_initialization_empty():
    a = TypeHandlerManager()
    assert a.types.items() == {}.items()


def test_type_handler_manager_initialization_simple(int_handler, str_handler):
    a = TypeHandlerManager({"int": int_handler, "str": str_handler})
    assert a.types.items() == {"int": int_handler, "str": str_handler}.items()


def test_type_handler_manager_from_managers_empty():
    assert TypeHandlerManager.from_managers() == TypeHandlerManager()


def test_type_handler_manager_from_managers_simple(int_handler, str_handler):
    assert TypeHandlerManager.from_managers(
        TypeHandlerManager({"int": int_handler}), TypeHandlerManager({"str": str_handler})
    ) == TypeHandlerManager({"int": int_handler, "str": str_handler})


def test_type_handler_manager_from_managers_complex(int_handler, str_handler, int_extra_handler):
    assert TypeHandlerManager.from_managers(
        TypeHandlerManager({"int": str_handler}),
        TypeHandlerManager({"int": int_handler}),
        TypeHandlerManager({"int": int_extra_handler}),
    ) == TypeHandlerManager(
        {"int": str_handler.overwrite_from_parent(int_handler).overwrite_from_parent(int_extra_handler)}
    )


def test_type_handler_manager_override_type_handler_empty(int_handler):
    assert TypeHandlerManager().override_type_handler("int", int_handler) == TypeHandlerManager({"int": int_handler})


def test_type_handler_manager_override_type_handler_simple(int_handler, int_extra_handler):
    assert TypeHandlerManager({"int": int_extra_handler}).override_type_handler(
        "int", int_handler
    ) == TypeHandlerManager({"int": int_handler})


def test_type_handler_manager_override_type_handler_complex(int_handler, str_handler, int_extra_handler):
    assert TypeHandlerManager({"int": int_extra_handler, "str": int_handler}).override_type_handler(
        "int", int_handler
    ).override_type_handler("str", str_handler) == TypeHandlerManager({"int": int_handler, "str": str_handler})


def test_type_handler_manager_add_type_handler_empty(int_handler):
    assert TypeHandlerManager().add_type_handler("int", int_handler) == TypeHandlerManager({"int": int_handler})


def test_type_handler_manager_add_type_handler_simple(int_handler, int_extra_handler):
    assert TypeHandlerManager({"int": int_extra_handler}).add_type_handler("int", int_handler) == TypeHandlerManager(
        {"int": int_extra_handler.overwrite_from_parent(int_handler)}
    )


def test_type_handler_manager_add_type_handler_complex(int_handler, str_handler, int_extra_handler):
    assert TypeHandlerManager({"int": int_extra_handler, "str": int_handler}).add_type_handler(
        "int", int_handler
    ).add_type_handler("str", str_handler) == TypeHandlerManager(
        {
            "int": int_extra_handler.overwrite_from_parent(int_handler),
            "str": int_handler.overwrite_from_parent(str_handler),
        }
    )


def test_type_handler_manager_from_select_types_empty():
    assert TypeHandlerManager().from_select_types("test") == TypeHandlerManager()


def test_type_handler_manager_from_select_types_simple(int_handler, str_handler):
    assert TypeHandlerManager({"int": int_handler, "str": str_handler}).from_select_types("int") == TypeHandlerManager(
        {"int": int_handler}
    )


def test_type_handler_manager_from_select_types_complex(int_handler, str_handler):
    assert TypeHandlerManager({"int": int_handler, "str": str_handler}).from_select_types(
        "int", "integers"
    ) == TypeHandlerManager({"int": int_handler})
