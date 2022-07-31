from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from graphlib import CycleError, TopologicalSorter
from re import search
from typing import Any, Generic, Literal, TypeVar

from attr import Factory, attrs, evolve, field, validators

from foundry.core import ChainMap, ChainMapView

"""
Declare constant literals.
"""

DEFAULT_ARGUMENT: Literal["__DEFAULT_ARGUMENT__"] = "__DEFAULT_ARGUMENT__"
"""
When a validator only desires a single argument, it will be passed as through this.
"""

TYPE_ARGUMENT: Literal["__TYPE_ARGUMENT__"] = "__TYPE_ARGUMENT__"
"""
The type the validator that should be used to create and object.
"""

PARENT_ARGUMENT: Literal["__PARENT__"] = "__PARENT__"
"""
The parent namespace that is passed to create an object relating to its namespace.
"""

META_TYPE_ARGUMENTS: Literal["__TYPE_ARGUMENTS__"] = "__TYPE_ARGUMENTS__"
"""
The key inside a dictionary for determining extra arguments for a type.
"""

META_TYPE_KEYWORD_ARGUMENTS: Literal["__TYPE_KEYWORD_ARGUMENTS__"] = "__TYPE_KEYWORD_ARGUMENTS__"
"""
The key inside a dictionary for determining extra keyword arguments for a type.
"""

VALID_TYPE_ARGUMENTS = (TYPE_ARGUMENT, "TYPE", "type")
"""
The valid ways a user can define the type attribute.
"""

VALID_META_TYPE_ARGUMENTS = (META_TYPE_ARGUMENTS, "args", "ARGS", "arguments", "ARGUMENTS")
"""
The valid ways a user can define the type meta-arguments.
"""

VALID_META_TYPE_KEYWORD_ARGUMENTS = (
    META_TYPE_KEYWORD_ARGUMENTS,
    "kwargs",
    "KWARGS",
    "keyword arguments",
    "KEYWORD ARGUMENTS",
)
"""
The valid ways a user can define the type meta-keyword-arguments.
"""

"""
Declare private type hints.
"""

_T = TypeVar("_T")
_V = TypeVar("_V", bound="Validator")
_CV = TypeVar("_CV", bound="ConcreteValidator")
_TV = TypeVar("_TV", bound="TypeValidator")
_PV = TypeVar("_PV", bound="PrimitiveValidator")
_NTH = TypeVar("_NTH", bound="_TypeHandler")
_NTHM = TypeVar("_NTHM", bound="_TypeHandlerManager")


_MetaValidator = Callable[[type[_T], Mapping], _T]
"""
Validates a type `_T` into an object `_T` by accepting a map of values.
"""

_MetaComplexValidator = Callable[[type[_T], Mapping, Sequence], _MetaValidator[_T]]
"""
Validates a type, `_T` into an object by accepting a map of values and a sequence and map of preset conditions
required for a complex type validator.
"""

