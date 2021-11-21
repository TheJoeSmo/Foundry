from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QIcon, QImage, QPixmap, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from foundry import data_dir, icon
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.objects.EnemyItem import MASK_COLOR
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.HorizontalLine import HorizontalLine
from foundry.gui.settings import (
    GUI_STYLE,
    RESIZE_LEFT_CLICK,
    RESIZE_RIGHT_CLICK,
    SETTINGS,
    load_settings,
    save_settings,
)
from foundry.smb3parse.constants import (
    POWERUP_FIREFLOWER,
    POWERUP_FROG,
    POWERUP_HAMMER,
    POWERUP_MUSHROOM,
    POWERUP_RACCOON,
    POWERUP_TANOOKI,
)

load_settings()

POWERUPS_NAME = 0
POWERUPS_X = 1
POWERUPS_Y = 2
POWERUPS_VALUE = 3
POWERUPS_PWING = 4
POWERUPS = [
    ("Small Mario", 32, 53, 0, False),
    ("Big Mario", 6, 48, POWERUP_MUSHROOM, False),
    ("Raccoon Mario", 57, 53, POWERUP_RACCOON, False),
    ("Fire Mario", 16, 53, POWERUP_FIREFLOWER, False),
    ("Tanooki Mario", 54, 53, POWERUP_TANOOKI, False),
    ("Frog Mario", 56, 53, POWERUP_FROG, False),
    ("Hammer Mario", 58, 53, POWERUP_HAMMER, False),
    # Even though P-Wing can *technically* be combined, it only really works with Raccoon and Tanooki suit
    ("Raccoon Mario with P-Wing", 55, 53, POWERUP_RACCOON, True),
    ("Tanooki Mario with P-Wing", 55, 53, POWERUP_TANOOKI, True),
]

png = QImage(str(data_dir / "gfx.png"))
png.convertTo(QImage.Format_RGB888)


