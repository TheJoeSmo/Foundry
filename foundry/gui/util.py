from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLayout,
    QMainWindow,
    QMenu,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from foundry import open_url
from foundry.gui.settings import SETTINGS

ID_PROP = "ID"


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        item.widget().deleteLater()


def ease_color(color1: QColor, color2: QColor, amount: float) -> QColor:
    """
    Eases between two colors, providing a combination of the two.

    Parameters
    ----------
    color1 : QColor
        The color which will be displayed with respect to amount.
    color2 : QColor
        The color which will be displayed with respect to 1 - amount.
    amount : float
        The amount as a decimal, where 1 represents everything and 0 represents nothing,
        that color1 will be shown and color2 will not.

    Returns
    -------
    QColor
        The intermediary color from color1 and color2.
    """
    alt_amount = 1 - amount
    return QColor(
        int(color1.red() * amount + color2.red() * alt_amount),
        int(color1.green() * amount + color2.green() * alt_amount),
        int(color1.blue() * amount + color2.blue() * alt_amount),
    )


class WhatIsThis(BaseModel):
    """
    A generic representation of the what's this description.  This enables a multi-line
    description to easily transfer from JSON and similar formats.

    Attributes
    ----------
    elements: list[str]
        A list of strings that represent each line of the description.
    """

    elements: list[str]

    @property
    def description(self) -> str:
        """
        The description of the `what's this` field in its entirety.

        Returns
        -------
        str
            The description of what the object is.
        """
        return "\n".join(self.elements)


class WidgetType(str, Enum):
    """
    A declaration of the widgets possible to be created through
    `JSON <https://en.wikipedia.org/wiki/JSON>`_ and
    `Pydantic <https://pydantic-docs.helpmanual.io/>`_.
    """

    button = "BUTTON"
    spinner = "SPINNER"

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


class Widget(BaseModel):
    """
    A generic representation of :class:`~PySide6.QtWidgets.QWidget`.

    Attributes
    ----------
    type: WidgetType
        The type of widget this widget represents.  This determines how constructors
        will treat the widget, often providing it additional parameters.
    parent_attribute_name: Optional[str]
        If provided, will be used to set this widget to its parent's name.
    what_is_this: Optional[WhatIsThis]
        The type hint for the given widget, if provided.
    """

    type: WidgetType
    parent_attribute_name: Optional[str]
    what_is_this: Optional[WhatIsThis]

    class Config:
        use_enum_values = True  # Allow storing the enum as a string


class Button(Widget):
    """
    A button representation of :class:`PySide6.QtWidgets.QPushButton`.

    Attributes
    ----------
    name: str
        The text that appears on the button.
    action: Optional[str]
        The name of the callable that will be acted upon when clicked.
    """

    name: str = Field(default_factory=Field(""))
    action: Optional[str]


class Spinner(Widget):
    """
    A spinner representation of :class:`PySide6.QtWidgets.QSpinBox`.


    Attributes
    ----------
    enabled: bool
        Decides if the spinner will be activated on start.
    minimum: Optional[int]
        Will provide a lower bound that will be applied to the spinner, if present.
    maximum: Optional[int]
        Will provide an upper bound that will be applied to the spinner, if present.
    hexadecimal: bool
        Decides if the spinner should use hex as its base.
    value_change_action: Optional[str]
        The name of the callable that will be acted upon when the value changes.
    """

    enabled: bool = Field(default_factor=Field(True))
    minimum: Optional[int]
    maximum: Optional[int]
    hexadecimal: bool = Field(default_factor=Field(False))
    value_change_action: Optional[str]


class WidgetCreator(BaseModel):
    """
    A generator for a :class:`~foundry.gui.util.Widget`.  Creates the widget dynamically from
    its type attribute to provide it additional information required to be a subclass of
    widget.

    For example a widget of type button will become a button, instead of a plain widget.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        return super().__init_subclass__(**kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def generate_widget(cls, v: dict) -> Widget:
        """
        The constructor for each specific widget.

        Parameters
        ----------
        v : dict
            The dictionary to create the widget.

        Returns
        -------
        Widget
            The created widget as defined by `v["type"]`.

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """
        type_ = WidgetType(v["type"])
        if type_ == WidgetType.button:
            return Button(**v)
        if type_ == WidgetType.spinner:
            return Spinner(**v)
        raise NotImplementedError(f"There is no widget of type {type_}")

    @classmethod
    def validate(cls, v: dict) -> Widget:
        """
        Validates that the provided object is a valid Widget.

        Parameters
        ----------
        v : dict
            The dictionary to create the widget.

        Returns
        -------
        Widget
            If validated, a widget will be created in accordance to `generate_widget`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:`~foundry.gui.util.WidgetType`.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not WidgetType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid widget type")
        return cls.generate_widget(v)


