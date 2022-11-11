from pytest import raises

from foundry.core.namespace import (
    ChildDoesNotExistException,
    CircularImportException,
    Namespace,
    Path,
    generate_namespace,
    get_namespace_dict_from_path,
    primitive_manager,
)


def test_namespace_initialization_empty():
    Namespace(None, {}, {}, {})


def test_namespace_initialization_with_parent(empty_namespace):
    Namespace(empty_namespace, {}, {}, {})


def test_namespace_initialization_empty_with_dependency(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {}, {})


def test_namespace_initialization_with_parent_with_dependency(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {}, {})


def test_namespace_initialization_empty_with_dependencies(empty_namespace):
    Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {}, {})


def test_namespace_initialization_with_parent_with_dependencies(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {}, {})


def test_namespace_initialization_empty_with_dependency_with_child(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {}, {"a": empty_namespace})


def test_namespace_initialization_with_parent_with_dependency_with_child(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {}, {"a": empty_namespace})


def test_namespace_initialization_empty_with_dependencies_with_child(empty_namespace):
    Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace})


def test_namespace_initialization_with_parent_with_dependencies_with_child(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace})


def test_namespace_initialization_empty_with_dependency_with_children(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_with_parent_with_dependency_with_children(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_empty_with_dependencies_with_children(empty_namespace):
    Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_with_parent_with_dependencies_with_children(empty_namespace):
    Namespace(
        empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace}
    )


def test_namespace_initialization_empty_with_dependency_with_child_with_element(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace})


def test_namespace_initialization_with_parent_with_dependency_with_child_with_element(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace})


def test_namespace_initialization_empty_with_dependencies_with_child_with_element(empty_namespace):
    Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {"c": 1}, {"a": empty_namespace})


def test_namespace_initialization_with_parent_with_dependencies_with_child_with_element(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {"c": 1}, {"a": empty_namespace})


