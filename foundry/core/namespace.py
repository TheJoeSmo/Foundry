from __future__ import annotations

from collections import ChainMap
from collections.abc import Iterable, Iterator, Sequence
from enum import Enum
from graphlib import CycleError, TopologicalSorter
from re import search
from typing import Any, Generic, TypeVar

from attr import attrs, evolve, field, validators

_T = TypeVar("_T")


def _is_valid_list_of_names(inst, attr, value: tuple) -> tuple[str, ...]:
    """
    Determines if a path is a valid list of names.

    Returns
    -------
    tuple[str, ...]
        The validated list of names.

    Raises
    ------
    InvalidChildName
        One or more of the names inside of `value` is not a valid name.
    """
    for name in value:
        if not is_valid_name(name):
            raise InvalidChildName(name)
    return value


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


def is_valid_name(name: Any, *, regrex: str = "^[A-Za-z_][A-Za-z0-9_]*$") -> bool:
    """
    Determines if a name for a given child is considered valid.

    Parameters
    ----------
    name : Any
        The name to check if it is valid.
    regrex : str, optional
        The regrex expression to check for validity.

    Returns
    -------
    bool
        If the name is valid.
    """
    return bool(search(regrex, name)) if isinstance(name, str) else False


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


def generate_dependency_graph(name: str, v: dict, parent: Path | None = None) -> dict[Path, set[Path]]:
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


def validate_namespace(v: dict, parent: Namespace | None = None) -> Namespace:
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


def validate_valid_name(name: str) -> str:
    """
    Validates that the name could be referenced inside any namespace.

    Parameters
    ----------
    name : str
        The name to validate.

    Returns
    -------
    str
        The validated name.

    Raises
    ------
    ValueError
        If the name could not be referenced inside any namespace.
    """
    if not is_valid_name(name):
        raise ValueError(f"Invalid element name `{name}`")
    return name


def validate_name_is_in_namespace(name: str, parent: Namespace) -> str:
    """
    Validates that `name` exists inside `parent`.

    Parameters
    ----------
    name : str
        The name to validate.
    parent : Namespace
        The namespace to start the name from.

    Returns
    -------
    str
        The validated name.

    Raises
    ------
    ValueError
        If there does not exist an element at `name` inside `parent`.
    """
    if name not in parent:
        raise ValueError(f"'{name}' does not exist at {Path(tuple(parent.path))!s}")
    return name


def validate_element_to_type(name: str, parent: Namespace, type_: type[_T]) -> type[_T]:
    """
    Validates that the element is of `type_`.

    Parameters
    ----------
    name : str
        The name to of the element to validate.
    parent : Namespace
        The namespace to start the name from.
    type_ : Type[_T]
        The expected type of the element.

    Returns
    -------
    Type[_T]
        The type used to validate the element.

    Raises
    ------
    ValueError
        The element was not of `type_`.
    """
    obj = parent[name]
    if not isinstance(obj, type_):
        raise ValueError(
            f"Object `{obj}` at {Path(tuple(parent.path))!s}.{name} "
            + f"is not a {type_.__name__}, but a {obj.__class__.__name__}"
        )
    return type_


def validate_element(parent: Namespace, name: str, type: type[_T]) -> _T:
    """
    Validates a referenced element inside of a namespace to ensure that it exists and is of the correct
    type.

    Parameters
    ----------
    parent: Namespace
        The namespace which the element of key `name` should exist inside.
    name: str
        The index or key associated inside `parent` of the element.
    type_: Type[_T]
        The type the element should take.

    Raises
    ------
    ValueError
        If the name is not a valid name for an element.
    ValueError
        If there does not exist an element inside `parent` at `name`.
    ValueError
        If the element inside `parent` at `name` is not of `type_`.

    Returns
    -------
    _T
        The element indexed inside `parent` with a key of `name`.
    """
    validate_valid_name(name)
    validate_name_is_in_namespace(name, parent)
    validate_element_to_type(name, parent, type)
    return parent[name]


def validate_path_name(path: Any) -> str:
    """
    Validates that the path can form a :class:~`foundry.core.namespace.Path`.

    Parameters
    ----------
    path : Any
        The path to validate.

    Returns
    -------
    str
        The validated path.

    Raises
    ------
    TypeError
        If the path is not a string.
    ValueError
        If the path cannot form a :class:~`foundry.core.namespace.Path`_ as specified by
    :func:~`foundry.core.namespace.is_valid_name`.
    """
    if not isinstance(path, str):
        raise TypeError(f"Path {path} must be a {str.__name__}")
    if path:  # Allow for empty strings to denote the root node.
        for name in path.split("."):
            if not is_valid_name(name):
                raise ValueError(f"Invalid path name '{name}' from `{path}`")
    return path


