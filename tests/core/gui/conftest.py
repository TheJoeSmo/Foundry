from logging import INFO, basicConfig

basicConfig(filename="tests/core/gui/logs.log", level=INFO, encoding="utf-8", filemode="w")

import foundry.core.gui  # noqa: F401, E402
