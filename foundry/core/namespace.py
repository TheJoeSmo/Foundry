from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import suppress
from functools import partial
from graphlib import CycleError, TopologicalSorter
from re import findall, search
from typing import Any, ClassVar, Generic, Literal, TypeVar, overload

from attr import Factory, attrs, evolve, field, validators

from foundry.core import ChainMap, ChainMapView, sequence_to_pretty_str

"""
Declare constant literals.
"""

DEFAULT_ARGUMENT: Literal["__DEFAULT_ARGUMENT__"] = "__DEFAULT_ARGUMENT__"
"""
When a validator only desires a single argument, it will be passed as through this.
"""

NOT_PROVIDED_ARGUMENT: Literal["__NOT_PROVIDED_ARGUMENT__"] = "__NOT_PROVIDED_ARGUMENT__"
"""
When the user did not provide an argument, this signifies that a default value should be used instead.
"""


TYPE_INFO_ARGUMENT: Literal["__TYPE_INFO_ARGUMENT__"] = "__TYPE_INFO_ARGUMENT__"
"""
The type the validator that should be used to create and object.
"""

PARENT_ARGUMENT: Literal["__PARENT__"] = "__PARENT__"
"""
The parent namespace that is passed to create an object relating to its namespace.
"""

TYPE_INFO_ARGS_ARGUMENTS: Literal["__TYPE_INFO_ARGS__"] = "__TYPE_INFO_ARGS__"
"""
The key inside a dictionary for determining extra arguments for a type.
"""

TYPE_INFO_KWARGS_ARGUMENTS: Literal["__TYPE_INFO_KWARGS__"] = "__TYPE_INFO_KWARGS__"
"""
The key inside a dictionary for determining extra keyword arguments for a type.
"""

TYPE_INFO_ARGUMENTS = (TYPE_INFO_ARGUMENT, "TYPE", "type")
"""
The valid ways a user can define the type attribute.
"""

VALID_META_TYPE_ARGUMENTS = (TYPE_INFO_ARGS_ARGUMENTS, "args", "ARGS", "arguments", "ARGUMENTS")
"""
The valid ways a user can define the type meta-arguments.
"""

VALID_META_TYPE_KEYWORD_ARGUMENTS = (
    TYPE_INFO_KWARGS_ARGUMENTS,
    "kwargs",
    "KWARGS",
    "keyword arguments",
    "KEYWORD ARGUMENTS",
)
"""
The valid ways a user can define the type meta-keyword-arguments.
"""

INVALID_USER_DEFINED_TYPES: str = "^(__)([^\r\n]+)(__)"
"""
Types that cannot be defined from the user.  This is primarily dunder types.
"""

EXCLUDED_VALUES: set[str] = {PARENT_ARGUMENT}
"""
Values that should be excluded inside an exception.
"""


"""
Declare private type hints.
"""

_T = TypeVar("_T")
_V = TypeVar("_V", bound="Validator")
_KV = TypeVar("_KV", bound="KeywordValidator")
_CV = TypeVar("_CV", bound="ConcreteValidator")
_TV = TypeVar("_TV", bound="TypeValidator")
_PV = TypeVar("_PV", bound="PrimitiveValidator")
_NTH = TypeVar("_NTH", bound="_TypeHandler")
_NTHM = TypeVar("_NTHM", bound="_TypeHandlerManager")


ValidatorCallable = Callable[[type[_T], Any], _T]
"""
Validates a type `_T` into an object `_T` by accepting a map of values.
"""

ComplexValidatorCallable = Callable[[type[_T], Mapping, Sequence], ValidatorCallable[_T]]
"""
Validates a type, `_T` into an object by accepting a map of values and a sequence and map of preset conditions
required for a complex type validator.
"""

_ComplexValidatorArguments = tuple[Sequence, Mapping]
"""
Arguments required to decompose `ComplexValidatorCallable`, which have been validated.
"""

"""
Declare common data class structures for common use.
"""


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
class TypeInformation(Generic[_T]):
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

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}(type_suggestion={self.type_suggestion}, "
        if self.arguments:
            s = f"{s}arguments={self.arguments}, "
        if self.keyword_arguments:
            s = f"{s}keyword_arguments={self.keyword_arguments}, "
        if self.parent is not None:
            s = f"{s}parent={self.parent}, "
        if s[-1] == " ":
            s = s[:-2]
        return f"{s})"


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True, repr=False)
class ValidatorCallableInformation(Generic[_T]):
    """
    A generic interface to validate an type into an object.

    Attributes
    ----------
    validator: ValidatorCallable
        The callable to convert the type into an object.
    type_suggestion: Type[_T] | None = None
        The suggested type to convert.
    use_parent: bool = True
        If the type requires a parent namespace to become an object.
    """

    validator: ValidatorCallable
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
class _ComplexValidatorCallableInformation(Generic[_T]):
    """
    A generic interface to decompose a complex validator into a normal validator.

    Attributes
    ----------
    validator: ComplexValidatorCallable
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

    validator: ComplexValidatorCallable
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

    def decompose(self, *args, **kwargs) -> ValidatorCallable[_T]:
        raise NotImplementedError

    def validate_type_information(self, info: TypeInformation) -> _ComplexValidatorArguments:
        raise NotImplementedError


ValidatorInformation = ValidatorCallable | ValidatorCallableInformation | _ComplexValidatorCallableInformation
"""
All the possible variants of validator callable information that can be provided from a namespace.
"""


ValidatorMapping = Mapping[str, ValidatorInformation]
"""
A map which contains a series of strings, which define creatable types such as the default, from
namespace, etc.; and their respective validators such that types could be validated in multiple ways.
"""


@attrs(slots=True, auto_attribs=True, frozen=True, eq=False, hash=True)
class _TypeHandler(Generic[_T]):
    """
    A model for representing the possible types a namespace element can possess and their
    respective validator methods.

    Attributes
    ----------
    types: ValidatorMapping
        A map containing the types and their respective validator methods.  This can come in
        two variants.  It can either be a simple callable or be defined as a ValidatorCallableInformation.
        If a callable is provided, it will automatically be converted to a ValidatorCallableInformation with
        default parameters for any ValidatorCallableInformation specific methods.  For more specification a
        ValidatorCallableInformation should be used instead.
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
    default_validator: TypeInformation | None = None

    def __eq__(self, other):
        if isinstance(other, _TypeHandler):
            return (
                self.default_type_suggestion == other.default_type_suggestion
                and self.default_validator == other.default_validator
                and self.types.keys() == other.types.keys()
                and all(
                    filter(
                        lambda k: _Converters.convert_to_validator(self.types[k])  # type: ignore
                        == _Converters.convert_to_validator(other.types[k]),  # type: ignore
                        iter(self.types.keys()),
                    )
                )
            )
        return NotImplemented

    def overwrite_from_parent(self: _NTH, other: _TypeHandler) -> _NTH:
        raise NotImplementedError

    def get_type_suggestion(self, info: TypeInformation) -> type[_T] | None:
        raise NotImplementedError

    def has_type(self, type: TypeInformation) -> bool:
        raise NotImplementedError

    def get_if_validator_uses_parent(self, type: TypeInformation) -> bool:
        raise NotImplementedError

    def get_validator(self, type: TypeInformation) -> ValidatorCallable:
        raise NotImplementedError

    @classmethod
    def validate_to_type(cls, type: TypeInformation, values: Mapping) -> _T:
        raise NotImplementedError


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