"""
Declare common data class structures for common use.
"""


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
class _MetaType(Generic[_T]):
    """
    A generic interface to represent a complex type.

    Parameters
    ----------
    type_suggestion: str
        The name of the type to be identified.
    arguments: tuple[Any, ...], default ()
        The required arguments to pass to the type validator.
    keyword_arguments: Mapping[str, Any], default {}
        The required keyword arguments to pass to the type validator.
    parent: Namespace | None = None
        The parent of the type, if provided.
    """

    type_suggestion: str
    arguments: tuple[Any, ...] = field(default=Factory(tuple))  # type: ignore
    keyword_arguments: Mapping[str, Any] = field(default=Factory(dict))  # type: ignore
    parent: Namespace | None = None


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
class MetaValidator(Generic[_T]):
    """
    A generic interface to validate an type into an object.

    Attributes
    ----------
    validator: _MetaValidator
        The callable to convert the type into an object.
    type_suggestion: Type[_T] | None = None
        The suggested type to convert.
    use_parent: bool = True
        If the type requires a parent namespace to become an object.
    """

    validator: _MetaValidator
    type_suggestion: type[_T] | None = None
    use_parent: bool = True

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}(validator={self.validator}, "
        if self.type_suggestion is not None:
            s = f"{s}type_suggestion={self.type_suggestion}, "
        if not self.use_parent:
            s = f"{s}use_parent={self.use_parent}, "
        if s[-1] == " ":
            s = s[:-2]
        return f"{s})"


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
class ComplexMetaValidator(Generic[_T]):
    """
    A generic interface to decompose a complex validator into a normal validator.

    Attributes
    ----------
    validator: _MetaComplexValidator
        The callable to decompose the type into a validator.
    arguments: tuple[Any, ...] = ()
        A series of validators to generate the arguments for the complex validator.
    keywords_arguments: Mapping[str, Any] = {}
        A series of keyword validators to generate the keyword arguments for the complex validator.
    restrict_arguments: bool = True
        If the validator should limit type meta-arguments.
    restrict_keywords: bool = True
        If the validator should limit type meta-keyword-arguments.
    """

    validator: _MetaComplexValidator
    arguments: tuple[Any, ...] = field(default=Factory(tuple))  # type: ignore
    keywords_arguments: Mapping[str, Any] = field(default=Factory(dict))  # type: ignore
    restrict_arguments: bool = True
    restrict_keywords: bool = True

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}(validator={self.validator}, "
        if not self.arguments:
            s = f"{s}arguments={self.arguments}, "
        if not self.keywords_arguments:
            s = f"{s}keyword={self.keywords_arguments}, "
        if not self.restrict_arguments:
            s = f"{s}restrict_arguments={self.restrict_arguments}, "
        if not self.restrict_keywords:
            s = f"{s}restrict_keywords={self.restrict_keywords}, "
        if s[-1] == " ":
            s = s[:-2]
        return f"{s})"

    def decompose(self, *args, **kwargs) -> _MetaValidator:
        """
        Decomposes the complex validator into a normal validator.

        Returns
        -------
        _MetaValidator
            The decomposed validator.

        Notes
        -----
        This method does not supply any validation of the arguments passed.
        """
        return self.validator(*args, **kwargs)


ValidatorMapping = Mapping[str, _MetaValidator | MetaValidator | ComplexMetaValidator]
"""
A map which contains a series of strings, which define creatable types such as the default, from
namespace, etc.; and their respective validators such that types could be validated in multiple ways.
"""


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _TypeHandler(Generic[_T]):
    """
    A model for representing the possible types a namespace element can possess and their
    respective validator methods.

    Attributes
    ----------
    types: ValidatorMapping
        A map containing the types and their respective validator methods.  This can come in
        two variants.  It can either be a simple callable or be defined as a MetaValidator.
        If a callable is provided, it will automatically be converted to a MetaValidator with
        default parameters for any MetaValidator specific methods.  For more specification a
        MetaValidator should be used instead.
    default_type_suggestion: Type[_T] | None, optional
        The suggested type to generate the handler as.  If not provided, no assumption should
        be made.

    Parameters
    ----------
    Generic : _T
        The type to be validated to.
    """

    types: ValidatorMapping = field(default=Factory(dict))  # type: ignore
    default_type_suggestion: type[_T] | None = None
    default_validator: _MetaType | None = None

    def overwrite_from_parent(self: _NTH, other: _TypeHandler) -> _NTH:
        raise NotImplementedError()

    def get_type_suggestion(self, type: _MetaType) -> type[_T] | None:
        raise NotImplementedError()

    def has_type(self, type: _MetaType) -> bool:
        raise NotImplementedError()

    def get_if_validator_uses_parent(self, type: _MetaType) -> bool:
        raise NotImplementedError()

    def get_if_validator_uses_parent_validator(self, type: _MetaType) -> bool:
        raise NotImplementedError()

    def get_validator(self, type: _MetaType) -> _MetaValidator:
        raise NotImplementedError()

    @staticmethod
    def validate_by_type(type: _MetaType, values: Mapping) -> _T:
        raise NotImplementedError()


ValidatorHandlerMapping = Mapping[str, _TypeHandler]
"""
A map which contains a series of string, which define creatable types such as an int, float, str; and
their respective handlers such that they can be further validated into that type.
"""


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _TypeHandlerManager:
    """
    Manages which type is associated to which handler.  This primarily serves as a series of
    convenience methods to manage a map to ensure consistent validation.

    Attributes
    ----------
    types: ValidatorHandlerMapping
        A series of types and their associated validator handler.
    """

    types: ValidatorHandlerMapping = field(default=Factory(dict))  # type: ignore

    @classmethod
    def from_managers(cls: type[_NTHM], *managers: _TypeHandlerManager) -> _NTHM:
        raise NotImplementedError()

    def override_type_handler(self: _NTHM, type_: str, handler: _TypeHandler) -> _NTHM:
        raise NotImplementedError()

    def add_type_handler(self: _NTHM, type_: str, handler: _TypeHandler) -> _NTHM:
        raise NotImplementedError()

    def from_select_types(self: _NTHM, *types: str) -> _NTHM:
        raise NotImplementedError()


"""
Define custom exceptions.
"""


class ValidationException(Exception):
    """
    An exception that is raised during the validation of a validator.
    """

    __slots__ = ()


class InvalidPositionalArgumentsException(Exception):
    """
    An exception that is raised during the validation of a validator which provided too many or few
    positional arguments.
    """

    __slots__ = ("validator", "arguments")

    def __init__(self, validator: ComplexMetaValidator, arguments: Sequence):
        self.validator = validator
        self.arguments = arguments
        required_args = len(validator.arguments)
        provided_args = len(arguments)
        if required_args > provided_args:
            super().__init__(f"{self.validator} missing {required_args - provided_args} argument(s)")
        else:
            super().__init__(f"{self.validator} takes {required_args - provided_args} argument(s)")


class InvalidKeywordArgumentsException(Exception):
    """
    An exception that is raised during the validation of a validator which provided too many or few
    keyword arguments.
    """

    __slots__ = ("validator", "arguments")

    def __init__(self, validator: ComplexMetaValidator, arguments: Mapping):
        self.validator = validator
        self.arguments = arguments
        invalid_arguments = set(validator.keywords_arguments.keys()) - set(arguments.keys())
        if invalid_arguments:
            super().__init__(f"{self.validator} got an unexpected keyword argument `{next(iter(invalid_arguments))}`")
        missing_arguments = set(arguments.keys()) - set(validator.keywords_arguments.keys())
        super().__init__(f"{self.validator} is missing keyword arguments: {missing_arguments}")


class MalformedArgumentsExceptions(Exception):
    """
    An exception that is raised when the arguments and key-word arguments are
    incorrectly provided.
    """

    __slots__ = ("class_", "expected_value", "provided_value")

    def __init__(self, class_: type[Validator], expected_value: type, provided_value: Any):
        self.class_ = class_
        self.expected_value = expected_value
        self.provided_value = provided_value
        super().__init__(
            f"{class_.__name__} requires data to be passed as {expected_value.__name__}, "
            f"but was passed {provided_value}"
        )


class MissingException(ValidationException):
    __slots__ = ("class_", "required_fields", "provided_values")

    class_: type[Validator]
    required_fields: set[str]
    provided_values: Mapping[str, Any]

    def __init__(self, class_: type[Validator], required_fields: set[str], provided_values: Mapping[str, Any]):
        self.class_ = class_
        self.required_fields = required_fields
        self.provided_values = provided_values
        super().__init__(
            f"{class_.__name__} requires {required_fields}, but {self._find_missing_keys()}"
            f"were not inside {provided_values}"
        )

    def _find_missing_keys(self) -> set[str]:
        return self.required_fields - set(self.provided_values.keys())


class NamespaceValidationException(ValidationException):
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


"""
Define concrete classes.
"""


class _Validators:
    """
    A helper class that defines a series of validators to ensure the correct types with `attrs`.
    """

    __slots__ = ()

    @staticmethod
    def is_valid_list_of_names(inst, attr, value: tuple) -> tuple[str, ...]:
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
            if not Path.is_valid_name(name):
                raise InvalidChildName(name)
        return value


class _Converters:
    """
    A helper class that defines a series of converters to help with `attrs`.
    """

    __slots__ = ()

    @staticmethod
    def convert_to_validator(
        value: _MetaValidator | MetaValidator | ComplexMetaValidator,
    ) -> MetaValidator | ComplexMetaValidator:
        """
        Converts a callable to a validator if required.

        Parameters
        ----------
        value : _MetaValidator | MetaValidator | ComplexMetaValidator
            The callable or validator to form the validator with.

        Returns
        -------
        MetaValidator | ComplexMetaValidator
            The validator that represents the callable provided.
        """
        return value if isinstance(value, (MetaValidator, ComplexMetaValidator)) else MetaValidator(value)


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
        factory=tuple, validator=[validators.instance_of(tuple), _Validators.is_valid_list_of_names]
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

    @staticmethod
    def is_valid_name(name: Any, *, regex: str = "^[A-Za-z_][A-Za-z0-9_]*$") -> bool:
        """
        Determines if a name for a given child is considered valid.

        Parameters
        ----------
        name : Any
            The name to check if it is valid.
        regex : str, optional
            The regex expression to check for validity.

        Returns
        -------
        bool
            If the name is valid.
        """
        return bool(search(regex, name)) if isinstance(name, str) else False


class TypeHandler(_TypeHandler[_T]):
    """
    A model for representing the possible types a namespace element can possess and their
    respective validator methods.

    Attributes
    ----------
    types: ValidatorMapping
        A map containing the types and their respective validator methods.  This can come in
        two variants.  It can either be a simple callable or be defined as a MetaValidator.
        If a callable is provided, it will automatically be converted to a MetaValidator with
        default parameters for any MetaValidator specific methods.  For more specification a
        MetaValidator should be used instead.
    default_type_suggestion: Type[_T] | None, optional
        The suggested type to generate the handler as.  If not provided, no assumption should
        be made.

    Parameters
    ----------
    Generic : _T
        The type to be validated to.
    """

    __slots__ = ()

    @staticmethod
    def _converted_types(class_: _TypeHandler) -> Mapping[str, MetaValidator | ComplexMetaValidator]:
        return {key: _Converters.convert_to_validator(value) for key, value in class_.types.items()}

    def __eq__(self, other):
        if isinstance(other, _TypeHandler):
            return (
                self.default_type_suggestion == other.default_type_suggestion
                and self.default_validator == other.default_validator
                and self._converted_types(self).items() == self._converted_types(other).items()
            )
        return NotImplemented

    def overwrite_from_parent(self: _NTH, other: _TypeHandler) -> _NTH:
        """
        `other` overwrites or adds additional type validators from this handler
        to form a new handler.

        Parameters
        ----------
        other : _TypeHandler
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

    @staticmethod
    def validate_by_type(type: _MetaType, values: Mapping) -> _T:
        """
        Generates and validates `values` of `type` to generate an object from `parent`.

        Parameters
        ----------
        type : _MetaType
            The type of object to generate and validate.
        values : Mapping
            The attributes of the object.

        Raises
        ------
        TypeError
            `parent` was not provided inside `type`.

        Returns
        -------
        _T
            The generated and validated object.
        """
        parent = type.parent
        if parent is None:
            raise TypeError("Parent must be defined to validate a type")
        validator: _TypeHandler = parent.validators.types[type.type_suggestion]
        validator_type: _MetaType | None = Validator.get_type_argument(values, validator.default_validator)
        if validator_type is None:
            raise ValueError("Type is not defined")
        validator_type = evolve(validator_type, parent=parent)
        type_suggestion = validator.get_type_suggestion(validator_type)
        if type_suggestion is None:
            raise ValueError(f"Cannot deduce type of {values} from {validator}")
        if validator.get_if_validator_uses_parent(validator_type):
            values = values | {PARENT_ARGUMENT: parent}
        return validator.get_validator(validator_type)(type_suggestion, values)

    def get_type_suggestion(self, type: _MetaType) -> type[_T] | None:
        """
        Provides the type that `type` requires as the first argument for its validator.

        Parameters
        ----------
        type : _MetaType
            The key to a type and its associated validator.

        Returns
        -------
        Type[_T] | None
            Provides the type if one is provided, otherwise defaults on `default_type_suggestion`.
        """
        validator = _Converters.convert_to_validator(self.types[type.type_suggestion])
        if isinstance(validator, MetaValidator):
            return validator.type_suggestion
        validated_args, validated_kwargs = self._validate_complex_meta_validator_arguments(validator, type)
        return validator.decompose(*validated_args, **validated_kwargs).type_suggestion

    @classmethod
    def _validate_complex_meta_validator_arguments(
        cls, validator: ComplexMetaValidator, arguments: _MetaType
    ) -> tuple[Sequence, Mapping]:
        """
        Validates a complex validator's arguments, such that it can be safely decomposed with the
        arguments and keyword-arguments returned.

        Parameters
        ----------
        validator : ComplexMetaValidator
            The complex validator to supply validation.
        arguments : _MetaType
            The arguments to validate.

        Returns
        -------
        tuple[Sequence, Mapping]
            The validated arguments and keyword-arguments required to decompose `validator`.

        Raises
        ------
        InvalidPositionalArgumentsException
            Positional arguments are missing or too many positional arguments were provided.
        InvalidKeywordArgumentsException
            Keyword arguments are missing or extra keys were provided.
        TypeError
            One of the positional arguments was formed into an invalid type.
        TypeError
            One of the keyword arguments was formed into an invalid type.

        Notes
        -----
        If `validator` does not set `restrict_arguments`, only the `arguments` of `validator` will be
        validated.  The rest of the positional arguments will be appended to the end not validated.
        The same process occurs for `restrict_keywords`.
        """
        if (validator.restrict_arguments and len(validator.arguments) != len(arguments.arguments)) or (
            len(validator.arguments) <= len(arguments.arguments)
        ):
            raise InvalidPositionalArgumentsException(validator, arguments.arguments)
        if validator.restrict_keywords and validator.keywords_arguments.keys() != arguments.keyword_arguments.keys():
            raise InvalidKeywordArgumentsException(validator, arguments.keyword_arguments)
        args = tuple(
            Validator.get_type_argument(
                arg, Validator.validate_other_type(TypeValidator.__type_default__, arg_type).__type_default__
            )
            for arg_type, arg in zip(validator.arguments, arguments.arguments)
        )
        for arg, arg_type_suggestion in zip(args, validator.arguments):
            arg_type = Validator.validate_other_type(TypeValidator.__type_default__, arg_type_suggestion)
            if not isinstance(arg, type(arg_type)):
                raise TypeError(f"{arg} is not of type {arg_type.__class__}")
        if not validator.restrict_arguments:
            args = tuple(*args, *arguments.arguments[len(args) :])
        kwargs = {
            key: Validator.get_type_argument(
                arguments.keyword_arguments[key],
                Validator.validate_other_type(
                    TypeValidator.__type_default__, validator.keywords_arguments[key]
                ).__type_default__,
            )
            for key in validator.keywords_arguments.keys()
        }
        for key in validator.keywords_arguments.keys():
            kwarg_type = Validator.validate_other_type(
                TypeValidator.__type_default__, validator.keywords_arguments[key]
            )
            if not isinstance(kwargs[key], type(kwarg_type)):
                raise TypeError(f"{kwargs[key]} is not of type {kwarg_type.__class__}")
        if not validator.restrict_keywords:
            keywords_to_add = set(arguments.keyword_arguments.keys()) - set(validator.keywords_arguments.keys())
            for key in keywords_to_add:
                kwargs |= {key: validator.keywords_arguments[key]}
        return args, kwargs

    def get_validator(self, type: _MetaType) -> _MetaValidator:
        """
        Gets a validator to generate a specific object from a map.

        Parameters
        ----------
        type : _MetaType
            The type information that defines the validator.

        Returns
        -------
        _MetaValidator
            The validator associated with `type`.

        Notes
        -----
        If `type` does not define `parent`, then complex validators will not be supported.
        """
        validator = _Converters.convert_to_validator(self.types[type.type_suggestion])
        if isinstance(validator, MetaValidator):
            return validator.validator
        validated_args, validated_kwargs = self._validate_complex_meta_validator_arguments(validator, type)
        return validator.decompose(*validated_args, **validated_kwargs)

    def get_if_validator_uses_parent(self, type: _MetaType) -> bool:
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
        validator = _Converters.convert_to_validator(self.types[type.type_suggestion])
        if isinstance(validator, MetaValidator):
            return validator.use_parent
        validated_args, validated_kwargs = self._validate_complex_meta_validator_arguments(validator, type)
        return validator.decompose(*validated_args, **validated_kwargs).use_parent

    def has_type(self, type: _MetaType) -> bool:
        """
        A convenience method to quickly determine if a 'type' is valid.

        Parameters
        ----------
        type : _MetaType
            The type to check if it is registered.

        Returns
        -------
        bool
            If the type is registered.
        """
        return type.type_suggestion in self.types


class TypeHandlerManager(_TypeHandlerManager):
    """
    Manages which type is associated to which handler.  This primarily serves as a series of
    convenience methods to manage a map to ensure consistent validation.

    Attributes
    ----------
    types: ValidatorHandlerMapping
        A series of types and their associated validator handler.
    """

    __slots__ = ()

    def __eq__(self, other) -> bool:
        if isinstance(other, _TypeHandlerManager):
            return self.types.items() == other.types.items()
        return NotImplemented

    @classmethod
    def from_managers(cls: type[_NTHM], *managers: _TypeHandlerManager) -> _NTHM:
        """
        Effectively merges a series of managers together into a single manager.

        Parameters
        ----------
        *managers: _TypeHandlerManager
            A series of managers to merge together.
        """
        manager = cls(ChainMap())  # Stops the creation of an empty dict.
        for m in managers:
            for type_, handler in m.types.items():
                manager = manager.add_type_handler(type_, handler)
        return manager

    def override_type_handler(self: _NTHM, type_: str, handler: _TypeHandler) -> _NTHM:
        """
        Generates a new manager which removes the current handler of `type_` if it exists
        and replaces it with `handler`.

        Parameters
        ----------
        type_ : str
            The type to override.
        handler : _TypeHandler
            The handler to validate the type with.

        Returns
        -------
        Self
            The generated manager with the mutation or addition to `type_`.
        """
        if isinstance(self.types, ChainMap):
            return self.__class__(ChainMap({type_: handler}, *self.types.maps))  # No need to make a new ChainMap.
        return self.__class__(ChainMap({type_: handler}, self.types))

    def add_type_handler(self: _NTHM, type_: str, handler: _TypeHandler) -> _NTHM:
        """
        Generates a new manager which adds a handler to validate `type_`.  If `type_`
        is already defined a new handler will be used which overrides this instance's
        handler for `type_`, such that `handler`'s validators will be used instead.

        Parameters
        ----------
        type_ : str
            The type to add validators to.
        handler : _TypeHandler
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
            return self.__class__(ChainMapView(self.types, set(types)))  # No need to make a new ChainMap.
        return self.__class__(ChainMapView(ChainMap(self.types), valid_keys=set(types)))


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True, cache_hash=True, cmp=False, repr=False)
class Namespace(Generic[_T]):
    """
    A complex tree structure to aid in the parsing of JSON and dictionary structures to facilitate
    the reuse of names and objects in different contexts.

    Parameters
    ----------
    _T
        The type that each `elements` is inside this namespace.

    Attributes
    ----------
    parent: Namespace | None = None, optional
        The parent namespace, which will contain this instance as a child.  If None is provided, this
        namespace is assumed to be an orphan or a root node.  By default, the namespace is a root node.
    dependencies: Mapping[str, Namespace] = {}, optional
        A map of dependencies that were successfully loaded from this namespace's parent, such that
        this namespace is self sufficient and does not need to interface with its parent.  Primarily,
        this instance will not consider mutations, as it is assumed that a namespace is immutable.
        There path is also included, to allow for more complex operations.  This is an optional field,
        if it is not provided it is assumed that there are no dependencies.
    elements: Mapping[str, _T] = {}, optional
        A map of elements that represent this namespace's core contribution.  This represents the core
        mapping functionality of the namespace.  By default there are no elements.
    children: Mapping[str, Namespace] = {}, optional.
        A map of namespaces which depend on this namespace to instantiate.  Children also often inherit
        many other attributes, such as `validators` and can relatively reference from the parent.  By
        default a namespace contains no children.
    validators: _TypeHandlerManager = TypeHandlerManager({})
        A manager for the various types that this namespace and its children can define without any
        external actions.  This can be used to limit possible user action and to facilitate dependency
        injection opposed to statically defining every possible type and their associated validator.
        By default no types can be declared.  This is a design decision to enforce limiting user input.
    """

    parent: Namespace | None = field(eq=False, default=None)
    dependencies: Mapping[str, Namespace] = field(factory=dict)
    elements: Mapping[str, _T] = field(factory=dict)
    children: Mapping[str, Namespace] = field(factory=dict)
    validators: _TypeHandlerManager = field(
        eq=False,
        default=Factory(
            lambda self: TypeHandlerManager({}) if self.parent is None else self.parent.validators,  # type: ignore
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

    def evolve_child(self, name: str, child: Namespace) -> Namespace:
        """
        A method to recursively generate a new namespace where a new child is appended to itself.

        Parameters
        ----------
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
        updated_parent = evolve(self, children=(self.children | {name: child}))
        return self.parent.evolve_child(self.name, updated_parent) if self.parent is not None else updated_parent

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


class Validator:
    """
    A namespace element validator, which seeks to encourage extension and modularity for
    namespace validators.

    Attributes
    ----------
    __validator_handler__: _TypeHandler
        The handler for validators to automatically validate and generate the objects from a namespace,
        also incorporates the parent's attribute, if it exists.
    __type_default__: _MetaType | None
        The type default.  If None, then the type must be provided.
    __names__: tuple[str, ...]
        The names to associate this type with.
    """

    __validator_handler__: _TypeHandler
    __type_default__: _MetaType | None = None
    __names__: tuple[str, ...] = ("__NONE_VALIDATOR__", "NONE", "none")
    __slots__ = ()

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    @property
    def type_handler(cls: type[_V]) -> TypeHandler[_V]:
        """
        Provides the type handler for this type.

        Returns
        -------
        TypeHandler[_V]
            The handler for to validate this type.
        """
        if not hasattr(cls, "__validator_handler__") or not cls.__validator_handler__.types:
            return TypeHandler(
                ChainMap(*[getattr(b, "type_handler").types for b in cls.__bases__ if hasattr(b, "type_handler")]),
                default_validator=cls.__type_default__,
            )
        return TypeHandler(
            ChainMap(
                cls.__validator_handler__.types,
                *[getattr(b, "type_handler").types for b in cls.__bases__ if hasattr(b, "type_handler")],
            ),
            default_validator=cls.__type_default__,
        )

    @classmethod
    @property
    def type_manager(cls) -> TypeHandlerManager:
        """
        Provides the type manager for this type and all of its associated names.

        Returns
        -------
        TypeHandlerManager
            The manager to find the proper validations for this type.
        """
        return TypeHandlerManager({name: cls.type_handler for name in cls.__names__})

    @classmethod
    def check_for_kwargs_only(cls, values: Any, *expected: str) -> Mapping:
        """
        A convenience method to ensure only key-word arguments are passed.

        Parameters
        ----------
        values : Any
            The arguments to validate.
        *expected: str
            Any key-word arguments that are required or expected.

        Returns
        -------
        Mapping
            The validated arguments.

        Raises
        ------
        MalformedArgumentsExceptions
            If the arguments were invalid.
        MissingException
            If an expected argument is not provided inside `values`.
        """
        if isinstance(values, dict):
            raise MalformedArgumentsExceptions(cls, dict, values)
        for keyword in expected:
            if keyword not in values:
                raise MissingException(cls, set(expected), values)
        return values

    @classmethod
    def check_for_args_only(cls, values: Any) -> Sequence:
        """
        A convenience method to ensure only arguments were passed.

        Parameters
        ----------
        values : Any
            The arguments to validate.

        Returns
        -------
        Sequence
            The validated arguments.

        Raises
        ------
        MalformedArgumentsExceptions
            If the arguments were invalid.
        """
        if isinstance(values, list):
            raise MalformedArgumentsExceptions(cls, list, values)
        return values

    @classmethod
    def validate_other_type(cls, type: _MetaType, v: Mapping) -> Validator:
        """
        Validates another type of validator.  This is achieved by observing the namespace's attributes
        and utilizing the validator's name suggestion to allow for the namespace to extend or restrict
        the use of that validator as required.  This allows for namespace validation to be consistent
        and secure.

        Parameters
        ----------
        type: _MetaType
            The type information to generate the validator to.
        v : Mapping
            The attributes of the validator.

        Returns
        -------
        Validator
            The validated validator.

        Raises
        ------
        TypeError
            `parent` is not provided inside `type`.
        """
        parent = type.parent
        if parent is None:
            raise TypeError("Parent must be defined to validate a type")
        return parent.validators.types[type.type_suggestion].validate_by_type(type, v)

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
    def get_parent_suggestion(cls, v: Mapping) -> Namespace | None:
        """
        A convenience method to access the parent of the validator.

        Parameters
        ----------
        v : Mapping
            A mapping containing the information to generate the object.

        Returns
        -------
        Namespace | None
            The namespace of the object if it exists.
        """
        return v.get(PARENT_ARGUMENT, None)

    @classmethod
    def get_default_argument(cls, v: Any) -> Any:
        """
        A convenience method to access the default argument for a type which only accepts a single
        argument.

        Parameters
        ----------
        v : Any
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
        if not isinstance(v, dict):
            return v
        if DEFAULT_ARGUMENT not in v and TYPE_ARGUMENT not in v:
            raise TypeError(f"{cls.__name__} with arguments {v} is malformed")
        elif DEFAULT_ARGUMENT not in v and len(v) > 2:
            raise TypeError(f"{cls.__name__} of {cls.get_type_suggestion(v)} only accepts a single value, not {v}")
        elif DEFAULT_ARGUMENT not in v:
            raise TypeError(f"{cls.__name__} of {cls.get_type_suggestion(v)} must be provided a value, not {v}")
        return v[DEFAULT_ARGUMENT]

    @classmethod
    def _validate_from_namespace(cls: type[_V], parent: Namespace, name: str, path: str) -> _V:
        """
        Generates and validates from another existing object from `parent`.

        Parameters
        ----------
        cls: Type[_V]
            The type to find inside the namespace.
        parent : Namespace
            The namespace with the object to copy.
        name : str
            The name of the object.
        path : str
            The path to the object Namespace.

        Returns
        -------
        _V
            The object inside the Namespace.
        """
        return validate_element(parent=parent.from_path(Path.validate(parent=parent, path=path)), name=name, type=cls)

    @staticmethod
    def validate_from_namespace(class_: type[_V], v: Mapping) -> _V:
        """
        Generates and validates from another existing object inside a namespace.

        Parameters
        ----------
        class_ : Type[_V]
            The type to find inside the namespace.
        v : Mapping
            A map containing a parent, name, and path.

        Returns
        -------
        _V
            The object inside the Namespace.

        Raises
        ------
        TypeError
            There does not exist a parent inside `v`
        TypeError
            The parent is not a Namespace.
        TypeError
            There does not exist a name inside `v`
        TypeError
            The name is not a string.
        TypeError
            There does not exist a path inside `v`
        TypeError
            The path is not a string.
        """
        if (parent := class_.get_parent_suggestion(v)) is None:
            raise TypeError(f"Parent namespace was not defined inside {v} to generate {class_.__name__} from namespace")
        if not isinstance(parent, Namespace):
            raise TypeError(f"{parent} is not {Namespace.__name__}")
        if "name" not in v:
            raise TypeError(f"Name is not inside {v} to generate {class_.__name__} from namespace")
        if not isinstance((name := v["name"]), str):
            raise TypeError(f"{name} is not {str.__name__}")
        if "path" not in v:
            raise TypeError(f"Path is not inside {v} to generate {class_.__name__} from namespace")
        if not isinstance((path := v["path"]), str):
            raise TypeError(f"{path} is not {str.__name__}")
        return class_._validate_from_namespace(parent, name, path)

    @classmethod
    def validate_by_type(cls: type[_V], v: Mapping) -> _V:
        """
        Generates and validates an object by its type defined in `__validator_handler__`.

        Parameters
        ----------
        cls : Type[_V]
            The type of object to generate.
        v : Mapping
            A mapping containing the information to generate the object.

        Returns
        -------
        _V
            The object generated from `v` specified by its type.
        """
        type_ = cls.get_type_argument(v)
        if type_ is None:
            raise KeyError(f"Cannot find type of {v}")
        return cls.type_handler.get_validator(type_)(cls, v)

    @classmethod
    def validate_type(cls: type[_V], v: Any) -> _V:
        """
        Generates and validates an object by its types and ensures that there is a type
        inside `v` such that it can be validated further.

        Parameters
        ----------
        cls : Type[_V]
            The type of object to generate.
        v : Any
            A map containing the information to generate the object.

        Returns
        -------
        _V
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
        type_ = cls.get_type_argument(v)
        if type_ is None:
            if cls.__type_default__ is None:
                raise TypeError(f"{v} does not define a type for {cls.__name__}")
            type_ = cls.__type_default__
        elif not cls.type_handler.has_type(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid type")
        v[TYPE_ARGUMENT] = type_  # Enforce that TYPE_ARGUMENT will always work for subclass validators.
        return cls.validate_by_type(v)

    @staticmethod
    def _get_type_argument(v: Mapping) -> Any:
        """
        Determines the type argument from a predefined list of valid types.

        Parameters
        ----------
        v : Mapping
            The map to find the type argument inside.

        Returns
        -------
        Any
            The type argument if found, else None.
        """
        return next((v[k] for k in VALID_TYPE_ARGUMENTS if k in v), None)

    @staticmethod
    def _get_type_meta_arguments(v: dict) -> tuple[Sequence, dict]:
        """
        Determines the type meta-arguments from a series of type arguments, `v`.

        Parameters
        ----------
        v : dict
            The type arguments to find the meta-arguments from.

        Returns
        -------
        tuple[Sequence, dict]
            A tuple containing the meta-args and meta-kwargs.

        Raises
        ------
        TypeError
            The meta-arguments are malformed.
        TypeError
            The meta-keyword-arguments are malformed.
        """
        args = next((v[k] for k in VALID_META_TYPE_ARGUMENTS if k in v), ())
        if not isinstance(args, Sequence):
            raise TypeError(f"Type arguments are malformed: {args} is not a list")
        kwargs = next((v[k] for k in VALID_META_TYPE_KEYWORD_ARGUMENTS if k in v), {})
        if not isinstance(kwargs, dict):
            raise TypeError(f"Type keyword arguments are malformed: {kwargs} is not a dictionary")
        return args, kwargs

    @staticmethod
    def _sanitize_type_arguments(v: Any) -> Mapping | str | None:
        """
        Sanitizes type arguments, such that the arguments will be provided in one of three states.

        Parameters
        ----------
        v : Any
            The data to validate.

        Returns
        -------
        Mapping | str | None
            One of three sanitized values representing the type arguments.  If None is returned, no type
            information can be determined.  If a str is passed, simple type information can be found
            at `v[TYPE_ARGUMENT]`.  If a map is passed, complex type information, `m`, can be found at
            `v[TYPE_ARGUMENT]`.  Inside `m` there exists three validated values: `TYPE_ARGUMENT`,
            `META_TYPE_ARGUMENTS`, and `META_TYPE_KEYWORD_ARGUMENTS` for the type suggestion,
            type meta-arguments, and type meta-keyword-arguments, respectively.

        Raises
        ------
        TypeError
            There exists `v[TYPE_ARGUMENT]`, but the data inside it is malformed.
        TypeError
            There exists a map inside `v[TYPE_ARGUMENT]`, but it does not provide a type suggestion.
        """
        if not isinstance(v, dict):
            return None
        type_data = v[TYPE_ARGUMENT] = Validator._get_type_argument(v)
        if type_data is None or isinstance(type_data, str):
            return type_data
        if not isinstance(type_data, dict):
            raise TypeError(f"Type is malformed: {type_data} must either be a string or dictionary")
        type_suggestion = type_data[TYPE_ARGUMENT] = Validator._get_type_argument(type_data)
        if type_suggestion is None:
            raise TypeError(f"Type is not defined: {type_suggestion} does not define `type`")
        type_data[META_TYPE_ARGUMENTS], type_data[META_TYPE_KEYWORD_ARGUMENTS] = Validator._get_type_meta_arguments(
            type_data
        )
        return type_data

    @staticmethod
    def get_type_argument(v: Any, default: _MetaType | None = None) -> _MetaType | None:
        """
        Determines the type of the object.  A few options are used, but it is advised to only
        use a single one, as the process to select the type should be assumed to be random.

        Parameters
        ----------
        v : Mapping
            A map of values to determine the type from.
        default: _MetaType | None = None
            The default type suggestion.

        Returns
        -------
        _MetaType | None
            The type if found otherwise None.
        """
        type_information = Validator._sanitize_type_arguments(v)
        if type_information is None:
            return evolve(default, parent=Validator.get_parent_suggestion(v))
        if isinstance(type_information, str):
            return _MetaType(v, parent=Validator.get_parent_suggestion(v))
        return _MetaType(
            type_information[TYPE_ARGUMENT],
            type_information[META_TYPE_ARGUMENTS],
            type_information[META_TYPE_KEYWORD_ARGUMENTS],
            Validator.get_parent_suggestion(v),
        )


class ConcreteValidator(Validator):
    """
    Automatically provides this class as the type suggestion for the handler.  This is so the namespace
    generation functions can actually call this instance with the correct type.
    """

    @classmethod
    @property
    def type_handler(cls: type[_CV]) -> TypeHandler[_CV]:
        handler = super().type_handler
        return evolve(handler, default_type_suggestion=cls)  # type: ignore


NoneValidator = ConcreteValidator


class TypeValidator(ConcreteValidator, TypeHandler):
    """
    A validator to generate a meta validator.
    """

    __type_default__: _MetaType = _MetaType("DEFAULT")
    __names__ = ("__TYPE_VALIDATOR__", "type", "TYPE")

    @classmethod
    @property
    def type_handler(cls: type[_TV]) -> _TypeHandler[_TV]:
        return cls.__validator_handler__

    @classmethod
    def validate(cls: type[_TV], v: Mapping) -> _TV:
        """
        Generates and validates a type validator from a map.

        Parameters
        ----------
        v : Mapping
            The values to validate.

        Returns
        -------
        _TV
            The validated type validator.

        Raises
        ------
        TypeError
            A parent was not provided.
        TypeError
            A type suggestion could not be found.
        """
        parent = Validator.get_parent_suggestion(v)
        if parent is None:
            raise TypeError(f"Parent was not defined inside {v}")
        type_suggestion = Validator.get_type_argument(v)
        if type_suggestion is None:
            raise TypeError(f"Type information was not provided inside {v}")
        handler = parent.validators.types[type_suggestion.type_suggestion]
        return cls(handler.types, handler.default_type_suggestion, handler.default_validator)


def _validate_type(class_: type[_TV], v: Mapping) -> _TV:
    return class_.validate(v)


TypeValidator.__validator_handler__ = TypeHandler({"DEFAULT": _validate_type})


class PrimitiveValidator(ConcreteValidator):
    """
    Adds methods to easily validate primitives through their native constructors.
    """

    __type_default__ = _MetaType("DEFAULT")

    def __init__(self, value: Any):
        super().__init__()

    @classmethod
    def validate_primitive(cls: type[_PV], v: Mapping) -> _PV:
        return cls(cls.get_default_argument(v))


def _validate_primitive(class_: type[_PV], v: Mapping) -> _PV:
    return class_.validate_primitive(v)


PrimitiveValidator.__validator_handler__ = TypeHandler(
    {"DEFAULT": MetaValidator(_validate_primitive, use_parent=False)}
)


class IntegerValidator(int, PrimitiveValidator):
    """
    A validator for integers.
    """

    __names__ = ("__INTEGER_VALIDATOR__", "int", "integer", "Int", "Integer", "INT", "INTEGER")


IntegerValidator.__validator_handler__ = TypeHandler(default_type_suggestion=IntegerValidator)


class NonNegativeIntegerValidator(IntegerValidator):
    __names__ = (
        "__NONNEGATIVE_INTEGER_VALIDATOR__",
        "non-negative int",
        "non-negative integer",
        "NONNEGATIVE_INT",
        "NONNEGATIVE_INTEGER",
    )

    @classmethod
    def validate_primitive(cls: type[_PV], v: Mapping) -> _PV:
        self = super().validate_primitive(v)
        if 0 > self:  # type: ignore
            raise ValueError(f"{self} must be a non-negative integer")
        return self


class FloatValidator(float, PrimitiveValidator):
    """
    A validator for floats.
    """

    __names__ = ("__FLOAT_VALIDATOR__", "float", "Float", "FLOAT")


FloatValidator.__validator_handler__ = TypeHandler(default_type_suggestion=FloatValidator)


class StringValidator(str, PrimitiveValidator):
    """
    A validator for strings.
    """

    __names__ = ("__STRING_VALIDATOR__", "str", "string", "Str", "String", "STR", "STRING")


StringValidator.__validator_handler__ = TypeHandler(default_type_suggestion=StringValidator)


primitive_manager = TypeHandlerManager.from_managers(
    NoneValidator.type_manager,
    IntegerValidator.type_manager,
    NonNegativeIntegerValidator.type_manager,
    FloatValidator.type_manager,
    StringValidator.type_manager,
)


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
    """
    Determines if there is a cycle inside for any dependency from a mapping.

    Parameters
    ----------
    graph : Mapping[Path, set[Path]]
        The graph to test if a cycle exists.

    Returns
    -------
    tuple[Path]
        A path which creates the cycle.
    """
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


def validate_namespace_type(namespace: Namespace, v: Mapping) -> _MetaType:
    """
    Validates that a namespace's type is a valid type.

    Parameters
    ----------
    namespace : Namespace
        The namespace to validate the type from.
    v : Mapping
        The mapping with the data for a namespace.

    Returns
    -------
    str
        The validated type.

    Raises
    ------

    TypeError
        There does not exist type inside `v`.
    TypeError
        `type` is not present inside `validators`.
    """
    v_to_validate = ChainMap({TYPE_ARGUMENT: namespace}, v)
    type_: _MetaType | None = Validator.get_type_argument(v_to_validate)
    if type_ is None:
        raise TypeError(f"Type of namespace is not found inside {v}.")
    if type_.type_suggestion not in namespace.validators.types.keys():
        raise TypeError(f"{type_} is not supported, only {namespace.validators.types.keys()}.")
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
    v: Mapping, parent: Namespace | None = None, validators: _TypeHandlerManager | None = None
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
    type_handler: _TypeHandlerManager | None, optional
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
    element_type = validate_namespace_type(namespace, v)
    handler = namespace.validators.types[element_type.type_suggestion]

    dependencies: set[Path] = set() if "dependencies" not in v else {Path.from_string(d) for d in v["dependencies"]}
    if parent is None and dependencies:
        dependency = list(dependencies)[0]
        raise ChildDoesNotExistException(dependency, dependency.root)
    elif parent:
        namespace = evolve(namespace, dependencies={str(path): parent.from_path(path) for path in dependencies})

    elements = {}
    for key, value in ({} if "elements" not in v else v["elements"]).items():
        elements[key] = handler.validate_by_type(element_type, value)
    namespace = evolve(namespace, elements=elements)

    return namespace


def generate_namespace(v: Mapping, validators: _TypeHandlerManager | None = None) -> Namespace:
    """
    Generates the root namespace from a mapping, creating every aspect of the namespace, including its
    children.  This also includes validation of the namespace, its children, its elements, and its children's
    elements, recursively.

    Parameters
    ----------
    v : Mapping
        The mapping to generate the namespace and its children from.
    validators: _TypeHandlerManager | None, optional.
        The possible validators that the namespace can possess, None by default.

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

    root = validate_namespace(v, None, validators)
    for dependency_path in order:
        dependency_parent_path = dependency_path.parent
        assert dependency_parent_path is not None  # This should be impossible because it must be descendent of root.

        dependency_parent = root.from_path(dependency_parent_path)
        dependency = validate_namespace(get_namespace_dict_from_path(v, dependency_path), dependency_parent)
        root = dependency_parent.evolve_child(dependency_path.name, dependency)  # Evolve the immutable root.

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
    if not Path.is_valid_name(name):
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
            if not Path.is_valid_name(name):
                raise ValueError(f"Invalid path name '{name}' from `{path}`")
    return path


# Allow all types to be validated by reference natively.
Validator.__validator_handler__ = TypeHandler({"FROM NAMESPACE": Validator.validate_from_namespace})
