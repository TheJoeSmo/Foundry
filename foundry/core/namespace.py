from __future__ import annotations

from collections import ChainMap
from collections.abc import Iterable, Iterator, Mapping, Sequence
from enum import Enum
from graphlib import CycleError, TopologicalSorter
from re import search
from typing import Any, Callable, Generic, Iterator, Sequence, Type, TypeVar

from attr import Factory, attrs, evolve, field, validators

from foundry.core import ChainMap, ChainMapView

_T = TypeVar("_T")
_NV = TypeVar("_NV", bound="NamespaceValidator")
_CNV = TypeVar("_CNV", bound="ConcreteNamespaceValidator")
_NTH = TypeVar("_NTH", bound="NamespaceTypeHandler")
_NTHM = TypeVar("_NTHM", bound="NamespaceTypeHandlerManager")
_PV = TypeVar("_PV", bound="_PrimitiveValidator")
_Validator = Callable[[Type[_T], Mapping], _T]
ValidatorMapping = Mapping[str, _Validator | "Validator"]
ValidatorHandlerMapping = Mapping[str, "NamespaceTypeHandler"]


DEFAULT_ARGUMENT = "__DEFAULT_ARGUMENT__"
TYPE_ARGUMENT = "__TYPE_ARGUMENT__"
VALID_TYPE_ARGUMENTS = (TYPE_ARGUMENT, "TYPE", "type")


def _get_type_argument(v: Mapping) -> str | None:
    """
    Determines the type of the object.  A few options are used, but it is advised to only
    use a single one, as the process to select the type should be assumed to be random.

    Parameters
    ----------
    v : Mapping
        A map of values to determine the type from.

    Returns
    -------
    str | None
        The type if found otherwise None.
    """
    for valid_argument in VALID_TYPE_ARGUMENTS:
        if valid_argument in v:
            return v[valid_argument]
    return None


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


def _validate_from_namespace(cls: Type[_T], parent: Namespace, name: str, path: str) -> _T:
    """
    Generates and validates from another existing object from `parent`.

    Parameters
    ----------
    cls: Type[_T]
        The type to find inside the namespace.
    parent : Namespace
        The namespace with the object to copy.
    name : str
        The name of the object.
    path : str
        The path to the object Namespace.

    Returns
    -------
    _T
        The object inside the Namespace.
    """
    return validate_element(parent=parent.from_path(Path.validate(parent=parent, path=path)), name=name, type=cls)


def convert_to_validator(value: _Validator | Validator) -> Validator:
    """
    Converts a callable to a validator if required.

    Parameters
    ----------
    value : _Validator | Validator
        The callable or validator to form the validator with.

    Returns
    -------
    Validator
        The validator that represents the callable provided.
    """
    return value if isinstance(value, Validator) else Validator(value)


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


def sort_topographically(graph: Mapping[Path, set[Path]]) -> Iterable[Path]:
    """
    From a graph of dependencies an iterable is produced to sort the vertices in topographic order, such
    that the dependencies could be loaded sequentially without any exceptions.

    Parameters
    ----------
    graph : Mapping[Path, set[Path]]
        The representation of the graph, where the mapping represents the set of vertices and its
        respective neighbors.

    Returns
    -------
    Iterable[Path]
        An iterable of the paths for the respective namespaces.
    """
    return TopologicalSorter(graph).static_order()


def find_cycle(graph: Mapping[Path, set[Path]]) -> tuple[Path]:
    return TopologicalSorter(graph)._find_cycle()  # type: ignore


def generate_dependency_graph(name: str, v: Mapping, parent: Path | None = None) -> Mapping[Path, set[Path]]:
    """
    Generates a graph where each vertex is a namespace and its neighbors are its dependencies, including
    its parent.

    Parameters
    ----------
    name: str
        The name of the root node.
    v : Mapping
        A map structure that represents the data.
    parent : Optional[Path], optional
        The parent of the root node, by default None

    Returns
    -------
    Mapping[Path, set[Path]]
        The graph that represents the data supplied.
    """
    graph: Mapping[Path, set[Path]] = {}
    path: Path = parent.create_child(name) if parent else Path()
    dependencies: set[Path] = set() if "dependencies" not in v else {Path.from_string(d) for d in v["dependencies"]}
    if parent is not None:
        dependencies.add(parent)
    graph[path] = dependencies

    children = {} if "children" not in v else v["children"]
    for name, child in children.items():
        graph |= generate_dependency_graph(name, child, parent=path)

    return graph