class ValidationException(ValueError):
    """
    An exception that is raised during the validation of a validator.
    """

    __slots__ = ()


class InvalidTypeArgumentException(ValidationException):
    """
    An exception that is raised when arguments to define the type of an object to validate is not
    provided.

    Attributes
    ----------
    argument: Mapping
        The argument that caused the exception.
    handler: _TypeHandler | _TypeHandlerManager
        The handler that was unable to determine the type.
    """

    __slots__ = ("argument", "handler")

    argument: Mapping | str
    handler: _TypeHandler | _TypeHandlerManager

    @property
    def valid_types(self) -> tuple[str]:
        return tuple(
            set(self.handler.types.keys())
            - set(findall(INVALID_USER_DEFINED_TYPES, "\n".join(self.handler.types.keys())))
        )


class MissingTypeArgumentException(InvalidTypeArgumentException):
    """
    An exception that is raised when the type arguments are not provided.
    """

    argument: Any

    __slots__ = ()

    def __init__(self, argument: Any, handler: _TypeHandler | _TypeHandlerManager):
        if isinstance(argument, Mapping):
            argument = {k: v for k, v in argument.items() if k not in EXCLUDED_VALUES}
        self.argument = argument
        self.handler = handler
        super().__init__(
            f"{self.argument} missing type argument to determine type from "
            f"valid types: {sequence_to_pretty_str(list(self.handler.types.keys()))}"
        )


class TypeNotFoundException(InvalidTypeArgumentException):
    """
    An exception that is raised when the type argument is provide but the handler did not
    define the type provided.
    """

    __slots__ = ()

    def __init__(self, argument: Mapping | str, handler: _TypeHandler | _TypeHandlerManager):
        if isinstance(argument, Mapping):
            argument = {k: v for k, v in argument.items() if k not in EXCLUDED_VALUES}
        self.argument = argument
        self.handler = handler
        if isinstance(argument, str):
            super().__init__(
                f"{self.argument} could not be found inside " f"valid types: {sequence_to_pretty_str(self.valid_types)}"
            )
        else:
            super().__init__(
                f"{argument.get(TYPE_INFO_ARGUMENT, None)} could not be found inside "
                f"valid types: {sequence_to_pretty_str(self.valid_types)}"
            )


class InvalidPositionalArgumentsException(ValidationException):
    """
    An exception that is raised during the validation of a validator which provided too many or few
    positional arguments.
    """

    __slots__ = ("validator", "arguments")

    def __init__(self, validator: ComplexValidatorCallableInformation, arguments: Sequence):
        self.validator = validator
        self.arguments = arguments
        required_args = len(validator.arguments)
        provided_args = len(arguments)
        if required_args > provided_args:
            super().__init__(f"{self.validator} missing {required_args - provided_args} argument(s)")
        else:
            super().__init__(f"{self.validator} takes {required_args - provided_args} argument(s)")


class InvalidKeywordArgumentsException(ValidationException):
    """
    An exception that is raised during the validation of a validator which provided too many or few
    keyword arguments.
    """

    __slots__ = ("validator", "arguments")

    def __init__(self, validator: ComplexValidatorCallableInformation, arguments: Mapping):
        self.validator = validator
        self.arguments = arguments
        if invalid_arguments := set(validator.keywords_arguments.keys()) - set(arguments.keys()):
            super().__init__(f"{self.validator} got an unexpected keyword argument `{next(iter(invalid_arguments))}`")
        missing_arguments = set(arguments.keys()) - set(validator.keywords_arguments.keys())
        super().__init__(f"{self.validator} is missing keyword arguments: {missing_arguments}")


class MalformedArgumentsExceptions(ValidationException):
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
        self.provided_values = {k: provided_values[k] for k in provided_values if k not in EXCLUDED_VALUES}
        super().__init__(
            f"{class_.__name__} requires {required_fields}, but "
            f"{sequence_to_pretty_str(list(self._find_missing_keys()))} "
            f"were not inside {self.provided_values}"
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
        value: ValidatorInformation,
    ) -> ValidatorCallableInformation | _ComplexValidatorCallableInformation:
        """
        Converts a callable to a validator if required.

        Parameters
        ----------
        value : ValidatorCallable | ValidatorCallableInformation | ComplexValidatorCallableInformation
            The callable or validator to form the validator with.

        Returns
        -------
        ValidatorCallableInformation | ComplexValidatorCallableInformation
            The validator that represents the callable provided.
        """

        return (
            value
            if isinstance(value, (ValidatorCallableInformation, _ComplexValidatorCallableInformation))
            else ValidatorCallableInformation(value)
        )


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


