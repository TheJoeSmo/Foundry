from PySide6.QtCore import QSize
from PySide6.QtGui import QMouseEvent, Qt
from PySide6.QtWidgets import QListWidget, QScrollBar, QSizePolicy, QWidget

from foundry.game.level.LevelRef import LevelRef
from foundry.gui.ContextMenu import ContextMenu


class ObjectList(QListWidget):
    def __init__(self, parent: QWidget, level_ref: LevelRef, context_menu: ContextMenu):
        super(ObjectList, self).__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        scroll_bar = QScrollBar(self)
        self.setVerticalScrollBar(scroll_bar)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWordWrap(True)

        self.setSelectionMode(self.ExtendedSelection)

        self.level_ref: LevelRef = level_ref
        self.level_ref.data_changed.connect(self.update_content)
        self.context_menu = context_menu

        self.labels = []
        self._on_selection_changed_ongoing = False
        self.itemSelectionChanged.connect(self.on_selection_changed)

        self.setWhatsThis(
            "<b>Object List</b><br/>"
            "This lists all the objects and enemies/items in the level. They appear in the order, "
            "that they are stored in the ROM as, which also decides which objects get drawn "
            "before/behind which.<br/>"
            "Enemies/items are always listed last, since they are also stored separately from the level "
            "objects.<br/><br/>"
            "Note: While Jumps are technically level objects, they are omitted here, since they are "
            "listed in a separate list below."
        )

    def sizeHint(self):
        return QSize(100, 200)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.on_right_down(event)
        else:
            return super(ObjectList, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.on_right_up(event)
        else:
            return super(ObjectList, self).mouseReleaseEvent(event)

    def on_right_down(self, event: QMouseEvent):
        item_under_mouse = self.itemAt(event.pos())

        if item_under_mouse is None:
            event.ignore()
            return

        if not item_under_mouse.isSelected():
            self.clearSelection()

            index = self.indexFromItem(item_under_mouse)

            selected_object = self.level_ref.level.get_all_objects()[index.row()]

            self.level_ref.selected_objects = [selected_object]

    def on_right_up(self, event):
        item_under_mouse = self.itemAt(event.pos())

        if item_under_mouse is None:
            event.ignore()
            return

        self.context_menu.as_list_menu().popup(event.globalPos())

    def update_content(self):
        """
        A new item has been selected, so select the new item.
        """
        prior_selection = self.currentIndex()
        currently_selected = set(obj.row() for obj in self.selectedIndexes())
        ignore_prior_selection = False

        level_objects = self.level_ref.level.get_all_objects()

        labels = [obj.name for obj in level_objects]
        if labels != self.labels:
            self.labels = labels

            self.blockSignals(True)
            self.clear()
            self.addItems(labels)

            for index, level_object in enumerate(level_objects):
                item = self.item(index)
                item.setData(Qt.UserRole, level_object)
                item.setSelected(level_object.selected)
                if level_object.selected and index not in currently_selected:
                    ignore_prior_selection = True

            self.blockSignals(False)

        has_changes = False
        for index, level_object in enumerate(level_objects):
            if level_object.selected and index not in currently_selected:
                has_changes = True
                break
        if not has_changes:
            return

        if self.selectedIndexes():
            self.scrollTo(self.selectedIndexes()[-1])

        if not ignore_prior_selection:
            self.setCurrentIndex(prior_selection)

    def selected_objects(self):
        return [self.item(index.row()).data(Qt.UserRole) for index in self.selectedIndexes()]

    def on_selection_changed(self):
        if self._on_selection_changed_ongoing:
            return

        self._on_selection_changed_ongoing = True
        self.level_ref.selected_objects = self.selected_objects()
        self._on_selection_changed_ongoing = False