def validate_namespace_type(validators: NamespaceTypeHandlerManager, v: Mapping) -> str:
    """
    Validates that a namespace's type is a valid type.

    Parameters
    ----------
    validators : NamespaceTypeHandlerManager
        The specific validators and associated types that the namespace can possess.
    v : Mapping
        The mapping with the data for a namespace.

    Returns
    -------
    str
        The validated type string.

    Raises
    ------
    KeyError
        There does not exist type inside `v`.
    TypeError
        `type` is not present inside `validators`.
    ValueError
        The `type` is present inside `validators` but the validation type was not defined
        properly, so the namespace could not determine which type to validate the type to.
    """
    type_ = _get_type_argument(v)
    if type_ is None:
        raise KeyError(f"type of namespace is not found inside {v}.")
    if type_ not in validators.types.keys():
        raise TypeError(f"{type_} is not supported, only {validators.types.keys()}.")
    if validators.types[type_].get_type_suggestion(type_) is None:
        raise ValueError(f"Could not determine how to validate {type_} from {validators.types[type_]}")
    return type_


def get_namespace_dict_from_path(v: Mapping, path: Path) -> Mapping:
    """
    Provides the mapping associated with a given path that will generate a namespace.

    Parameters
    ----------
    v : Mapping
        The root map and its children to obtain its or its children's namespace's map from.
    path : Path
        The path to namespace which is valid from root.

    Returns
    -------
    Mapping
        The namespace's map associated with the path provided.

    Raises
    ------
    ChildDoesNotExistException
        The child associated with the path provided does not exist inside the map.
    """
    get_dependency_dict = v
    for element in path:
        try:
            get_dependency_dict = get_dependency_dict["children"][element]
        except KeyError as e:
            raise ChildDoesNotExistException(path, element) from e
    return get_dependency_dict


def validate_namespace(
    v: Mapping, parent: Namespace | None = None, validators: NamespaceTypeHandlerManager | None = None
) -> Namespace:
    """
    Handles the primary validation which is required to generate a namespace.  Specifically, its dependencies
    and it's elements are validated and loaded into the namespace.

    Parameters
    ----------
    v : Mapping
        The mapping to generate the namespace from.
    parent : Optional[Namespace], optional
        The parent of this namespace, by default makes the namespace the root.
    type_handler: NamespaceTypeHandlerManager | None, optional
        The type manager to validate and generate new namespaces from, by default the parent's handler if
        a parent is provided, otherwise the default handler will be used.

    Returns
    -------
    Namespace
        The namespace represented by this map, excluding its children.

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
    namespace = Namespace(parent) if validators is None else Namespace(parent, validators=validators)
    element_type = validate_namespace_type(namespace.validators, v)
    validator = namespace.validators.types[element_type]

    dependencies: set[Path] = set() if "dependencies" not in v else {Path.from_string(d) for d in v["dependencies"]}
    if parent is None and dependencies:
        dependency = list(dependencies)[0]
        raise ChildDoesNotExistException(dependency, dependency.root)
    elif parent:
        namespace = evolve(namespace, dependencies={str(path): parent.from_path(path) for path in dependencies})

    elements = {}
    for key, value in ({} if "elements" not in v else v["elements"]).items():
        elements[key] = validator.validate_by_type(element_type, value, namespace)
    namespace = evolve(namespace, elements=elements)

    return namespace


def generate_namespace(v: Mapping) -> Namespace:
    """
    Generates the root namespace from a mapping, creating every aspect of the namespace, including its
    children.  This also includes validation of the namespace, its children, its elements, and its children's
    elements, recursively.

    Parameters
    ----------
    v : Mapping
        The mapping to generate the namespace and its children from.

    Returns
    -------
    Namespace
        The root namespace and its children derived from the map provided.

    Notes
    -----
    Generating namespace is a multi-step process because a namespace's children can depend on components
    which depend on it's parent.  In other words, a child cannot be guaranteed to be able to be initialized
    at the time that it's parent is created.  Instead, the child must be appended afterwards to ensure
    that the parent namespace can accommodate all the variants that its children can take.  Because a
    namespace's dependency and parent must follow a directed acyclic graph with accordance to the namespace's
    invariant, we can sort the dependency graph of the root topographically.  This generates a sequence
    which can load the all the namespaces in an order which will not conflict with one another.  Once
    every namespace is iterated through in topographic order, the root should correctly define the map.
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