class LayoutType(str, Enum):
    """
    A declaration of the layouts possible to be created through
    `JSON <https://en.wikipedia.org/wiki/JSON>`_ and
    `Pydantic <https://pydantic-docs.helpmanual.io/>`_.
    """

    horizontal = "HORIZONTAL"
    verticle = "VERTICLE"
    form = "FORM"

    @classmethod
    def has_value(cls, value):
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


class LayoutMeta(BaseModel):
    """
    A generic representation of :class:`~PySide6.QtWidgets.QLayout`.

    Attributes
    ----------
    type: LayoutType
        The type of layout this layout represents.  This determines how constructors
        will treat the layout, often providing it additional parameters.
    """

    type: LayoutType

    class Config:
        use_enum_values = True  # Allow storing the enum as a string


class BoxLayout(LayoutMeta):
    """
    A layout which the widgets are laid in a linear fashion in a single direction.

    Attributes
    ----------
    widgets: list[WidgetCreator]
        A list of widgets that are inside the layout, which will start from the origin to the
        layout's ending point.
    """

    widgets: list[WidgetCreator]

    def get_widgets(self) -> list[Widget]:
        """
        A helper function to get the list of widgets with the correct typing hint.

        Returns
        -------
        list[Widget]
            The list of widgets as defined in `self.widgets`.
        """
        return self.widgets  # type: ignore


class Form(BaseModel):
    """
    A layout which sets a series of widgets adjacent to their respective labels.

    Attributes
    ----------
    label: str
        The description of the following widget to its side.
    widget: WidgetCreator
        The widget that is displayed in the given form.
    """

    label: str
    widget: WidgetCreator

    def get_widget(self) -> Widget:
        """
        A helper function to get the widget with the correct typing hint.

        Returns
        -------
        Widget
            The widget as defined in `self.widget`.
        """
        return self.widget  # type: ignore


class FormLayout(LayoutMeta):
    """
    A layout which widgets are adjacent to their respective labels.

    Attributes
    ----------
    forms: list[Form]
        The respective forms that compose the layout with their respective widgets and labels.
    """

    forms: list[Form]


class LayoutCreator(BaseModel):
    """
    A generator for a :class:`~foundry.gui.util.LayoutMeta`.  Creates the layout dynamically
    from its type attribute to provide it additional information required to be a subclass of
    layout.

    For example a layout of type horizontal will become a box layout, instead of a plain layout.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        return super().__init_subclass__(**kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def generate_layout(cls, v: dict) -> LayoutMeta:
        """
        The constructor for each specific layout.

        Parameters
        ----------
        v : dict
            The dictionary to create the layout.

        Returns
        -------
        LayoutMeta
            The created layout as defined by `v["type"]`

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """

        type_ = LayoutType(v["type"])
        if type_ == LayoutType.horizontal or type_ == LayoutType.verticle:
            return BoxLayout(**v)
        if type_ == LayoutType.form:
            return FormLayout(**v)
        raise NotImplementedError(f"There is no layout of type {type_}")

    @classmethod
    def validate(cls, v):
        """
        Validates that the provided object is a valid LayoutMeta.

        Parameters
        ----------
        v : dict
            The dictionary to create the layout.

        Returns
        -------
        Widget
            If validated, a layout will be created in accordance to `generate_layout`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:`~foundry.gui.util.LayoutType`.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not LayoutType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid layout type")
        return cls.generate_layout(v)


class Layout(BaseModel):
    """
    A helper class to allow for easier use of :class:`~foundry.gui.util.LayoutCreator` as
    it does not provide type hints.

    Attributes
    ----------
    layout: LayoutCreator
        The layout creator, which generates the layout automatically in accordance to layout
        creator.
    """

    layout: LayoutCreator

    def get_layout(self) -> LayoutMeta:
        """
        A helper method that provides correct typing hints for layout.

        Returns
        -------
        LayoutMeta
            The LayoutMeta as described in `self.layout`.
        """
        return self.layout  # type: ignore


