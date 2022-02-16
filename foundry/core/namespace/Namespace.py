from __future__ import annotations

from collections import ChainMap
from collections.abc import Iterable
from graphlib import CycleError, TopologicalSorter
from typing import Any, Generic, Iterator, Optional, Sequence, TypeVar

from attr import attrs, evolve, field

from foundry.core.namespace import NamespaceType, Uninitializable
from foundry.core.namespace.Path import Path

_T = TypeVar("_T")


class NamespaceValidationException(Exception):
    """
    An exception that is raised during the validation of a namespace.
    """

    __slots__ = ()


class CircularImportException(NamespaceValidationException):
    """
    This exception is raised during the importation of dependencies if a cycle exists.  A cycle makes it
    so none of the `foundry.core.namespace.Namespace` inside the cycle could be fully initialized without
    violating the invariant of the namespace.  Thus, the namespaces cannot be initialized and this
    exception must be raised.

    Attributes
    ----------
    cycle: Optional[tuple[Path]]
        The cycle that was detected.
    """

    __slots__ = ("cycle",)

    cycle: Optional[tuple[Path]]

    def __init__(self, cycle: Optional[tuple[Path]] = None):
        self.cycle = cycle
        if self.cycle is not None:
            super().__init__(f"Cannot import because {[str(c) for c in self.cycle]} forms a cycle.")
        else:
            super().__init__("A cycle exists.")


class ParentDoesNotExistException(NamespaceValidationException):
    """
    A method is called where the :class:~`foundry.core.namespace.Namespace.Namespace` did not have parent
    where a parent was required.

    Attributes
    ----------
    child: Optional[Namespace]
        The child without a parent.
    """

    __slots__ = ("child",)

    child: Optional[Namespace]

    def __init__(self, child: Optional[Namespace] = None):
        self.child = child
        if self.child is not None:
            super().__init__(f"{child} does not have a parent.")
        else:
            super().__init__("No parent exists.")


class ChildDoesNotExistException(NamespaceValidationException):
    """
    A method is called where the :class:~`foundry.core.namespace.Namespace.Namespace` did not have child
    when a child was required.

    Attributes
    ----------
    parent: Optional[Namespace]
        The parent that did not contain
    path: Path
    unfound_child: str
    """

    __slots__ = "parent", "path", "unfound_child"

    parent: Optional[Namespace]
    path: Path
    unfound_child: str

    def __init__(self, path: Path, unfound_child: str, parent: Optional[Namespace] = None):
        self.path, self.unfound_child, self.parent = path, unfound_child, parent
        if self.parent is not None:
            super().__init__(f"{parent} did not contain {unfound_child} from path {path}")
        else:
            super().__init__(f"{unfound_child} does not exist inside {path}")


