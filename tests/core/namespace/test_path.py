from pytest import raises

from foundry.core.namespace.Path import InvalidChildName, Path, is_valid_name


def test_is_valid_name_empty():
    assert not is_valid_name("")


def test_is_valid_name_short_simple():
    assert is_valid_name("a")


def test_is_valid_name_simple():
    assert is_valid_name("hello")


def test_is_valid_name_simple_caps():
    assert is_valid_name("HELLO")


def test_is_valid_name_with_underscore_start():
    assert is_valid_name("_hello")


def test_is_valid_name_with_dot():
    assert not is_valid_name("hello.world")


def test_is_valid_with_int():
    assert not is_valid_name(1)


def test_empty_path():
    assert "" == str(Path(()))


def test_invalid_empty_path():
    with raises(InvalidChildName):
        Path(("",))


def test_invalid_int_path():
    with raises(InvalidChildName):
        Path((1,))  # type: ignore


def test_simple_path():
    assert "a" == str(Path(("a",)))


def test_lower_case_name_path():
    assert "hello" == str(Path(("hello",)))


def test_upper_case_name_path():
    assert "HELLO" == str(Path(("HELLO",)))


def test_underscore_name_path():
    assert "_hello" == str(Path(("_hello",)))


def test_invalid_name_dot_path():
    with raises(InvalidChildName):
        Path(("hello.world",))


def test_complex_path():
    assert "a.b.c" == str(Path(("a", "b", "c")))


def test_complex_path_with_empty_start():
    with raises(InvalidChildName):
        Path(("", "a", "b", "c"))


def test_complex_path_with_invalid():
    with raises(InvalidChildName):
        Path(("a", "b", "c.d"))


def test_path_from_invalid_type():
    with raises(TypeError):
        Path(["a", "b", "c"])  # type: ignore


def test_name_from_empty():
    assert "" == Path(()).name


def test_name_from_simple_root():
    assert "a" == Path(("a",)).name


def test_name_from_simple_parent():
    assert "c" == Path(("a", "b", "c")).name


def test_create_child_simple():
    assert "a.b" == str(Path(("a",)).create_child("b"))


def test_create_child_complex():
    assert "a.b.c" == str(Path(("a", "b")).create_child("c"))


def test_create_child_invalid_name():
    with raises(InvalidChildName):
        Path(("a",)).create_child("")


def test_create_child_invalid_int_as_name():
    with raises(InvalidChildName):
        Path(("a",)).create_child(1)  # type: ignore


def test_create_child_from_parent_simple():
    assert "a.b" == str(Path.create_child_from_parent(Path(("a",)), "b"))


def test_create_child_from_parent_complex():
    assert "a.b.c" == str(Path.create_child_from_parent(Path(("a", "b")), "c"))


def test_create_child_from_parent_invalid_name():
    with raises(InvalidChildName):
        Path.create_child_from_parent(Path(("a",)), "")


def test_create_child_from_parent_invalid_int_as_name():
    with raises(InvalidChildName):
        Path.create_child_from_parent(Path(("a",)), 1)  # type: ignore


def test_from_string_empty():
    assert "" == str(Path.from_string(""))


def test_from_string_simple():
    assert "a" == str(Path.from_string("a"))


def test_from_string_complex():
    assert "a.b.c" == str(Path.from_string("a.b.c"))


def test_from_string_empty_child():
    with raises(InvalidChildName):
        Path.from_string("a.b.")


def test_from_string_invalid_name():
    with raises(InvalidChildName):
        Path.from_string("a.@.c")