def create_widget(parent: QWidget, meta: Widget) -> QWidget:
    """
    Creates a widget from a :class:`~foundry.gui.util.Widget`, providing its actual
    implementation.

    Parameters
    ----------
    parent : QWidget
        The widget which houses the widget's actions.
    meta : Widget
        The instance that holds the widget's attributes.

    Returns
    -------
    QWidget
        The created instance of a QWidget in accordance to `meta`.

    Raises
    ------
    NotImplementedError
        If the constructor does not implement a valid implementation for a given `meta.type`.
    """
    if isinstance(meta, Button):
        widget = QPushButton(meta.name)
        if meta.action is not None:
            widget.clicked.connect(getattr(parent, meta.action))  # type: ignore
    elif isinstance(meta, Spinner):
        widget = QSpinBox()
        if not meta.enabled:
            widget.setEnabled(False)
        if meta.minimum is not None:
            widget.setMinimum(meta.minimum)
        if meta.maximum is not None:
            widget.setMaximum(meta.maximum)
        if meta.hexadecimal:
            widget.setDisplayIntegerBase(16)
            widget.setPrefix("0x")
        if meta.value_change_action is not None:
            widget.valueChanged.connect(getattr(parent, meta.value_change_action))  # type: ignore
    else:
        raise NotImplementedError(f"{meta.type} is not supported")

    if meta.parent_attribute_name is not None:
        setattr(parent, meta.parent_attribute_name, widget)
    if meta.what_is_this is not None:
        widget.setWhatsThis(meta.what_is_this.description)
    return widget


def setup_description(parent: QWidget, flags: dict):
    """
    Generates any descriptions for a widget.  Most commonly the `what's this` field.

    Parameters
    ----------
    parent : QWidget
        The widget to apply the description to.
    flags : dict
        The dict that describes the description.
    """
    if "what is this" in flags:
        parent.setWhatsThis(WhatIsThis(elements=flags["what is this"]).description)


def setup_layout(parent: QWidget, flags: dict) -> QLayout:
    """
    Creates a layout from a series of flags and a parent.  The layout will pass any events
    automatically to the parent and will work identically to one created through code.

    Parameters
    ----------
    parent : QWidget
        The parent of the layout.  Typically the layout becomes the main layout of the parent.
    flags : dict
        The dict that described the layout.

    Returns
    -------
    QLayout
        The instance of the well formed layout.

    Raises
    ------
    NotImplementedError
        If the provided `meta.type` is not implemened.
    """
    meta = Layout(**flags).get_layout()

    if isinstance(meta, BoxLayout):
        if meta.type == LayoutType.horizontal:
            layout = QHBoxLayout()
        elif meta.type == LayoutType.verticle:
            layout = QVBoxLayout()
        else:
            raise NotImplementedError(f"{meta} does not support layout type of {meta.type}")

        for layout_widget in meta.get_widgets():
            layout.addWidget(create_widget(parent, layout_widget))
    elif isinstance(meta, FormLayout):
        layout = QFormLayout()

        for form in meta.forms:
            layout.addRow(form.label, create_widget(parent, form.get_widget()))
    else:
        raise NotImplementedError(f"{meta.type} is not supported")

    parent.setLayout(layout)

    return layout


def setup_widget_menu(widget: QMainWindow, flags):
    for menu_name, menu in flags["menu"].items():
        qmenu = QMenu(menu["name"])
        if menu.get("attribute", False):
            setattr(widget, f"{menu_name}_menu", qmenu)
        if "action" in menu:
            qmenu.triggered.connect(getattr(widget, menu["action"]))
        menu_type = menu["type"]

        for index, option_group in enumerate(menu["options"]):
            if index != 0:
                qmenu.addSeparator()
            if menu_type == "actions":
                for base_name, option in option_group.items():
                    name: str = option["name"]
                    action = qmenu.addAction(name)
                    if option.get("attribute", False):
                        setattr(widget, f"{base_name}_action", action)
                    if "action" in option:
                        method = getattr(widget, option["action"])
                    elif "link" in option:

                        def call_link(url: str):
                            def call_link():
                                return open_url(url)

                            return call_link

                        method = call_link(option["link"])
                    else:
                        raise NotImplementedError
                    if option.get("wrapped", False):
                        action.triggered.connect(lambda *_, m=method: m())
                    else:
                        action.triggered.connect(method)

            elif menu_type == "settings":
                for option in option_group.values():
                    name: str = option["display_name"]
                    action = qmenu.addAction(name)
                    action.setProperty(ID_PROP, option["id"])
                    action.setCheckable(True)
                    action.setChecked(SETTINGS[option["name"]])
        widget.menuBar().addMenu(qmenu)


def setup_window(widget: QMainWindow, flags):
    setup_widget_menu(widget, flags)