class ParentDoesNotContainChildException(NamespaceValidationException):
    """
    For each :class:~`foundry.core.namespace.Namespace.Namespace`, it is expected that the parent attribute
    also references the child.  If a method which relies on this functionality does finds that this is
    not the case, this exception will be raised.

    Attributes
    ----------
    parent: Namespace
        That does not have a reference to the child.
    child: Namespace
        The child which called the method that required this functionality.
    """

    __slots__ = "parent", "child"

    parent: Namespace
    child: Namespace

    def __init__(self, parent: Namespace, child: Namespace):
        self.parent = parent
        self.child = child
        super().__init__(f"{parent} does not reference {child}.")


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True, cache_hash=True, cmp=False, repr=False)
class Namespace(Generic[_T]):
    parent: Optional[Namespace] = field(eq=False, default=None)
    dependencies: dict[str, Namespace] = field(factory=dict)
    elements: dict[str, _T] = field(factory=dict)
    children: dict[str, Namespace] = field(factory=dict)

    def __attrs_post_init__(self):
        # Get around frozen object to magically make children connect to parent.
        object.__setattr__(
            self,
            "children",
            {k: Namespace(self, v.dependencies, v.elements, v.children) for k, v in self.children.items()},
        )

    def __eq__(self, other) -> bool:
        """
        Tests for equality between two elements.

        Parameters
        ----------
        other : Any
            The other element to be compared.

        Returns
        -------
        bool
            If these self and other are equivalent.

        Notes
        -----
        Parent is not checked for equality, as this creates a recursive loop.  Instead, it is advised to check the
        root for equality if such a check is desired.
        """
        return (
            isinstance(other, Namespace)
            and self.dependencies == other.dependencies
            and self.elements == other.elements
            and self.children == other.children
        )

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}("
        if self.parent is not None:
            s = f"{s}parent={self.parent}, "
        if self.dependencies:
            s = f"{s}dependencies={self.dependencies}, "
        if self.elements:
            s = f"{s}elements={self.elements}, "
        if self.children:
            s = f"{s}children={self.children}"
        if s[-1] == " ":
            s = s[:-2]
        return f"{s})"

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}("
        if self.dependencies:
            dependencies = {str(key) for key in self.dependencies}
            s = f"{s}dependencies={dependencies}, "
        if self.elements:
            elements = {str(k): str(v) for k, v in self.elements.items()}
            s = f"{s}elements={elements}, "
        if self.children:
            children = {str(k): str(v) for k, v in self.children.items()}
            s = f"{s}children={children}"
        if s[-1] == " ":
            s = s[:-2]
        return f"{s})"

    def __iter__(self) -> Iterator:
        return iter(self.public_elements)

    def __getitem__(self, key: str) -> Any:
        return self.public_elements[key]

    def dict(self) -> dict:
        """
        Converts the namespace to a dict that can be reconstructed back into itself.

        Returns
        -------
        dict
            A dict that represents a namespace.
        """
        return {
            "dependencies": {k: v.dict() for k, v in self.dependencies.items()},
            "elements": self.elements,
            "children": {k: v.dict() for k, v in self.children.items()},
        }

    @property
    def name(self) -> str:
        """
        Finds the name of the child inside its parent that refers to itself.

        Returns
        -------
        str
            The name that refers to itself from its parent.

        Raises
        ------
        ParentDoesNotExistException
            The parent of this instance is None.
        ParentDoesNotContainChildException
            The parent and child are not linked properly.
        """
        if self.parent is None:
            raise ParentDoesNotExistException(self)
        for name, child in self.parent.children.items():
            if child is self:
                return name
        raise ParentDoesNotContainChildException(self.parent, self)

    @property
    def path(self) -> Sequence[str]:
        """
        Provides a series of names or keys that will yield itself from the root node.

        Returns
        -------
        Sequence[str]
            A series of names to provide itself from the root node.
        """
        return list(self.parent.path) + [self.name] if self.parent is not None else []

    @property
    def root(self) -> Namespace:
        """
        Finds the child tree without a parent.  From the root node all other child tree of the same vein should
        be accessible.

        Returns
        -------
        ExtendedChildTree
            The namespace whose parent is None.
        """
        parent = self
        while parent.parent is not None:
            parent = parent.parent
        return parent

    @property
    def public_elements(self) -> ChainMap:
        """
        The entire dict of elements that can be accessed via the dictionary interface.

        Returns
        -------
        ChainMap
            A dict containing the elements of this instance and any public facing elements from its dependencies.
        """
        return ChainMap(self.elements, *[d.elements for d in self.dependencies.values()])

    def namespace_exists_at_path(self, path: Path) -> bool:
        """
        Checks if a namespace exists relative to this namespace and a provided path.

        Parameters
        ----------
        path : Path
            The path the namespace is relative to.

        Returns
        -------
        bool
            If the namespace exists relative to this namespace and the path provided.
        """
        namespace = self.root
        for name in path:
            if name not in namespace.children:
                return False
            namespace = namespace.children[name]
        return True

    def from_path(self, path: Path) -> Namespace:
        """
        Finds a namespace starting from this namespace by following the path provided.

        Parameters
        ----------
        path : Path
            The path to follow to get to a namespace.

        Returns
        -------
        Namespace
            The namespace relative to this namespace and the path provided.

        Raises
        ------
        KeyError
            There does not exist a namespace relative to this namespace the path provided, such that
            :func:~`foundry.core.namespace.Namespace.Namespace.namespace_exists_at_path` is False.
            Thus, a namespace cannot be returned from the parameters provided.
        """
        assert self.namespace_exists_at_path(path)
        from_path = self.root
        for element in path:
            from_path = from_path.children[element]
        return from_path


def sort_topographically(graph: dict[Path, set[Path]]) -> Iterable[Path]:
    """
    From a graph of dependencies an iterable is produced to sort the vertices in topographic order, such
    that the dependencies could be loaded sequentially without any exceptions.

    Parameters
    ----------
    graph : dict[Path, set[Path]]
        The representation of the graph, where the dictionary represents the set of vertices and its
        respective neighbors.

    Returns
    -------
    Iterable[Path]
        An iterable of the paths for the respective namespaces.
    """
    return TopologicalSorter(graph).static_order()


def find_cycle(graph: dict[Path, set[Path]]) -> tuple[Path]:
    return TopologicalSorter(graph)._find_cycle()  # type: ignore


def generate_dependency_graph(name: str, v: dict, parent: Optional[Path] = None) -> dict[Path, set[Path]]:
    """
    Generates a graph where each vertex is a namespace and its neighbors are its dependencies, including
    its parent.

    Parameters
    ----------
    name: str
        The name of the root node.
    v : dict
        A dictionary structure that represents the data.
    parent : Optional[Path], optional
        The parent of the root node, by default None

    Returns
    -------
    dict[Path, set[Path]]
        The graph that represents the data supplied.
    """
    graph: dict[Path, set[Path]] = {}
    path: Path = parent.create_child(name) if parent else Path()
    dependencies: set[Path] = set() if "dependencies" not in v else {Path.from_string(d) for d in v["dependencies"]}
    if parent is not None:
        dependencies.add(parent)
    graph[path] = dependencies

    children = {} if "children" not in v else v["children"]
    for name, child in children.items():
        graph |= generate_dependency_graph(name, child, parent=path)

    return graph


def get_namespace_type(v: dict) -> type:
    """
    Determines the namespace's element's type by the type specified inside the dict.

    Parameters
    ----------
    v : dict
        The dict with the data for a namespace.

    Returns
    -------
    type
        The type that this dict's namespace should represent.

    Raises
    ------
    KeyError
        The dictionary does not contain a type for the namespace to be associated with.
    NotImplementedError
        The type supplied by the namespace is unsupported.
    """
    if "type" not in v:
        raise KeyError(f"type of namespace is not found inside {v}.")
    type_: str = v["type"]

    if NamespaceType.NONE == type_:
        return Uninitializable
    if NamespaceType.INTEGER == type_:
        return int
    if NamespaceType.STRING == type_:
        return str
    if NamespaceType.FLOAT == type_:
        return float
    if NamespaceType.FILE == type_:
        from foundry.core.file.FileGenerator import FileGenerator

        return FileGenerator
    if NamespaceType.DRAWABLE == type_:
        from foundry.core.drawable.DrawableGenerator import DrawableGeneratator

        return DrawableGeneratator
    raise NotImplementedError


def get_namespace_dict_from_path(v: dict, path: Path) -> dict:
    """
    Provides the dictionary associated with a given path that will generate a namespace.

    Parameters
    ----------
    v : dict
        The root dictionary and its children to obtain its or its children's namespace's dictionary from.
    path : Path
        The path to namespace which is valid from root.

    Returns
    -------
    dict
        The namespace's dict associated with the path provided.

    Raises
    ------
    ChildDoesNotExistException
        The child associated with the path provided does not exist inside the dictionary.
    """
    get_dependency_dict = v
    for element in path:
        try:
            get_dependency_dict = get_dependency_dict["children"][element]
        except KeyError as e:
            raise ChildDoesNotExistException(path, element) from e
    return get_dependency_dict


def validate_namespace(v: dict, parent: Optional[Namespace] = None) -> Namespace:
    """
    Handles the primary validation which is required to generate a namespace.  Specifically, its dependencies
    and it's elements are validated and loaded into the namespace.

    Parameters
    ----------
    v : dict
        The dictionary to generate the namespace from.
    parent : Optional[Namespace], optional
        The parent of this namespace, by default None

    Returns
    -------
    Namespace
        The namespace represented by this dictionary, excluding its children.

    Raises
    ------
    ChildDoesNotExistException
        If a root node contains dependencies, it will raise an exception to note this contradiction.  A root
        node may not depend on anything, by definition.

    Notes
    -----
    This method does not handle the generation of a namespace's children.  This is done intentionally because
    this namespace's children may depend on namespace's which depend on it's parent.  Thus, the parent cannot
    load its children without creating a circular importation loop.  Instead, the children must be appended
    to the namespace after its initialization to facilitate such a relationship.
    """
    type_ = get_namespace_type(v)
    namespace = Namespace(parent)

    dependencies: set[Path] = set() if "dependencies" not in v else {Path.from_string(d) for d in v["dependencies"]}
    if parent is None and dependencies:
        dependency = list(dependencies)[0]
        raise ChildDoesNotExistException(dependency, dependency.root)
    elif parent:
        namespace = evolve(namespace, dependencies={str(path): parent.from_path(path) for path in dependencies})

    elements = {}
    for key, value in ({} if "elements" not in v else v["elements"]).items():
        try:
            elements[key] = type_(value, parent=namespace)
        except TypeError:
            try:
                elements[key] = type_(value)
            except TypeError or AttributeError:
                elements[key] = type_.validate(value | {"parent": parent})  # type: ignore
    namespace = evolve(namespace, elements=elements)

    return namespace


def _evolve_child(parent: Namespace, name: str, child: Namespace) -> Namespace:
    """
    A method to recursively generate a new namespace where a new child is appended to itself.

    Parameters
    ----------
    parent : Namespace
        The parent to append a child to.
    name : str
        The name of the child to be appended.
    child : Namespace
        The child to be appended.

    Returns
    -------
    Namespace
        The root node of the parent namespace updated to reflect the parent namespace with the
        child appended.

    Notes
    -----
    Because a namespace is immutable, changing the children of a namespace would undermine the purpose
    of an immutable type after its construction.  Because a namespace cannot be initialized with its children
    due to dependency conflicts, they must be added after its construction.  To achieve this, a new root
    namespace must be generated to reflect this change in the tree structure of the namespaces.
    """
    updated_parent = evolve(parent, children=(parent.children | {name: child}))
    return _evolve_child(parent.parent, parent.name, updated_parent) if parent.parent is not None else updated_parent


def generate_namespace(v: dict) -> Namespace:
    """
    Generates the root namespace from a dictionary, creating every aspect of the namespace, including its
    children.  This also includes validation of the namespace, its children, its elements, and its children's
    elements, recursively.

    Parameters
    ----------
    v : dict
        The dictionary to generate the namespace and its children from.

    Returns
    -------
    Namespace
        The root namespace and its children derived from the dictionary provided.

    Notes
    -----
    Generating namespace is a multi-step process because a namespace's children can depend on components
    which depend on it's parent.  In other words, a child cannot be guaranteed to be able to be initialized
    at the time that it's parent is created.  Instead, the child must be appended afterwards to ensure
    that the parent namespace can accommodate all the variants that its children can take.  Because a
    namespace's dependency and parent must follow a directed acyclic graph with accordance to the namespace's
    invariant, we can sort the dependency graph of the root topographically.  This generates a sequence
    which can load the all the namespaces in an order which will not conflict with one another.  Once
    every namespace is iterated through in topographic order, the root should correctly define the
    dictionary.
    """
    order = iter(sort_topographically(dependency_graph := generate_dependency_graph("root", v)))

    try:
        next(order)  # Skip the root node, as it needs a special construction.
    except CycleError as e:
        raise CircularImportException(find_cycle(dependency_graph)) from e

    root = validate_namespace(v, None)
    for dependency_path in order:
        dependency_parent_path = dependency_path.parent
        assert dependency_parent_path is not None  # This should be impossible because it must be descendent of root.

        dependency_parent = root.from_path(dependency_parent_path)
        dependency = validate_namespace(get_namespace_dict_from_path(v, dependency_path), dependency_parent)
        root = _evolve_child(dependency_parent, dependency_path.name, dependency)  # Evolve the immutable root.

    return root