def test_namespace_initialization_empty_with_dependency_with_children_with_element(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_with_parent_with_dependency_with_children_with_element(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_empty_with_dependencies_with_children_with_element(empty_namespace):
    Namespace(
        None, {"a": empty_namespace, "b": empty_namespace}, {"c": 1}, {"a": empty_namespace, "b": empty_namespace}
    )


def test_namespace_initialization_with_parent_with_dependencies_with_children_with_element(empty_namespace):
    Namespace(
        empty_namespace,
        {"a": empty_namespace, "b": empty_namespace},
        {"c": 1},
        {"a": empty_namespace, "b": empty_namespace},
    )


def test_namespace_initialization_empty_with_dependency_with_child_with_elements(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


def test_namespace_initialization_with_parent_with_dependency_with_child_with_elements(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


def test_namespace_initialization_empty_with_dependencies_with_child_with_elements(empty_namespace):
    Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


def test_namespace_initialization_with_parent_with_dependencies_with_child_with_elements(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


def test_namespace_initialization_empty_with_dependency_with_children_with_elements(empty_namespace):
    Namespace(None, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_with_parent_with_dependency_with_children_with_elements(empty_namespace):
    Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace, "b": empty_namespace})


def test_namespace_initialization_empty_with_dependencies_with_children_with_elements(empty_namespace):
    Namespace(
        None,
        {"a": empty_namespace, "b": empty_namespace},
        {"c": 1, "d": 2},
        {"a": empty_namespace, "b": empty_namespace},
    )


def test_namespace_initialization_with_parent_with_dependencies_with_children_with_elements(empty_namespace):
    Namespace(
        empty_namespace,
        {"a": empty_namespace, "b": empty_namespace},
        {"c": 1, "d": 2},
        {"a": empty_namespace, "b": empty_namespace},
    )


def test_namespace_from_namespace_is_equal(all_namespaces):
    for namespace in all_namespaces:
        namespace_from_namespace = Namespace(
            namespace.parent, namespace.dependencies, namespace.elements, namespace.children
        )
        assert namespace == namespace_from_namespace
        assert isinstance(namespace_from_namespace, Namespace)
        for child in namespace_from_namespace.children.values():
            assert namespace_from_namespace is child.parent


def test_namespace_root_none(all_namespaces):
    for namespace in all_namespaces:
        if namespace.parent is None:
            assert namespace.root is namespace


def test_namespace_root_not_none(all_namespaces):
    for namespace in all_namespaces:
        if namespace.parent is not None:
            namespace.root
            assert namespace.root is not namespace


def test_namespace_get_item_must_be_element_or_dependency(all_namespaces):
    for namespace in all_namespaces:
        for name in namespace:
            name_exist = False
            if name in namespace.elements:
                name_exist = True
            for d in namespace.dependencies.values():
                if name in d.elements:
                    name_exist = True
            assert name_exist


def test_namespace_namespace_exists_at_path_empty(empty_namespace):
    assert empty_namespace.namespace_exists_at_path(Path())
    assert not empty_namespace.namespace_exists_at_path(Path(("foo",)))


def test_namespace_namespace_exists_at_path_simple():
    namespace = Namespace(children={"foo": Namespace()})

    assert namespace.namespace_exists_at_path(Path())
    assert namespace.namespace_exists_at_path(Path(("foo",)))
    assert not namespace.namespace_exists_at_path(Path(("bar",)))


def test_namespace_namespace_exists_at_path_complex():
    namespace = Namespace(children={"foo": Namespace(children={"bar": Namespace()}), "bar": Namespace()})

    assert namespace.namespace_exists_at_path(Path())
    assert namespace.namespace_exists_at_path(Path(("foo",)))
    assert namespace.namespace_exists_at_path(Path(("bar",)))
    assert not namespace.namespace_exists_at_path(Path(("foo_bar",)))
    assert namespace.namespace_exists_at_path(Path(("foo", "bar")))
    assert not namespace.namespace_exists_at_path(Path(("bar", "foo")))


def test_namespace_from_path_empty(empty_namespace):
    assert empty_namespace is empty_namespace.from_path(Path())


def test_namespace_from_path_simple():
    namespace = Namespace(children={"foo": Namespace()})

    assert namespace is namespace.from_path(Path())
    assert namespace.children["foo"] is namespace.from_path(Path(("foo",)))


def test_namespace_from_path_complex():
    namespace = Namespace(children={"foo": Namespace(children={"bar": Namespace()}), "bar": Namespace()})

    assert namespace is namespace.from_path(Path())
    assert namespace.children["foo"] is namespace.from_path(Path(("foo",)))
    assert namespace.children["bar"] is namespace.from_path(Path(("bar",)))
    assert namespace.children["foo"].children["bar"] is namespace.from_path(Path(("foo", "bar")))


def test_generate_namespace_initialization_empty(empty_namespace):
    namespace = generate_namespace({"type": "INTEGER"}, primitive_manager)
    assert empty_namespace == namespace


def test_generate_namespace_initialization_with_int_elements():
    namespace = generate_namespace({"type": "INTEGER", "elements": {"a": 1, "b": 2, "c": 3}}, primitive_manager)
    assert Namespace(elements={"a": 1, "b": 2, "c": 3}) == namespace


def test_generate_namespace_initialization_empty_hierarchy(empty_namespace):
    namespace = generate_namespace({"type": "INTEGER", "children": {"a": {"type": "INTEGER"}}}, primitive_manager)
    assert Namespace(None, {}, {}, {"a": empty_namespace}) == namespace


def test_generate_namespace_initialization_inheritance_hierarchy_does_not_exist():
    with raises(ChildDoesNotExistException):
        generate_namespace(
            {
                "type": "INTEGER",
                "children": {
                    "bar": {"type": "INTEGER", "dependencies": ["foo"]},
                },
            },
            primitive_manager,
        )


def test_generate_namespace_initialization_inheritance_hierarchy():
    namespace = generate_namespace(
        {
            "type": "INTEGER",
            "children": {
                "foo": {"type": "INTEGER"},
                "bar": {"type": "INTEGER", "dependencies": ["foo"]},
            },
        },
        primitive_manager,
    )

    foo = Namespace()
    mutable_namespace = Namespace(children={"foo": foo, "bar": Namespace(dependencies={"foo": foo})})
    assert mutable_namespace == namespace


def test_generate_namespace_initialization_inheritance_hierarchy_circular_dependencies_on_self():
    with raises(CircularImportException):
        generate_namespace(
            {
                "type": "INTEGER",
                "children": {
                    "foo": {"type": "INTEGER", "dependencies": ["foo"]},
                },
            },
            primitive_manager,
        )


def test_generate_namespace_initialization_inheritance_hierarchy_circular_dependencies():
    with raises(CircularImportException):
        generate_namespace(
            {
                "type": "INTEGER",
                "children": {
                    "foo": {"type": "INTEGER", "dependencies": ["bar"]},
                    "bar": {"type": "INTEGER", "dependencies": ["foo"]},
                },
            },
            primitive_manager,
        )


def test_generate_namespace_initialization_inheritance_hierarchy_circular_dependencies_many():
    with raises(CircularImportException):
        generate_namespace(
            {
                "type": "INTEGER",
                "children": {
                    "foo": {"type": "INTEGER", "dependencies": ["foo_bar"]},
                    "bar": {"type": "INTEGER", "dependencies": ["foo"]},
                    "foo_bar": {"type": "INTEGER", "dependencies": ["bar"]},
                },
            },
            primitive_manager,
        )


def test_generate_namespace_initialization_inheritance_hierarchy_circular_dependencies_complex():
    with raises(CircularImportException):
        generate_namespace(
            {
                "type": "INTEGER",
                "children": {
                    "foo": {"type": "INTEGER", "dependencies": ["bar"]},
                    "bar": {"type": "INTEGER", "dependencies": ["bar_foo"]},
                    "foo_bar": {"type": "INTEGER", "dependencies": ["bar"]},
                    "bar_foo": {"type": "INTEGER", "dependencies": ["foo_bar"]},
                },
            },
            primitive_manager,
        )


def test_generate_namespace_initialization_inheritance_hierarchy_complex():
    namespace = generate_namespace(
        {
            "type": "INTEGER",
            "children": {
                "foo": {
                    "type": "INTEGER",
                    "children": {"foo_bar": {"type": "INTEGER", "dependencies": ["bar"]}},
                },
                "bar": {"type": "INTEGER", "dependencies": ["foo"]},
                "bar_foo": {"type": "INTEGER", "dependencies": ["foo.foo_bar"]},
            },
        },
        primitive_manager,
    )

    assert "foo" in namespace.children
    assert "bar" in namespace.children
    assert "bar_foo" in namespace.children
    assert "foo_bar" in namespace.children["foo"].children
    assert "bar" in namespace.children["foo"].children["foo_bar"].dependencies
    assert "foo" in namespace.children["bar"].dependencies
    assert "foo.foo_bar" in namespace.children["bar_foo"].dependencies


def test_get_namespace_dict_from_path_empty_namespace(empty_namespace):
    assert empty_namespace.dict() == get_namespace_dict_from_path(
        {"dependencies": {}, "elements": {}, "children": {}}, Path()
    )


def test_get_namespace_dict_from_path_child():
    d = {"dependencies": {}, "elements": {}, "children": {"foo": {"dependencies": {}, "elements": {}, "children": {}}}}
    expected_namespace = Namespace(children={"foo": Namespace()})

    assert expected_namespace.dict() == get_namespace_dict_from_path(d, Path())
    assert expected_namespace.children["foo"].dict() == get_namespace_dict_from_path(d, Path(("foo",)))


def test_evolve_child_from_empty():
    parent, child = Namespace(), Namespace()

    assert Namespace(children={"foo": Namespace()}) == parent.evolve_child("foo", child)


def test_evolve_child_from_simple():
    parent, child = Namespace(children={"foo": Namespace()}), Namespace()

    assert Namespace(children={"foo": Namespace(children={"bar": Namespace()})}) == parent.children["foo"].evolve_child(
        "bar", child
    )


def test_generate_namespace_generate_integer():
    namespace = generate_namespace({"type": "INTEGER", "elements": {"foo": 1}}, primitive_manager)

    assert Namespace(elements={"foo": 1}) == namespace


def test_generate_namespace_generate_string():
    namespace = generate_namespace({"type": "STRING", "elements": {"foo": "string"}}, primitive_manager)

    assert Namespace(elements={"foo": "string"}) == namespace


def test_generate_namespace_generate_float():
    namespace = generate_namespace({"type": "FLOAT", "elements": {"foo": 1.1}}, primitive_manager)

    assert Namespace(elements={"foo": 1.1}) == namespace


def test_generate_namespace_generate_file():
    from foundry import root_dir
    from foundry.core.file import FilePath

    namespace = generate_namespace({"type": "FILE", "elements": {"foo": "$data/gfx.png"}}, FilePath.type_manager)

    assert Namespace(elements={"foo": FilePath(root_dir) / "data" / "gfx.png"}) == namespace


def test_generate_namespace_generate_drawable():
    from foundry.core.drawable import Drawable

    # Just test that it loads.
    generate_namespace(
        {
            "type": "NONE",
            "children": {
                "foo": {"type": "FILE", "elements": {"bar": "$data/gfx.png"}},
                "bar": {
                    "type": "DRAWABLE",
                    "dependencies": ["foo"],
                    "elements": {
                        "foobar": {
                            "type": "FROM FILE",
                            "path": {"type": "FROM NAMESPACE", "path": "foo", "name": "bar"},
                        }
                    },
                },
            },
        },
        Drawable.type_manager,
    )