class NamespaceValidationException(Exception):
    """
    An exception that is raised during the validation of a namespace.
    """

    __slots__ = ()


class CircularImportException(NamespaceValidationException):
    """
    This exception is raised during the importation of dependencies if a cycle exists.  A cycle makes it
    so none of the :class:~`foundry.core.namespace.Namespace`_ inside the cycle could be fully
    initialized without violating the invariant of the namespace.  Thus, the namespaces cannot
    be initialized and this exception must be raised.

    Attributes
    ----------
    cycle: Optional[tuple[Path]]
        The cycle that was detected.
    """

    __slots__ = ("cycle",)

    cycle: tuple[Path] | None

    def __init__(self, cycle: tuple[Path] | None = None):
        self.cycle = cycle
        if self.cycle is not None:
            super().__init__(f"Cannot import because {[str(c) for c in self.cycle]} forms a cycle.")
        else:
            super().__init__("A cycle exists.")


class ParentDoesNotExistException(NamespaceValidationException):
    """
    A method is called where the :class:~`foundry.core.namespace.Namespace`_ did not have parent
    where a parent was required.

    Attributes
    ----------
    child: Optional[Namespace]
        The child without a parent.
    """

    __slots__ = ("child",)

    child: Namespace | None

    def __init__(self, child: Namespace | None = None):
        self.child = child
        if self.child is not None:
            super().__init__(f"{child} does not have a parent.")
        else:
            super().__init__("No parent exists.")


class ChildDoesNotExistException(NamespaceValidationException):
    """
    A method is called where the :class:~`foundry.core.namespace.Namespace.Namespace`_ did not have child
    when a child was required.

    Attributes
    ----------
    parent: Optional[Namespace]
        The parent that did not contain
    path: Path
    unfound_child: str
    """

    __slots__ = "parent", "path", "unfound_child"

    parent: Namespace | None
    path: Path
    unfound_child: str

    def __init__(self, path: Path, unfound_child: str, parent: Namespace | None = None):
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