class ComplexValidatorCallableInformation(_ComplexValidatorCallableInformation[_T]):
    def decompose(self, *args, **kwargs) -> ValidatorCallable[_T]:
        """
        Decomposes the complex validator into a normal validator.

        Returns
        -------
        ValidatorCallable
            The decomposed validator.

        Notes
        -----
        This method does not supply any validation of the arguments passed.
        """
        return self.validator(*args, **kwargs)

    @staticmethod
    def _validate_argument(validator: type[Validator], handler: TypeHandler, argument: Any, parent: Namespace) -> Any:
        validated_argument = validator.validate_arguments_to_map(
            argument, default_override=handler.default_validator, parent=parent
        )
        type_info = validated_argument[TYPE_INFO_ARGUMENT] = Validator.get_type_information(
            validated_argument, handler.default_validator
        )
        if type_info is None:
            type_info = getattr(validator, "__type_default__", None)
        if type_info is None:
            raise MissingTypeArgumentException(validated_argument, handler)
        if type_info.type_suggestion not in handler.types:
            raise TypeNotFoundException(validated_argument, handler)
        validated_argument |= {TYPE_INFO_ARGUMENT: type_info.type_suggestion}  # enforce type found
        return validator.validate_by_type(validated_argument)

    @staticmethod
    def _validate_arguments(
        restrict_arguments: bool,
        argument_types: Sequence,
        arguments: Sequence,
        parent: Namespace,
    ) -> Sequence | None:
        if (restrict_arguments and len(argument_types) != len(arguments)) or (len(argument_types) <= len(arguments)):
            return None
        return tuple(
            *(
                ComplexValidatorCallableInformation._validate_argument(
                    TypeValidator, TypeValidator.validate(arg_type), arg, parent
                )
                for arg_type, arg in zip(argument_types, arguments)
            ),
            *arguments[len(argument_types) :],
        )

    @staticmethod
    def _validate_keyword_arguments(
        restrict_keywords: bool, keyword_types: Mapping, arguments: Mapping, parent: Namespace
    ) -> Mapping | None:
        if restrict_keywords and keyword_types.keys() != arguments.keys():
            return None
        return {
            key: ComplexValidatorCallableInformation._validate_argument(
                TypeValidator, TypeValidator.validate(keyword_types[key]), arguments[key], parent
            )
            for key in keyword_types.keys()
        } | {key: arguments[key] for key in set(arguments.keys()) - set(keyword_types.keys())}

    def validate_type_information(self, info: TypeInformation) -> _ComplexValidatorArguments:
        """
        Validates a complex validator's arguments, such that it can be safely decomposed with the
        arguments and keyword-arguments returned.

        Parameters
        ----------
        info : TypeInformation
            The type arguments to validate.

        Returns
        -------
        _ComplexValidatorArguments
            The validated type arguments and keyword-arguments required to decompose `self`.

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
        If `self` does not set `restrict_arguments`, only the `info` of `self` will be
        validated.  The rest of the positional arguments will be appended to the end not validated.
        The same process occurs for `restrict_keywords`.
        """
        parent = info.parent
        if parent is None:
            raise TypeError(f"Parent must be defined inside {info}")
        args = self._validate_arguments(self.restrict_arguments, self.arguments, info.arguments, parent)
        if args is None:
            raise InvalidPositionalArgumentsException(self, info.arguments)
        kwargs = self._validate_keyword_arguments(
            self.restrict_keywords, self.keywords_arguments, info.keyword_arguments, parent
        )
        if kwargs is None:
            raise InvalidKeywordArgumentsException(self, info.keyword_arguments)
        return args, kwargs


