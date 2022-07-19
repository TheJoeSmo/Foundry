from pytest import fixture

from foundry.core.namespace import Namespace


@fixture
def empty_namespace():
    return Namespace(None, {}, {}, {})


@fixture
def namespace_with_parent(empty_namespace):
    return Namespace(empty_namespace, {}, {}, {})


@fixture
def namespace_with_dependency(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {}, {})


@fixture
def namespace_with_parent_with_dependency(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace}, {}, {})


@fixture
def namespace_with_dependencies(empty_namespace):
    return Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {}, {})


@fixture
def namespace_with_parent_with_dependencies(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {}, {})


@fixture
def namespace_with_dependency_with_child(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {}, {"a": empty_namespace})


@fixture
def namespace_with_parent_with_dependency_with_child(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace}, {}, {"a": empty_namespace})


@fixture
def namespace_with_dependencies_with_child(empty_namespace):
    return Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace})


@fixture
def namespace_with_parent_with_dependencies_with_child(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace})


@fixture
def namespace_with_dependency_with_children(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace})


@fixture
def namespace_with_parent_with_dependency_with_children(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace})


@fixture
def namespace_with_dependencies_with_children(empty_namespace):
    return Namespace(
        None, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace}
    )


@fixture
def namespace_with_parent_with_dependencies_with_children(empty_namespace):
    return Namespace(
        empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {}, {"a": empty_namespace, "b": empty_namespace}
    )


@fixture
def namespace_with_dependency_with_child_with_element(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace})


@fixture
def namespace_with_parent_with_dependency_with_child_with_element(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace})


@fixture
def namespace_with_dependencies_with_child_with_element(empty_namespace):
    return Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {"c": 1}, {"a": empty_namespace})


@fixture
def namespace_with_parent_with_dependencies_with_child_with_element(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {"c": 1}, {"a": empty_namespace})


@fixture
def namespace_with_dependency_with_children_with_element(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace, "b": empty_namespace})


@fixture
def namespace_with_parent_with_dependency_with_children_with_element(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1}, {"a": empty_namespace, "b": empty_namespace})


@fixture
def namespace_with_dependencies_with_children_with_element(empty_namespace):
    return Namespace(
        None, {"a": empty_namespace, "b": empty_namespace}, {"c": 1}, {"a": empty_namespace, "b": empty_namespace}
    )


@fixture
def namespace_with_parent_with_dependencies_with_children_with_element(empty_namespace):
    return Namespace(
        empty_namespace,
        {"a": empty_namespace, "b": empty_namespace},
        {"c": 1},
        {"a": empty_namespace, "b": empty_namespace},
    )


@fixture
def namespace_with_dependency_with_child_with_elements(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


@fixture
def namespace_with_parent_with_dependency_with_child_with_elements(empty_namespace):
    return Namespace(empty_namespace, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


@fixture
def namespace_empty_with_dependencies_with_child_with_elements(empty_namespace):
    return Namespace(None, {"a": empty_namespace, "b": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace})


@fixture
def namespace_with_parent_with_dependencies_with_child_with_elements(empty_namespace):
    return Namespace(
        empty_namespace, {"a": empty_namespace, "b": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace}
    )


@fixture
def namespace_empty_with_dependency_with_children_with_elements(empty_namespace):
    return Namespace(None, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace, "b": empty_namespace})


@fixture
def namespace_with_parent_with_dependency_with_children_with_elements(empty_namespace):
    return Namespace(
        empty_namespace, {"a": empty_namespace}, {"c": 1, "d": 2}, {"a": empty_namespace, "b": empty_namespace}
    )


@fixture
def namespace_empty_with_dependencies_with_children_with_elements(empty_namespace):
    return Namespace(
        None,
        {"a": empty_namespace, "b": empty_namespace},
        {"c": 1, "d": 2},
        {"a": empty_namespace, "b": empty_namespace},
    )


@fixture
def namespace_with_parent_with_dependencies_with_children_with_elements(empty_namespace):
    return Namespace(
        empty_namespace,
        {"a": empty_namespace, "b": empty_namespace},
        {"c": 1, "d": 2},
        {"a": empty_namespace, "b": empty_namespace},
    )


@fixture
def all_namespaces(
    empty_namespace,
    namespace_with_parent,
    namespace_with_parent_with_dependencies,
    namespace_with_dependency,
    namespace_with_dependency_with_child,
    namespace_with_parent_with_dependency,
    namespace_with_parent_with_dependency_with_child,
    namespace_with_dependencies,
    namespace_with_dependencies_with_child,
    namespace_with_parent_with_dependencies_with_child,
    namespace_with_dependency_with_children,
    namespace_with_parent_with_dependencies_with_children,
    namespace_with_dependencies_with_child_with_element,
    namespace_with_parent_with_dependency_with_children,
    namespace_with_parent_with_dependency_with_child_with_element,
    namespace_with_dependencies_with_children,
    namespace_with_dependency_with_children_with_element,
    namespace_with_dependency_with_child_with_element,
    namespace_with_dependencies_with_children_with_element,
    namespace_with_dependency_with_child_with_elements,
    namespace_with_parent_with_dependencies_with_child_with_element,
    namespace_with_parent_with_dependency_with_child_with_elements,
    namespace_empty_with_dependency_with_children_with_elements,
    namespace_with_parent_with_dependency_with_children_with_element,
    namespace_with_parent_with_dependencies_with_child_with_elements,
    namespace_with_parent_with_dependencies_with_children_with_elements,
    namespace_with_parent_with_dependencies_with_children_with_element,
    namespace_empty_with_dependencies_with_children_with_elements,
    namespace_empty_with_dependencies_with_child_with_elements,
    namespace_with_parent_with_dependency_with_children_with_elements,
):

    return [
        empty_namespace,
        namespace_with_parent,
        namespace_with_parent_with_dependencies,
        namespace_with_dependency,
        namespace_with_dependency_with_child,
        namespace_with_parent_with_dependency,
        namespace_with_parent_with_dependency_with_child,
        namespace_with_dependencies,
        namespace_with_dependencies_with_child,
        namespace_with_parent_with_dependencies_with_child,
        namespace_with_dependency_with_children,
        namespace_with_parent_with_dependencies_with_children,
        namespace_with_dependencies_with_child_with_element,
        namespace_with_parent_with_dependency_with_children,
        namespace_with_parent_with_dependency_with_child_with_element,
        namespace_with_dependencies_with_children,
        namespace_with_dependency_with_children_with_element,
        namespace_with_dependency_with_child_with_element,
        namespace_with_dependencies_with_children_with_element,
        namespace_with_dependency_with_child_with_elements,
        namespace_with_parent_with_dependencies_with_child_with_element,
        namespace_with_parent_with_dependency_with_child_with_elements,
        namespace_empty_with_dependency_with_children_with_elements,
        namespace_with_parent_with_dependency_with_children_with_element,
        namespace_with_parent_with_dependencies_with_child_with_elements,
        namespace_with_parent_with_dependencies_with_children_with_elements,
        namespace_with_parent_with_dependencies_with_children_with_element,
        namespace_empty_with_dependencies_with_children_with_elements,
        namespace_empty_with_dependencies_with_child_with_elements,
        namespace_with_parent_with_dependency_with_children_with_elements,
    ]
