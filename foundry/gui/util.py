from PySide6.QtWidgets import QMainWindow, QMenu

from foundry import open_url
from foundry.gui.settings import SETTINGS

ID_PROP = "ID"


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        item.widget().deleteLater()


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
                        action.triggered.connect(lambda *_: method())
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