class TypeHandler(_TypeHandler[_T]):
    """
    A model for representing the possible types a namespace element can possess and their
    respective validator methods.

    Attributes
    ----------
    types: ValidatorMapping
        A map containing the types and their respective validator methods.  This can come in
        two variants.  It can either be a simple callable or be defined as a ValidatorCallableInformation.
        If a callable is provided, it will automatically be converted to a ValidatorCallableInformation with
        default parameters for any ValidatorCallableInformation specific methods.  For more specification a
        ValidatorCallableInformation should be used instead.
    default_type_suggestion: Type[_T] | None, optional
        The suggested type to generate the handler as.  If not provided, no assumption should
        be made.

    Parameters
    ----------
    Generic : _T
        The type to be validated to.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}({dict(self.types)}, "
        if self.default_type_suggestion is not None:
            s = f"{s}default_type_suggestion={self.default_type_suggestion.__name__}, "
        if self.default_validator is not None:
            s = f"{s}default_validator={self.default_validator}, "
        if s[-1] == " ":
            s = s[:-2]
        return f"{s})"

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

    @classmethod
    def validate_to_type(cls, type: TypeInformation, values: Mapping) -> _T:
        """
        Generates and validates `values` of `type` to generate an object from `parent`.

        Parameters
        ----------
        type : TypeInformation
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
        handler: _TypeHandler = parent.validators.types[type.type_suggestion]
        validator: TypeInformation | None = Validator.get_type_information(values, handler.default_validator)
        # try a second time
        if validator is None and handler.default_type_suggestion is not None:
            validator_class: type[Validator] = handler.default_type_suggestion
            validator: TypeInformation | None = validator_class.type_handler.default_validator
        if validator is None:
            raise ValueError(
                f"Type is not defined for {handler.default_validator} from values {values}, "
                + f"only {set(handler.types.keys())} are supported"
            )
        validator = evolve(validator, parent=parent)
        type_suggestion = handler.get_type_suggestion(validator)
        if type_suggestion is None:
            raise ValueError(f"Cannot deduce type of {values} from {handler}")
        if handler.get_if_validator_uses_parent(validator):
            values = values | {PARENT_ARGUMENT: parent}
        return handler.get_validator(validator)(type_suggestion, values)

    def get_type_suggestion(self, info: TypeInformation) -> type[_T] | None:
        """
        Provides the type that `info` requires as the first argument for its validator.

        Parameters
        ----------
        info : TypeInformation
            The information for a given type to generate its associated validator.

        Returns
        -------
        type[_T] | None
            Provides the type if one is provided, otherwise defaults on `default_type_suggestion`.
        """
        try:
            type_suggestion = self.types[info.type_suggestion]
        except KeyError as e:
            raise TypeNotFoundException(info.type_suggestion, self) from e
        validator = _Converters.convert_to_validator(type_suggestion)
        if isinstance(validator, ValidatorCallableInformation):
            return validator.type_suggestion if validator.type_suggestion is not None else self.default_type_suggestion
        validated_args, validated_kwargs = validator.validate_type_information(info)
        return validator.decompose(*validated_args, **validated_kwargs).type_suggestion

    def get_validator(self, type: TypeInformation) -> ValidatorCallable:
        """
        Gets a validator to generate a specific object from a map.

        Parameters
        ----------
        type : TypeInformation
            The type information that defines the validator.

        Returns
        -------
        ValidatorCallable
            The validator associated with `type`.

        Notes
        -----
        If `type` does not define `parent`, then complex validators will not be supported.
        """
        validator = _Converters.convert_to_validator(self.types[type.type_suggestion])
        if isinstance(validator, ValidatorCallableInformation):
            return validator.validator
        validated_args, validated_kwargs = validator.validate_type_information(type)
        return validator.decompose(*validated_args, **validated_kwargs)

    def get_if_validator_uses_parent(self, type: TypeInformation) -> bool:
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
        if isinstance(validator, ValidatorCallableInformation):
            return validator.use_parent
        validated_args, validated_kwargs = validator.validate_type_information(type)
        return validator.decompose(*validated_args, **validated_kwargs).use_parent

    def has_type(self, type: TypeInformation) -> bool:
        """
        A convenience method to quickly determine if a 'type' is valid.

        Parameters
        ----------
        type : TypeInformation
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self.types)})"

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
        if isinstance(self.types, (ChainMap, ChainMapView)):
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


class _ValidatorHelper:
    """
    A class containing a series of helper methods to validate items from a namespace.
    """

    @classmethod
    def is_valid_type_name(cls, name: str) -> bool:
        """
        Determines if a type can be defined by a user.

        Parameters
        ----------
        name : str
            The name to validate.

        Returns
        -------
        bool
            If the name could be a valid type name.
        """
        return not search(INVALID_USER_DEFINED_TYPES, name) if isinstance(name, str) else False

    @classmethod
    def get_type_identity_suggestion(cls, v: Mapping) -> Mapping | str | None:
        """
        Determines the type argument from a predefined list of valid types.

        Parameters
        ----------
        v : Mapping
            The map to find the type argument inside.

        Returns
        -------
        Mapping | str | None
            The type argument if found, else None.

        Raises
        ------
        TypeError
            The type is not a map or string.
        """
        type_identity = next((v[k] for k in TYPE_INFO_ARGUMENTS if k in v), None)
        if isinstance(type_identity, TypeInformation):
            type_identity = type_identity.type_suggestion
        if type_identity is None:
            return None
        if isinstance(type_identity, (str, Mapping)):
            return type_identity
        raise TypeError(f"Type must be a string or map, not {type_identity}")

    @classmethod
    def get_type_identity(cls, v: Mapping) -> str:
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
            The type identity of the object.
        """
        return v[TYPE_INFO_ARGUMENT]

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
    def get_type_information(cls, v: Any, default: TypeInformation | None = None) -> TypeInformation | None:
        """
        Determines the type of the object.  A few options are used, but it is advised to only
        use a single one, as the process to select the type should be assumed to be random.

        Parameters
        ----------
        v : Mapping
            A map of values to determine the type from.
        default: TypeInformation | None = None
            The default type suggestion.

        Returns
        -------
        TypeInformation | None
            The type if found otherwise None.
        """
        type_information = cls._sanitize_type_arguments(v)
        if type_information is None:
            if default is None:
                return None
            return evolve(default, parent=cls.get_parent_suggestion(v) if isinstance(v, dict) else None)
        if isinstance(type_information, str):
            return TypeInformation(type_information, parent=cls.get_parent_suggestion(v))
        return TypeInformation(
            type_information[TYPE_INFO_ARGUMENT],
            type_information[TYPE_INFO_ARGS_ARGUMENTS],
            type_information[TYPE_INFO_KWARGS_ARGUMENTS],
            cls.get_parent_suggestion(v),
        )

    @classmethod
    def _get_type_meta_arguments(cls, v: dict) -> _ComplexValidatorArguments:
        """
        Determines the type meta-arguments from a series of type arguments, `v`.

        Parameters
        ----------
        v : dict
            The type arguments to find the meta-arguments from.

        Returns
        -------
        _ComplexValidatorArguments
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

    @classmethod
    def _sanitize_type_arguments(cls, v: Any) -> Mapping | str | None:
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
            at `v[TYPE_INFO_ARGUMENT]`.  If a map is passed, complex type information, `m`, can be found at
            `v[TYPE_INFO_ARGUMENT]`.  Inside `m` there exists three validated values: `TYPE_INFO_ARGUMENT`,
            `TYPE_INFO_ARGS_ARGUMENTS`, and `TYPE_INFO_KWARGS_ARGUMENTS` for the type suggestion,
            type meta-arguments, and type meta-keyword-arguments, respectively.

        Raises
        ------
        TypeError
            There exists `v[TYPE_INFO_ARGUMENT]`, but the data inside it is malformed.
        TypeError
            There exists a map inside `v[TYPE_INFO_ARGUMENT]`, but it does not provide a type suggestion.
        """
        if not isinstance(v, dict):
            return None
        type_data = v[TYPE_INFO_ARGUMENT] = cls.get_type_identity_suggestion(v)
        if type_data is None or isinstance(type_data, str):
            return type_data
        if not isinstance(type_data, dict):
            raise TypeError(f"Type is malformed: {type_data} must either be a string or dictionary")
        type_suggestion = type_data[TYPE_INFO_ARGUMENT] = cls.get_type_identity_suggestion(type_data)
        if type_suggestion is None:
            raise TypeError(f"Type is not defined: {type_suggestion} does not define `type`")
        (
            type_data[TYPE_INFO_ARGS_ARGUMENTS],
            type_data[TYPE_INFO_KWARGS_ARGUMENTS],
        ) = cls._get_type_meta_arguments(type_data)
        return type_data