class SettingsDialog(CustomDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent, "Settings")

        mouse_box = QGroupBox("Mouse", self)
        mouse_box.setLayout(QVBoxLayout())

        label = QLabel("Scroll objects with mouse wheel:")
        label.setToolTip("Select an object and scroll up and down to change its type.")
        self._scroll_check_box = QCheckBox("Enabled")
        self._scroll_check_box.setChecked(SETTINGS["object_scroll_enabled"])
        self._scroll_check_box.toggled.connect(self._update_settings)

        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(label)
        scroll_layout.addStretch(1)
        scroll_layout.addWidget(self._scroll_check_box)

        label = QLabel("Show object names on hover:")
        label.setToolTip(
            "When hovering your cursor over an object in a level, its name and position is shown in a tooltip."
        )
        self._tooltip_check_box = QCheckBox("Enabled")
        self._tooltip_check_box.setChecked(SETTINGS["object_tooltip_enabled"])
        self._tooltip_check_box.toggled.connect(self._update_settings)

        tooltip_layout = QHBoxLayout()
        tooltip_layout.addWidget(label)
        tooltip_layout.addStretch(1)
        tooltip_layout.addWidget(self._tooltip_check_box)

        self.lmb_radio = QRadioButton("Left Mouse Button")
        rmb_radio = QRadioButton("Right Mouse Button")

        self.lmb_radio.setChecked(SETTINGS["resize_mode"] == RESIZE_LEFT_CLICK)
        rmb_radio.setChecked(SETTINGS["resize_mode"] == RESIZE_RIGHT_CLICK)

        self.lmb_radio.toggled.connect(self._update_settings)

        radio_group = QButtonGroup()
        radio_group.addButton(self.lmb_radio)
        radio_group.addButton(rmb_radio)

        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel("Object resize mode:"))
        resize_layout.addStretch(1)
        resize_layout.addWidget(self.lmb_radio)
        resize_layout.addWidget(rmb_radio)

        mouse_box.layout().addLayout(scroll_layout)
        mouse_box.layout().addLayout(tooltip_layout)
        mouse_box.layout().addLayout(resize_layout)

        # -----------------------------------------------
        # GUI theme section

        self.gui_style_box = QGroupBox("GUI", self)
        self.gui_style_hbox = QHBoxLayout(self.gui_style_box)
        self.gui_style_hbox.addWidget(QLabel("Style:"))
        self.gui_style_combo_box = QComboBox()
        self.gui_style_hbox.addWidget(self.gui_style_combo_box)

        for gui_style in GUI_STYLE.keys():
            self.gui_style_combo_box.addItem(gui_style.capitalize())
        self.gui_style_combo_box.setCurrentIndex(list(GUI_STYLE.keys()).index(SETTINGS["gui_style"]))
        self.gui_style_combo_box.currentIndexChanged.connect(self._update_settings)

        # -----------------------------------------------
        # emulator command

        self.emulator_command_input = QLineEdit(self)
        self.emulator_command_input.setPlaceholderText("Path to emulator")
        self.emulator_command_input.setText(SETTINGS["instaplay_emulator"])

        self.emulator_command_input.textChanged.connect(self._update_settings)

        self.emulator_path_button = QPushButton(icon("folder.svg"), "", self)
        self.emulator_path_button.pressed.connect(self._get_emulator_path)

        self.command_arguments_input = QLineEdit(self)
        self.command_arguments_input.setPlaceholderText("%f")
        self.command_arguments_input.setText(SETTINGS["instaplay_arguments"])

        self.command_arguments_input.textEdited.connect(self._update_settings)

        self.command_label = QLabel()

        command_box = QGroupBox("Emulator", self)
        command_layout = QVBoxLayout(command_box)

        command_layout.addWidget(QLabel('Emulator command or "path to exe":'))

        command_input_layout = QHBoxLayout()
        command_input_layout.addWidget(self.emulator_command_input)
        command_input_layout.addWidget(self.emulator_path_button)

        command_layout.addLayout(command_input_layout)
        command_layout.addWidget(QLabel("Command arguments (%f will be replaced with rom path):"))
        command_layout.addWidget(self.command_arguments_input)
        command_layout.addWidget(QLabel("Command used to play the rom:"))
        command_layout.addWidget(self.command_label)

        command_layout.addWidget(HorizontalLine())

        command_layout.addWidget(QLabel("Power up of Mario when playing level:"))
        self.powerup_combo_box = QComboBox()

        for name, x, y, value, p_wing in POWERUPS:
            powerup_icon = self._load_from_png(x, y)

            self.powerup_combo_box.addItem(powerup_icon, name)

        self.powerup_combo_box.currentIndexChanged.connect(self._update_settings)
        self.powerup_combo_box.setCurrentIndex(SETTINGS["default_powerup"])

        label = QLabel("Start with invincibility:")
        label.setToolTip("The player will start with star power.")
        self.powerup_star = QCheckBox("Enabled")
        self.powerup_star.setIcon(self._load_from_png(5, 48))
        self.powerup_star.setChecked(SETTINGS["default_power_has_star"])
        self.powerup_star.toggled.connect(self._update_settings)

        powerup_star_layout = QHBoxLayout()
        powerup_star_layout.addWidget(label)
        powerup_star_layout.addStretch(1)
        powerup_star_layout.addWidget(self.powerup_star)

        label = QLabel("Starting World:")
        label.setToolTip("The world that the player starts inside.")
        self.starting_world = QSpinBox(self)
        self.starting_world.setRange(1, 9)
        self.starting_world.setValue(SETTINGS["default_starting_world"])
        self.starting_world.valueChanged.connect(self._update_settings)

        starting_world_layout = QHBoxLayout()
        starting_world_layout.addWidget(label)
        starting_world_layout.addStretch(1)
        starting_world_layout.addWidget(self.starting_world)

        command_layout.addWidget(self.powerup_combo_box)
        command_layout.addLayout(powerup_star_layout)
        command_layout.addLayout(starting_world_layout)

        # ----------------------

        layout = QVBoxLayout(self)
        layout.addWidget(mouse_box)
        layout.addWidget(self.gui_style_box)
        layout.addWidget(command_box)

        self.update()

    def update(self):
        self.command_label.setText(f" > {SETTINGS['instaplay_emulator']} {SETTINGS['instaplay_arguments']}")

    def _update_settings(self, _):
        SETTINGS["instaplay_emulator"] = self.emulator_command_input.text()
        SETTINGS["instaplay_arguments"] = self.command_arguments_input.text()

        if self.lmb_radio.isChecked():
            SETTINGS["resize_mode"] = RESIZE_LEFT_CLICK
        else:
            SETTINGS["resize_mode"] = RESIZE_RIGHT_CLICK

        # setup style sheets
        SETTINGS["gui_style"] = self.gui_style_combo_box.currentText().upper()
        GUI_STYLE[SETTINGS["gui_style"]](self.parent())

        SETTINGS["object_scroll_enabled"] = self._scroll_check_box.isChecked()
        SETTINGS["object_tooltip_enabled"] = self._tooltip_check_box.isChecked()

        SETTINGS["default_powerup"] = self.powerup_combo_box.currentIndex()
        if hasattr(self, "powerup_star"):
            SETTINGS["default_power_has_star"] = self.powerup_star.isChecked()
        if hasattr(self, "starting_world"):
            SETTINGS["default_starting_world"] = self.starting_world.value()

        self.update()

    def _get_emulator_path(self):
        path_to_emulator, _ = QFileDialog.getOpenFileName(self, caption="Select emulator executable")

        if not path_to_emulator:
            return

        self.emulator_command_input.setText(path_to_emulator)

    @staticmethod
    def _load_from_png(x: int, y: int) -> QIcon:
        image = png.copy(QRect(x * Block.SIDE_LENGTH, y * Block.SIDE_LENGTH, Block.SIDE_LENGTH, Block.SIDE_LENGTH))
        mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
        image.setAlphaChannel(mask)

        pixmap = QPixmap.fromImage(image)
        icon_from_png = QIcon(pixmap)

        return icon_from_png

    def on_exit(self):
        save_settings()

        super(SettingsDialog, self).on_exit()