def validate_from_namespace(cls: Type[_T], v: Mapping) -> _T:
    """
    Generates and validates from another existing object inside a namespace.

    Parameters
    ----------
    cls : Type[_T]
        The type to find inside the namespace.
    v : Mapping
        A map containing a parent, name, and path.

    Returns
    -------
    _T
        The object inside the Namespace.

    Raises
    ------
    KeyError
        There does not exist a parent inside `v`
    TypeError
        The parent is not a Namespace.
    KeyError
        There does not exist a name inside `v`
    TypeError
        The name is not a string.
    KeyError
        There does not exist a path inside `v`
    TypeError
        The path is not a string.
    """
    if "parent" not in v:
        raise KeyError(f"Parent namespace was not defined inside {v} to generate {cls.__name__} from namespace")
    if not isinstance((parent := v["parent"]), Namespace):
        raise TypeError(f"{parent} is not {Namespace.__name__}")
    if "name" not in v:
        raise KeyError(f"Name is not inside {v} to generate {cls.__name__} from namespace")
    if not isinstance((name := v["name"]), str):
        raise TypeError(f"{name} is not {str.__name__}")
    if "path" not in v:
        raise KeyError(f"Path is not inside {v} to generate {cls.__name__} from namespace")
    if not isinstance((path := v["path"]), str):
        raise TypeError(f"{path} is not {str.__name__}")
    return _validate_from_namespace(cls, parent, name, path)


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


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Validator(Generic[_T]):
    validator: _Validator
    type_suggestion: Type[_T] | None = None
    use_parent: bool = True


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class NamespaceTypeHandler(Generic[_T]):
    """
    A model for representing the possible types a namespace element can possess and their
    respective validator methods.

    Attributes
    ----------
    types: ValidatorMapping
        A map containing the types and their respective validator methods.  This can come in
        two variants.  It can either be a simple callable or be defined as a Validator.
        If a callable is provided, it will automatically be converted to a Validator with
        default parameters for any Validator specific methods.  For more specification a
        Validator should be used instead.
    default_type_suggestion: Type[_T] | None, optional
        The suggested type to generate the handler as.  If not provided, no assumption should
        be made.

    Parameters
    ----------
    Generic : _T
        The type to be validated to.
    """

    types: ValidatorMapping = field(default=dict)
    default_type_suggestion: Type[_T] | None = None

    def overwrite_from_parent(self: _NTH, other: NamespaceTypeHandler) -> _NTH:
        """
        `other` overwrites or adds additional type validators from this handler
        to form a new handler.

        Parameters
        ----------
        other : NamespaceTypeHandler
            The handler to override values from this handler.

        Returns
        -------
        Self
            The extended parent.
        """
        return type(self)(
            ChainMap(other.types, self.types),
            default_type_suggestion=self.default_type_suggestion
            if other.default_type_suggestion is None
            else other.default_type_suggestion,
        )

    def validate_by_type(self, type: str, values: Mapping, parent: Namespace) -> _T:
        """
        Generates and validates `values` of `type` to generate an object from `parent`.

        Parameters
        ----------
        type : str
            The type of object to generate and validate.
        values : Mapping
            The attributes of the object.
        parent : Namespace
            The parent namespace of the object.

        Returns
        -------
        _T
            The generated and validated object.
        """
        validator = parent.validators.types[type]
        if validator.get_if_validator_uses_parent(type):
            return validator.get_validator(type)(validator.get_type_suggestion(type), values | {"parent": parent})
        return validator.get_validator(type)(validator.get_type_suggestion(type), values)

    def get_type_suggestion(self, type: str) -> Type[_T] | None:
        """
        Provides the type that `type` requires as the first argument for its validator.

        Parameters
        ----------
        type : str
            The key to a type and its associated validator.

        Returns
        -------
        Type[_T] | None
            Provides the type if one is provided, otherwise defaults on `default_type_suggestion`.
        """
        return (
            suggestion
            if (suggestion := convert_to_validator(self.types[type]).type_suggestion) is not None
            else self.default_type_suggestion
        )

    def get_validator(self, type: str) -> _Validator:
        """
        Gets a validator to generate a specific object from a map.

        Parameters
        ----------
        type : str
            The type to validate to.

        Returns
        -------
        _Validator
            The validator associated with `type`.
        """
        return convert_to_validator(self.types[type]).validator

    def get_if_validator_uses_parent(self, type: str) -> bool:
        """
        Gets if a validator should request the parent namespace to be inside the map which is passed to
        it for its initialization.

        Parameters
        ----------
        type : str
            The type to validate.

        Returns
        -------
        bool
            If the parent is used by the validator.
        """
        return convert_to_validator(self.types[type]).use_parent

    def has_type(self, type: str) -> bool:
        """
        A convenience method to quickly determine if a 'type' is valid.

        Parameters
        ----------
        type : str
            The type to check if it is registered.

        Returns
        -------
        bool
            If the type is registered.
        """
        return type in self.types


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class NamespaceTypeHandlerManager:
    """
    Manages which type is associated to which handler.  This primarily serves as a series of
    convenience methods to manage a map to ensure consistent validation.

    Attributes
    ----------
    types: ValidatorHandlerMapping
        A series of types and their associated validator handler.
    """

    types: ValidatorHandlerMapping

    @classmethod
    def from_managers(cls, *managers: NamespaceTypeHandlerManager):
        """
        Effectively merges a series of managers together into a single manager.

        Parameters
        ----------
        *managers: NamespaceTypeHandlerManager
            A series of managers to merge together.
        """
        manager = cls(ChainMap())
        for m in managers:
            for type_, handler in m.types.items():
                manager.add_type_handler(type_, handler)
        return manager

    def override_type_handler(self: _NTHM, type_: str, handler: NamespaceTypeHandler) -> _NTHM:
        """
        Generates a new manager which removes the current handler of `type_` if it exists
        and replaces it with `handler`.

        Parameters
        ----------
        type_ : str
            The type to override.
        handler : NamespaceTypeHandler
            The handler to validate the type with.

        Returns
        -------
        Self
            The generated manager with the mutation or addition to `type_`.
        """
        if isinstance(self.types, ChainMap):
            return self.__class__(ChainMap({type_: handler}, *self.types.maps))  # No need to make a new ChainMap.
        return self.__class__(ChainMap({type_: handler}, self.types))

    def add_type_handler(self: _NTHM, type_: str, handler: NamespaceTypeHandler) -> _NTHM:
        """
        Generates a new manager which adds a handler to validate `type_`.  If `type_`
        is already defined a new handler will be used which overrides this instance's
        handler for `type_`, such that `handler`'s validators will be used instead.

        Parameters
        ----------
        type_ : str
            The type to add validators to.
        handler : NamespaceTypeHandler
            The handler to validate the type with.

        Returns
        -------
        Self
             The generated manager with the mutation or addition to `type_`.
        """
        if type_ not in self.types:
            return self.override_type_handler(type_, handler)  # Overrides nothing, as it is not there.
        return self.__class__(ChainMap({type_: self.types[type_].overwrite_from_parent(handler)}, self.types))

    def from_select_types(self: _NTHM, *types: str) -> _NTHM:
        """
        Generates a new manager which ensures only `types` can be validated.

        Parameters
        ----------
        *types: str
            The types that can be validated.

        Returns
        -------
        Self
            This manager, but with a limit to only validate `types`.
        """
        if isinstance(self.types, ChainMap) or isinstance(self.types, ChainMapView):
            return self.__class__(ChainMapView(self.types, set(*types)))  # No need to make a new ChainMap.
        return self.__class__(ChainMapView(ChainMap(self.types), set(*types)))


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True, cache_hash=True, cmp=False, repr=False)
class Namespace(Generic[_T]):
    parent: Namespace | None = field(eq=False, default=None)
    dependencies: Mapping[str, Namespace] = field(factory=dict)
    elements: Mapping[str, _T] = field(factory=dict)
    children: Mapping[str, Namespace] = field(factory=dict)
    validators: NamespaceTypeHandlerManager = field(
        eq=False,
        default=Factory(
            lambda self: NamespaceTypeHandlerManager({})
            if self.parent is None
            else self.parent.validators,  # type: ignore
            takes_self=True,  # type: ignore
        ),
    )

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
            s = f"{s}children={self.children}, "
        if self.validators:
            s = f"{s}validators={self.validators}, "
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
        The entire map of elements that can be accessed via the mapping interface.

        Returns
        -------
        ChainMap
            A map containing the elements of this instance and any public facing elements from its dependencies.
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