class Validator(_ValidatorHelper):
    """
    A namespace element validator, which seeks to encourage extension and modularity for
    namespace validators.

    Attributes
    ----------
    __validator_handler__: ClassVar[_TypeHandler]
        The handler for validators to automatically validate and generate the objects from a namespace,
        also incorporates the parent's attribute, if it exists.
    __type_default__: ClassVar[TypeInformation | None]
        The type default.  If None, then the type must be provided.
    __names__: ClassVar[tuple[str, ...]]
        The names to associate this type with.
    __required_validators__: ClassVar[tuple[type[Validator]]]
        Required validators to use the full capacity of this validator.
    __allowed_conversions__: ClassVar[tuple[type, ...]] = ()
        Any additional acceptable conversions other than this validator that this validator is permitted
        to create.  This is meant to used to reference an underlying validator which this type decorates.

    Notes
    -----
    While `__allowed_conversions__` can be used in many applications, it is strongly advised to not use
    it unless absolutely required.  This is because this creates the issue that any of the types provided
    from this validator will decompose into the union of all the types and this type provided.  This
    could generate a leak of type data and would result in the corruption of validated data.
    """

    __validator_handler__: ClassVar[_TypeHandler]
    __type_default__: ClassVar[TypeInformation | None] = None
    __names__: ClassVar[tuple[str, ...]] = ("__NONE_VALIDATOR__", "NONE", "none")
    __required_validators__: ClassVar[tuple[type[Validator], ...]] = ()
    __allowed_conversions__: ClassVar[tuple[type[Validator], ...]] = ()
    __slots__ = ()

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    @property
    def default_name(cls) -> str:
        """
        Provides the name suggestion for this type, for it to be found by a manager.

        Returns
        -------
        str
            The name suggestion.
        """
        return cls.__names__[0]

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
        return TypeHandlerManager().from_managers(
            TypeHandlerManager({name: cls.type_handler for name in cls.__names__}),
            *(validator.type_manager for validator in cls.__required_validators__),
        )

    @classmethod
    def get_type_handler_from_parent(cls, parent: Namespace) -> _TypeHandler:
        """
        Obtains the handler for a type from `parent`.

        Parameters
        ----------
        parent: Namespace
            The parent to get the handler from.

        Returns
        -------
        _TypeHandler
            The handler that is associated with this type.
        """
        handler = parent.validators.types.get(cls.default_name, None)
        if handler is None:
            raise TypeError(f"{parent} does not support {cls.default_name}")
        return handler

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
        type_ = cls.get_type_information(v)
        if type_ is None:
            raise KeyError(f"Cannot find type of { {k: v_ for k, v_ in v.items() if k not in EXCLUDED_VALUES} }")
        return cls.type_handler.get_validator(type_)(cls, v)

    @classmethod
    def validate_arguments_to_map(
        cls, v: Any, *, default_override: TypeInformation | None = None, parent: Namespace | None = None
    ) -> dict:
        """
        Standardizes the arguments passed to a map.

        Parameters
        ----------
        v : Any
            A map containing the information to generate the object.
        default_override: TypeInformation | None = None
            An override to use as a default validator.
        parent: Namespace | None = None
            Sets the parent attribute.

        Returns
        -------
        Mapping
            The information standardized to a map.

        Raises
        ------
        TypeError
            `v` was not passed as a map.
        """
        if isinstance(v, dict):
            if parent is not None:
                v[PARENT_ARGUMENT] = parent
            return v
        default_suggestion = default_override or cls.__type_default__
        if default_suggestion is None:
            raise TypeError(f"{v} is not a {dict.__name__}")
        return {DEFAULT_ARGUMENT: v, PARENT_ARGUMENT: parent, TYPE_INFO_ARGUMENT: default_suggestion.type_suggestion}

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
            There does not exist `type` inside `v` and `__type_default__` is None.
        TypeError
            `type` is not a valid type.
        """
        v = cls.validate_arguments_to_map(v)
        type_ = cls.get_type_information(v)
        if type_ is None:
            if cls.__type_default__ is None:
                raise TypeError(f"{v} does not define a type for {cls.__name__}")
            type_ = cls.__type_default__
        elif not cls.type_handler.has_type(type_):
            raise TypeError(f"{type_} is not a valid type")
        return cls.validate_by_type(v)


"""
Helper methods to define new types of validators.
"""


def _get_classmethod_validator_method(method_name: str) -> ValidatorCallable:
    """
    Provides a validator from a classmethod.  This extracts the class from the class method to
    allow it to be called with ease.

    Parameters
    ----------
    method_name : str
        The name of the method to use.

    Returns
    -------
    ValidatorCallable
        The validator from the classmethod.
    """

    def call_classmethod_validator(cls: type[_V], v) -> _V:
        return getattr(cls, method_name)(v)

    return call_classmethod_validator


def _get_classmethod_complex_validator_method(method_name: str) -> _ComplexValidatorCallableInformation:
    """
    Provides a validator from a classmethod.  This extracts the class from the class method to
    allow it to be called with ease.

    Parameters
    ----------
    method_name : str
        The name of the method to use.

    Returns
    -------
    _ComplexValidatorCallableInformation
        The complex validator from the classmethod.
    """

    def call_classmethod_validator(cls, kwargs, args):
        return getattr(cls, method_name)(kwargs, args)

    return _ComplexValidatorCallableInformation(call_classmethod_validator)


def custom_validator(
    validator_name: str,
    complex: bool = False,
    use_parent: bool | None = None,
    validator: ValidatorInformation | None = None,
    method_name: str = "validate",
) -> Callable[[type[_V]], type[_V]]:
    """
    Provides a decorator to add a custom method as a validator to a validator type.

    Parameters
    ----------
    validator_name : str
        The name that the user can define this validator as.
    complex: bool, optional
            Determines if the validator provided should be considered complex if it derives from
            `cls` and `method_name`.
    use_parent
        If the validator should use a parent.
    validator : ValidatorInformation | None, optional
            The method to be used as the validator, by default None.  If None, it will try to
            use `method_name` to find a classmethod to use as a validator.
    method_name : str, optional
        A method_name to provide if a method is not provided, by default "validate"

    Returns
    -------
    Callable[[type[_V], ValidatorInformation | None, str], type[_V]]
        A decorator to add a custom method to a validator.
    """

    def custom_validator(
        cls: type[_V],
    ) -> type[_V]:
        """
        Adds a method to the validator handler following a class' instantiation.  This is done
        to help remove the otherwise clunky syntax required.

        Parameters
        ----------
        cls : type[_V]
            The class to be modified.


        Returns
        -------
        type[_V]
            The modified validator.
        """
        val = validator
        if validator is None:
            if complex:
                val = _get_classmethod_complex_validator_method(method_name)
            elif use_parent is None:
                val = _get_classmethod_validator_method(method_name)
            else:
                val = ValidatorCallableInformation(
                    _get_classmethod_validator_method(method_name), use_parent=use_parent
                )

        if not hasattr(cls, "__validator_handler__"):
            cls.__validator_handler__ = TypeHandler()
        cls.__validator_handler__ = evolve(
            cls.__validator_handler__, types=cls.__validator_handler__.types | {validator_name: val}
        )
        return cls

    return custom_validator


@overload
def default_validator(
    cls: None = None,
    complex: bool = False,
    use_parent: bool = True,
    validator: ValidatorInformation | None = None,
    method_name: str = "validate",
) -> partial:
    ...


@overload
def default_validator(
    cls: type[_V] = None,
    complex: bool = False,
    use_parent: bool = True,
    validator: ValidatorInformation | None = None,
    method_name: str = "validate",
) -> type[_V]:
    ...


def default_validator(
    cls: type[_V] | None = None,
    complex: bool = False,
    use_parent: bool = True,
    validator: ValidatorInformation | None = None,
    method_name: str = "validate",
):
    """
    Generates a validator for the default type suggestion.

    Parameters
    ----------
    cls : type[_V]
        The validator to decorate.
    complex: bool, optional
        If the validator is complex.
    use_parent
        If the validator should use a parent.
    validator : ValidatorInformation | None, optional
        The validator to use, if it is not defined inside `cls`, by default None
    method_name : str, optional
        The method of the `cls` to use if `validator` is None, by default "validate"
    """
    if cls is None:
        return partial(
            default_validator, complex=complex, use_parent=use_parent, validator=validator, method_name=method_name
        )

    if cls.__type_default__ is None or cls.__type_default__.type_suggestion is None:
        cls.__type_default__ = TypeInformation("DEFAULT")
    if hasattr(cls, "__validator_handler__") and cls.__validator_handler__.default_validator is None:
        cls.__validator_handler__ = evolve(cls.__validator_handler__, default_validator=TypeInformation("DEFAULT"))
    return custom_validator(cls.__type_default__.type_suggestion, complex, use_parent, validator, method_name)(cls)


"""
Helper validators to provide specific helper methods to ease integration into the system.
"""


class SingleArgumentValidator(Validator):
    """
    A validator that only accepts a single validator.
    """

    __slots__ = ()

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
        if TYPE_INFO_ARGUMENT not in v:
            raise TypeError(
                f"{cls.__name__} with arguments { {k: v_ for k, v_ in v.items() if k not in EXCLUDED_VALUES} } "
                + "is malformed"
            )
        if DEFAULT_ARGUMENT not in v:
            raise ValueError(
                f"{cls.__name__} with arguments { {k: v_ for k, v_ in v.items() if k not in EXCLUDED_VALUES} } "
                + "is not a single argument"
            )
        return v[DEFAULT_ARGUMENT]


class ArgumentsValidator(SingleArgumentValidator):
    """
    A validator to more easily parse a list of arguments.
    """

    __slots__ = ()

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
        argument = cls.get_default_argument(values)
        if not isinstance(argument, Sequence):
            raise MalformedArgumentsExceptions(cls, Sequence, argument)
        return argument


class KeywordValidator(Validator):
    """
    A validator to more easily parse a dict and their associated keyword arguments.
    """

    __slots__ = ()

    @classmethod
    def check_for_kwargs_only(cls, values: Any, *expected: tuple[str, bool]) -> Mapping:
        """
        A convenience method to ensure only key-word arguments are passed.

        Parameters
        ----------
        values : Any
            The arguments to validate.
        *expected: tuple[str, bool]
            Any key-word arguments that are expected anf if they are required.

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
        if not isinstance(values, dict):
            raise MalformedArgumentsExceptions(cls, dict, values)
        for keyword, required in expected:
            if required and keyword not in values:
                raise MissingException(cls, {e[0] for e in expected}, values)
        return values


