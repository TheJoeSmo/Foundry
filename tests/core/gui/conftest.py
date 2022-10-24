from logging import DEBUG, INFO, basicConfig, getLogger

basicConfig(filename="tests/core/gui/logs.log", level=DEBUG, encoding="utf-8", filemode="w")

import foundry.core.gui as gui  # noqa: E402

signal_logger = getLogger(gui.SIGNAL_LOGGER_NAME)
signal_logger.setLevel(INFO)

undo_logger = getLogger(gui.UNDO_LOGGER_NAME)
undo_logger.setLevel(DEBUG)