class NamespaceValidator:
    """
    A namespace element validator, which seeks to encourage extension and modularity for
    namespace validators.

    Attributes
    ----------
    __validator_handler__: NamespaceTypeHandler
        The handler for validators to automatically validate and generate the objects from a namespace,
        also incorporates the parent's attribute, if it exists.
    __type_default__: str | None
        The type default.  If None, then the type must be provided.
    __names__: tuple[str, ...]
        The names to associate this type with.
    """

    __validator_handler__: NamespaceTypeHandler = NamespaceTypeHandler({"FROM NAMESPACE": validate_from_namespace})
    __type_default__: str | None = None
    __names__: tuple[str, ...] = ("NONE", "none")
    __slots__ = ()

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    @property
    def type_handler(cls: Type[_NV]) -> NamespaceTypeHandler[_NV]:
        """
        Provides the type handler for this type.

        Returns
        -------
        NamespaceTypeHandler[_NV]
            The handler for to validate this type.
        """
        return NamespaceTypeHandler(
            ChainMap(
                cls.__validator_handler__.types,
                *[getattr(b, "type_handler").types for b in cls.__bases__ if hasattr(b, "type_handler")],
            )
        )

    @classmethod
    @property
    def type_manager(cls) -> NamespaceTypeHandlerManager:
        """
        Provides the type manager for this type and all of its associated names.

        Returns
        -------
        NamespaceTypeHandlerManager
            The manager to find the proper validations for this type.
        """
        return NamespaceTypeHandlerManager({name: cls.type_handler for name in cls.__names__})

    @classmethod
    def get_type_suggestion(cls, v: Mapping) -> str:
        """
        A convenience method to access the string type of the object after it has been validated by
        `validate_type`.

        Parameters
        ----------
        v : Mapping
            A mapping containing the information to generate the object.

        Returns
        -------
        str
            The type of the object.
        """
        return v[TYPE_ARGUMENT]

    @classmethod
    def get_default_argument(cls, v: Mapping) -> Any:
        """
        A convenience method to access the default argument for a type which only accepts a single
        argument.

        Parameters
        ----------
        v : Mapping
            A mapping containing the information to generate the object.

        Returns
        -------
        Any
            The default argument

        Raises
        ------
        TypeError
            Both the type and default argument is not present.
        TypeError
            Too many arguments were provided to deduce the default argument.
        TypeError
            No argument were provided other than the type.
        """
        if DEFAULT_ARGUMENT not in v and TYPE_ARGUMENT not in v:
            raise TypeError(f"{cls.__name__} with arguments {v} is malformed")
        elif DEFAULT_ARGUMENT not in v and len(v) > 2:
            raise TypeError(f"{cls.__name__} of {cls.get_type_suggestion(v)} only accepts a single value, not {v}")
        elif DEFAULT_ARGUMENT not in v:
            raise TypeError(f"{cls.__name__} of {cls.get_type_suggestion(v)} must be provided a value, not {v}")
        return v[DEFAULT_ARGUMENT]

    @classmethod
    def validate_by_type(cls: Type[_NV], v: Mapping) -> _NV:
        """
        Generates and validates an object by its type defined in `__validator_handler__`.

        Parameters
        ----------
        cls : Type[_NV]
            The type of object to generate.
        v : Mapping
            A mapping containing the information to generate the object.

        Returns
        -------
        _NV
            The object generated from `v` specified by its type.
        """
        type_ = _get_type_argument(v)
        if type_ is None:
            raise KeyError(f"Cannot find type of {v}")
        return cls.type_handler.get_validator(type_)(cls, v)

    @classmethod
    def validate_type(cls: Type[_NV], v: Any) -> _NV:
        """
        Generates and validates an object by its types and ensures that there is a type
        inside `v` such that it can be validated further.

        Parameters
        ----------
        cls : Type[_NV]
            The type of object to generate.
        v : Any
            A map containing the information to generate the object.

        Returns
        -------
        _NV
            The object generated from `v` specified by its type.

        Raises
        ------
        TypeError
            `v` was not passed as a map.
        TypeError
            There does not exist `type` inside `v` and `__type_default__` is None.
        TypeError
            `type` is not a valid type.
        """
        if not isinstance(v, dict):
            if cls.__type_default__ is None:
                raise TypeError(f"{v} is not a {dict.__name__}")
            v = {DEFAULT_ARGUMENT: v}
        type_ = _get_type_argument(v)
        if type_ is None:
            if cls.__type_default__ is None:
                raise TypeError(f"{v} does not define a type for {cls.__name__}")
            type_ = cls.__type_default__
        elif not cls.type_handler.has_type(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid type")
        v[TYPE_ARGUMENT] = type_  # Enforce that TYPE_ARGUMENT will always work for subclass validators.
        return cls.validate_by_type(v)


class ConcreteNamespaceValidator(NamespaceValidator):
    """
    Automatically provides this class as the type suggestion for the handler.  This is so the namespace
    generation functions can actually call this instance with the correct type.
    """

    @classmethod
    @property
    def type_handler(cls: Type[_CNV]) -> NamespaceTypeHandler[_CNV]:
        handler = super().type_handler
        return evolve(handler, default_type_suggestion=cls)  # type: ignore


NoneValidator = ConcreteNamespaceValidator


class _PrimitiveValidator(ConcreteNamespaceValidator):
    __type_default__ = "DEFAULT"

    def __init__(self, value: Any):
        raise NotImplementedError()

    @classmethod
    def _validate_primitive(cls: Type[_PV], v: Mapping) -> _PV:
        return cls(cls.get_default_argument(v))

    __validator_handler__ = NamespaceTypeHandler({"DEFAULT": Validator(_validate_primitive, use_parent=False)})


class IntegerValidator(int, _PrimitiveValidator):
    pass


IntegerValidator.__validator_handler__ = NamespaceTypeHandler(default_type_suggestion=IntegerValidator)


class FloatValidator(float, _PrimitiveValidator):
    pass


FloatValidator.__validator_handler__ = NamespaceTypeHandler(default_type_suggestion=FloatValidator)


class StringValidator(str, _PrimitiveValidator):
    pass


StringValidator.__validator_handler__ = NamespaceTypeHandler(default_type_suggestion=StringValidator)


primitive_manager = NamespaceTypeHandlerManager.from_managers(
    IntegerValidator.type_manager, FloatValidator.type_manager, StringValidator.type_manager
)