class InvalidChildName(ValueError):
    """
    An exception raised when a child's name inside :class:~`foundry.core.namespace.util.ChildTreeProtocol`_
    is considered to be invalid.

    Attributes
    ----------
    name: str
        The invalid string in its entirety.
    invalid_element: str
        The invalid portion of the string.  By definition this must be a subset of name.
    """

    __slots__ = "name", "invalid_element"

    name: str
    invalid_element: str | None

    def __init__(self, name: str, invalid_element: str | None = None):
        self.name = name
        self.invalid_element = invalid_element
        if invalid_element is not None:
            super().__init__(f'The name "{name}" contained an invalid element: {invalid_element}.')
        else:
            super().__init__(f'The name "{name}" contained an invalid element.')


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True, eq=True)
class Path:
    """
    A representation of a path that be taken through a tree structure to get to a given element.

    Attributes
    ----------
    decomposed_path: tuple[str, ...] = (,)
        A series of strings that represent a series of keys that can be taken to traverse a tree structure.

    Raises
    ------
    InvalidChildName
        If any of the children name are returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
    """

    decomposed_path: tuple[str, ...] = field(
        factory=tuple, validator=[validators.instance_of(tuple), _is_valid_list_of_names]
    )

    def __str__(self) -> str:
        return ".".join(self.decomposed_path)

    def __iter__(self) -> Iterator[str]:
        return iter(self.decomposed_path)

    def __getitem__(self, key: int | slice):
        return self.decomposed_path.__getitem__(key)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @property
    def root(self) -> str:
        """
        Provides the root of the element referenced.

        Returns
        -------
        str
            The root of the element referenced.
        """
        return "" if len(self.decomposed_path) == 0 else self.decomposed_path[0]

    @property
    def parent(self) -> Path | None:
        """
        Provides the parent Path of this path, if one exists.

        Returns
        -------
        Optional[Path]
            The parent path of this path if one exists, else None.
        """
        return None if len(self.decomposed_path) == 0 else Path(self.decomposed_path[:-1])

    @property
    def name(self) -> str:
        """
        Provides the name of the element referenced.

        Returns
        -------
        str
            The name of the element referenced.
        """
        return "" if len(self.decomposed_path) == 0 else self.decomposed_path[-1]

    def create_child(self, name: str) -> Path:
        """
        Creates a child element with this instance as the parent and name as a child of parent.

        Parameters
        ----------
        name : str
            A child of this path to create a new instance from.

        Returns
        -------
        Path
            A path that represents a child of this parent with the name as the top element.

        Raises
        ------
        InvalidChildName
            If name is returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
        """
        return self.__class__(tuple(list(self.decomposed_path) + [name]))

    @classmethod
    def create_child_from_parent(cls, parent: Path | None, child: str) -> Path:
        """
        Create a child of the same instance of this from parent, if it exists, and a child.  If no child exists, then
        the child will be created as root.

        Parameters
        ----------
        parent : Optional[Path]
            A parent that may exist to create a child from.
        child : str
            The name of the top most name to exist inside the path.

        Returns
        -------
        Self
            A path that represents a child of the parent, if it exists, otherwise root.

        Raises
        ------
        InvalidChildName
            If name is returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
        """
        return cls((child,)) if parent is None else parent.create_child(child)

    @classmethod
    def from_string(cls, s: str) -> Path:
        """
        Creates a path from a string.

        Parameters
        ----------
        s : str
            The string to convert to a path.

        Returns
        -------
        Self
            A path that represents a path.

        Raises
        ------
        InvalidChildName
            If any of the children name are returned as invalid for :func:`foundry.core.namespace.is_valid_name`.
        """
        return cls(tuple(s.split("."))) if s else cls()

    @classmethod
    def validate_path_from_parent(cls, parent: Namespace, s: str) -> Path:
        """
        Adds an additional validation that the path derived from `s` exists
        relative to `parent`.

        Parameters
        ----------
        parent : Namespace
            The parent to derive the path from.
        s : str
            The path to be derived.

        Returns
        -------
        Path
            The path derived from `s` and `parent`.

        Raises
        ------
        ValueError
            The path `s` does not exist relative to `parent`.
        """
        if not parent.namespace_exists_at_path(path := cls.from_string(s)):
            raise ValueError(f"'{path!s}' does not exist in {parent!s}")
        return path

    @classmethod
    def validate(cls, *_, path: str, use_parent: bool = True, parent: Namespace | None = None) -> Path:
        """
        Validates that the provided object is a valid Path.

        Parameters
        ----------
        path : str
            The path to be validated.
        use_parent : bool, optional
            If the path must exist relative to `parent`, by default True
        parent : Namespace | None, optional
            The namespace to validate the path from, by default None

        Returns
        -------
        Path
            Generates a validated path from `s`.

        Raises
        ------
        ValueError
            If `use_parent` and there does `parent` is None.
        TypeError
            If `parent` is not None or a Namespace.
        """

        path = validate_path_name(path)
        if use_parent and parent is None:
            raise ValueError("Parent does not exist")
        if not use_parent:
            return cls.from_string(path)
        if not isinstance(parent, Namespace):
            raise TypeError(f"Parent {parent} must be {Namespace.__name__}")
        return cls.validate_path_from_parent(parent, path)


class NamespaceType(str, Enum):
    """
    The type of elements allowed inside the namespace.
    """

    NONE = "NONE"
    INTEGER = "INTEGER"
    STRING = "STRING"
    FLOAT = "FLOAT"
    FILE = "FILE"
    DRAWABLE = "DRAWABLE"

    @classmethod
    def has_value(cls, value: str) -> bool:
        """
        A convenience method to quickly determine if a value is a valid enumeration.

        Parameters
        ----------
        value : str
            The value to check against the enumeration.

        Returns
        -------
        bool
            If the value is inside the enumeration.
        """
        return value in cls._value2member_map_


class Uninitializable:
    """
    A class that will always throw an exception on initialization.  Used to enforce no elements for a given
    namespace.
    """

    def __init__(self, parent, *args, **kwargs):
        raise ValueError(f"{parent!s} contains no elements")


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True, cache_hash=True, cmp=False, repr=False)
class Namespace(Generic[_T]):
    parent: Namespace | None = field(eq=False, default=None)
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
            :func:~`foundry.core.namespace.Namespace.namespace_exists_at_path`_ is False.
            Thus, a namespace cannot be returned from the parameters provided.
        """
        assert self.namespace_exists_at_path(path)
        from_path = self.root
        for element in path:
            from_path = from_path.children[element]
        return from_path