class ConcreteValidator(Validator):
    """
    Automatically provides this class as the type suggestion for the handler.  This is so the namespace
    generation functions can actually call this instance with the correct type.
    """

    __slots__ = ()

    @classmethod
    @property
    def type_handler(cls: type[_CV]) -> TypeHandler[_CV]:
        handler = super().type_handler
        return evolve(handler, default_type_suggestion=cls)  # type: ignore


NoneValidator = ConcreteValidator


@default_validator
class TypeValidator(ConcreteValidator, KeywordValidator, TypeHandler):
    """
    A validator to generate a meta validator.
    """

    __names__ = ("__TYPE_VALIDATOR__", "type", "TYPE")
    __slots__ = ()

    @classmethod
    @property
    def type_handler(cls: type[_TV]) -> _TypeHandler[_TV]:
        return cls.__validator_handler__

    @classmethod
    def from_validator(cls: type[_TV], validator: type[Validator], parent: Namespace) -> _TV:
        handler = parent.validators.types.get(validator.default_name, None)
        if handler is None:
            raise MissingTypeArgumentException(validator, parent.validators)
        return cls(handler.types, handler.default_type_suggestion, handler.default_validator)

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
        parent = cls.get_parent_suggestion(v)
        if parent is None:
            raise TypeError(f"Parent was not defined inside {v}")
        type_suggestion = cls.get_type_information(v)
        if type_suggestion is None:
            raise TypeError(f"Type information was not provided inside {v}")
        handler = parent.validators.types[type_suggestion.type_suggestion]
        return cls(handler.types, handler.default_type_suggestion, handler.default_validator)


"""
Primitive validator definitions which enables the creation of new types quickly.
"""


@default_validator(complex=True)
class OptionalValidator(ConcreteValidator):
    """
    A validator which decorates another type to allow it to either be provided
    or be None.  Otherwise, it will provide normal validation of the underlying
    validator.
    """

    __intern__: ClassVar[dict[type[Validator], type[Validator]]] = {}
    __slots__ = ()

    @classmethod
    def generate_class(cls, argument_validator: type[Validator]) -> type[Validator]:
        """
        Generates an optional validator which decorates the underlying validator provided.

        Parameters
        ----------
        argument_validator : type[Validator]
            The validator to be decorated.

        Returns
        -------
        type[Validator]
            The optional validator that wraps `argument_validator`.
        """
        if argument_validator not in cls.__intern__:

            @classmethod
            def validate(cls, v: Mapping):
                if NOT_PROVIDED_ARGUMENT in v:
                    return None
                with suppress(MissingTypeArgumentException, TypeNotFoundException):
                    return validate_argument(argument_validator, v, cls.get_parent_suggestion(v))
                return None

            InternalOptionalValidator = default_validator(
                type(
                    f"{argument_validator.__name__}OptionalValidator",
                    (ConcreteValidator, ArgumentsValidator),
                    {
                        "validate": validate,
                        "__names__": argument_validator.__names__,
                        "__default__": None,
                        "__required_validators__": (argument_validator,),
                        "__allowed_conversions__": (argument_validator,),
                        "__slots__": (),
                    },
                )
            )

            cls.__intern__[argument_validator] = InternalOptionalValidator
        return cls.__intern__[argument_validator]

    @classmethod
    def validate(cls, kwargs, args) -> ValidatorCallable:
        return cls.generate_class(args).validate  # type: ignore


class DefaultValidator(OptionalValidator):
    """
    A validator which decorates another type to allow it to either be provided
    or be a default value.  Otherwise, it will provide normal validation of the underlying
    validator.
    """

    __intern__: ClassVar[dict[tuple[type[Validator], Any], type[Validator]]] = {}
    __slots__ = ()

    @classmethod
    def generate_class(cls, argument_validator: type[Validator], default: Any) -> type[Validator]:
        """
        Generates an default or optional validator which decorates the underlying validator provided.

        Parameters
        ----------
        argument_validator : type[Validator]
            The validator to be decorated.

        Returns
        -------
        type[Validator]
            The default or optional validator that wraps `argument_validator` to have the default
            value of `default`.
        """
        if default is None:
            return OptionalValidator.generate_class(argument_validator)

        if (argument_validator, default) not in cls.__intern__:
            InternalOptionalValidator = OptionalValidator.generate_class(argument_validator)

            @classmethod
            def validate(cls, v: Mapping):
                if NOT_PROVIDED_ARGUMENT in v:
                    return default
                with suppress(MissingTypeArgumentException, TypeNotFoundException):
                    return validate_argument(InternalOptionalValidator, v, cls.get_parent_suggestion(v))
                return default

            InternalDefaultValidator = default_validator(
                type(
                    f"{argument_validator.__name__}DefaultValidator",
                    (ConcreteValidator, ArgumentsValidator),
                    {
                        "validate": validate,
                        "__names__": argument_validator.__names__,
                        "__default__": default,
                        "__required_validators__": (argument_validator,),
                        "__allowed_conversions__": (argument_validator,),
                        "__slots__": (),
                    },
                )
            )

            cls.__intern__[(argument_validator, default)] = InternalDefaultValidator
        return cls.__intern__[(argument_validator, default)]


@default_validator(complex=True)
class SequenceValidator(ConcreteValidator):
    """
    A validator which decorates another type to allow it to be provided as a list of elements.
    """

    __intern__: ClassVar[dict[type[Validator], type[Validator]]] = {}
    __slots__ = ()

    @classmethod
    def generate_class(cls, argument_validator: type[_V]) -> type[Validator]:
        """
        Generates an sequence validator which decorates the underlying validator provided.

        Parameters
        ----------
        argument_validator : type[Validator]
            The validator to be decorated.

        Returns
        -------
        type[Validator]
            The sequence validator that wraps `argument_validator`.
        """
        if argument_validator not in cls.__intern__:

            def __init__(self, elements: Sequence[_V]):
                self.elements = tuple(elements)

            def __repr__(self) -> str:
                return f"{self.__class__.__name__}({self.elements})"

            def __getitem__(self, index: int) -> _V:
                return self.elements[index]

            def __len__(self) -> int:
                return len(self.elements)

            @classmethod
            def validate(cls, v: Mapping):
                args = cls.check_for_args_only(v)
                return cls(validate_argument(argument_validator, arg, cls.get_parent_suggestion(v)) for arg in args)

            InternalSequenceValidator = default_validator(
                type(
                    f"{argument_validator.__name__}SequenceValidator",
                    (Sequence, ConcreteValidator, ArgumentsValidator),
                    {
                        "validate": validate,
                        "__init__": __init__,
                        "__getitem__": __getitem__,
                        "__len__": __len__,
                        "__required_validators__": (argument_validator,),
                        "__slots__": ("elements",),
                    },
                )
            )

            cls.__intern__[argument_validator] = InternalSequenceValidator
        return cls.__intern__[argument_validator]

    @classmethod
    def validate(cls, kwargs, args) -> ValidatorCallable:
        return cls.generate_class(args).validate  # type: ignore


@default_validator(complex=True)
class TupleValidator(ConcreteValidator):
    """
    A validator which decorates a series of validators to allow it to be provided as a ordered list
    of elements.
    """

    __intern__: ClassVar[dict[tuple[type[Validator], ...], type[Validator]]] = {}
    __slots__ = ()

    @classmethod
    def generate_class(cls, argument_validators: tuple[type[Validator], ...]) -> type[Validator]:
        """
        Generates an tuple validator which decorates the underlying validators provided.

        Parameters
        ----------
        argument_validators: tuple[type[Validator], ...]
            An ordered sequence of validators to be decorated.

        Returns
        -------
        type[Validator]
            The tuple validator that wraps `argument_validators`.
        """
        if argument_validators not in cls.__intern__:

            def __init__(self, elements: tuple):
                self.elements = elements

            def __repr__(self) -> str:
                return f"{self.__class__.__name__}({self.elements})"

            def __getitem__(self, index: int) -> Validator:
                return self.elements[index]

            def __len__(self) -> int:
                return len(self.elements)

            @classmethod
            def validate(cls, v: Mapping):
                args = cls.check_for_args_only(v)
                return tuple(
                    validate_argument(arg_validator, arg, cls.get_parent_suggestion(v))
                    for arg, arg_validator in zip(args, argument_validators)
                )

            InternalTupleValidator = default_validator(
                type(
                    "InternalTupleValidator",
                    (Sequence, ConcreteValidator, ArgumentsValidator),
                    {
                        "validate": validate,
                        "__init__": __init__,
                        "__getitem__": __getitem__,
                        "__len__": __len__,
                        "__required_validators__": argument_validators,
                        "__slots__": ("elements",),
                    },
                )
            )

            cls.__intern__[argument_validators] = InternalTupleValidator
        return cls.__intern__[argument_validators]

    @classmethod
    def validate(cls, kwargs, args) -> ValidatorCallable:
        return cls.generate_class(args).validate  # type: ignore


@default_validator(use_parent=False, method_name="validate_primitive")
class PrimitiveValidator(ConcreteValidator, SingleArgumentValidator):
    """
    Adds methods to easily validate primitives through their native constructors.
    """

    __slots__ = ()

    def __init__(self, value: Any):
        super().__init__()

    @classmethod
    def validate_primitive(cls: type[_PV], v) -> _PV:
        return cls(cls.get_default_argument(v))


@default_validator(use_parent=False)
class BoolValidator(ConcreteValidator, SingleArgumentValidator):
    """
    A validator for booleans.

    Notes
    -----
    Due to the way literals work inside Python, bool cannot be extended.  To get around this
    restriction we simply decompose the validator to its core type.
    """

    __names__ = ("__BOOL_VALIDATOR__", "bool", "Bool", "BOOL", "boolean", "Boolean", "BOOLEAN")
    __allowed_conversions__ = (bool,)  # type: ignore
    __slots__ = ()

    def __init__(self, value: Any):
        super().__init__()

    @classmethod
    def validate(cls, v) -> bool:
        return bool(cls.get_default_argument(v))


class IntegerValidator(int, PrimitiveValidator):
    """
    A validator for integers.
    """

    __names__ = ("__INTEGER_VALIDATOR__", "int", "integer", "Int", "Integer", "INT", "INTEGER")
    __slots__ = ()


class NonNegativeIntegerValidator(IntegerValidator):
    __names__ = (
        "__NONNEGATIVE_INTEGER_VALIDATOR__",
        "non-negative int",
        "non-negative integer",
        "NONNEGATIVE_INT",
        "NONNEGATIVE_INTEGER",
    )
    __slots__ = ()

    @classmethod
    def validate_primitive(cls: type[_PV], v) -> _PV:
        self = super().validate_primitive(v)
        if self < 0:  # type: ignore
            raise ValueError(f"{self} must be a non-negative integer")
        return self


class FloatValidator(float, PrimitiveValidator):
    """
    A validator for floats.
    """

    __names__ = ("__FLOAT_VALIDATOR__", "float", "Float", "FLOAT")
    __slots__ = ()


class StringValidator(str, PrimitiveValidator):
    """
    A validator for strings.
    """

    __names__ = ("__STRING_VALIDATOR__", "str", "string", "Str", "String", "STR", "STRING")
    __slots__ = ()


primitive_manager = TypeHandlerManager.from_managers(
    NoneValidator.type_manager,
    OptionalValidator.type_manager,
    DefaultValidator.type_manager,
    SequenceValidator.type_manager,
    TupleValidator.type_manager,
    BoolValidator.type_manager,
    IntegerValidator.type_manager,
    NonNegativeIntegerValidator.type_manager,
    FloatValidator.type_manager,
    StringValidator.type_manager,
)


def validate_argument(validator: type[_V], arg: Any, parent: Namespace) -> _V:
    """
    Validates an arbitrary argument where the validator is already known.

    Parameters
    ----------
    validator : type[_V]
        The type to validate to.
    arg : Any
        The argument to be validated.
    parent : Namespace
        The parent to obtain validation information from.

    Returns
    -------
    _V
        The validated argument.
    """
    return ComplexValidatorCallableInformation._validate_argument(
        validator, TypeValidator.from_validator(validator, parent), arg, parent
    )


def validate(**kwargs: type[Validator]) -> Callable[[Callable[..., _KV]], ValidatorCallable[_KV]]:
    """
    A decorator to automatically validate a series of keyword arguments with a series of validators.

    Parameters
    ----------
    **kwargs: type[Validator]
        A series of keyword required values to generator with respect to the validator.

    Returns
    -------
    Callable[[Callable[..., _KV]], ValidatorCallable[_KV]]
        A decorator which will take a classmethod and converts it to a validator.
    """

    def validate(_f: Callable[..., _KV]) -> ValidatorCallable[_KV]:
        def validate_arguments(cls: type[_KV], values: Any) -> _KV:
            """
            Validates `values` by the predetermined kwargs validator suggestions with respect
            to the parent namespace passed inside `values`.

            Parameters
            ----------
            values : Any
                A series of values to be validated.

            Returns
            -------
            _KV
                The values validated and composed into its correct type.

            Raises
            ------
            KeyError
                The parent namespace was not defined inside `values`.
            """
            kwargs_ = cls.check_for_kwargs_only(
                values, *[(k, isinstance(kwargs[k], (DefaultValidator, OptionalValidator))) for k in kwargs]
            )
            parent = cls.get_parent_suggestion(values)
            if parent is None:
                raise KeyError("Parent is required")
            return _f(
                cls,
                **{
                    k: validate_argument(v, kwargs_.get(k, {NOT_PROVIDED_ARGUMENT: None}), parent)
                    for k, v in kwargs.items()
                },
            )

        return validate_arguments

    return validate


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


def validate_namespace_type(namespace: Namespace, v: Mapping) -> TypeInformation:
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
    v_to_validate = v | {PARENT_ARGUMENT: namespace}
    type_: TypeInformation | None = Validator.get_type_information(v_to_validate)
    if type_ is None:
        raise TypeError(f"Type of namespace is not found inside {v}.")
    if type_.type_suggestion not in namespace.validators.types.keys():
        raise TypeNotFoundException(v_to_validate, namespace.validators)
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

    elements = {
        key: handler.validate_to_type(element_type, value)
        for key, value in ({} if "elements" not in v else v["elements"]).items()
    }

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
    valid_types = (type_, *getattr(type_, "__allowed_conversions__", ()))
    if not isinstance(obj, valid_types):
        raise ValueError(
            f"Object `{obj}` at {Path(tuple(parent.path))!s}.{name} is not one of the following: "
            + f"{sequence_to_pretty_str([t.__name__ for t in valid_types])}, but a {obj.__class__.__name__}"
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
Validator.__validator_handler__ = TypeHandler({"FROM NAMESPACE": Validator.validate_from_namespace})  # type: ignore
