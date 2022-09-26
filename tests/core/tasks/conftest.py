from logging import DEBUG, basicConfig

basicConfig(filename="tests/core/tasks/logs.log", level=DEBUG, encoding="utf-8", filemode="w")

import foundry.core.tasks  # noqa: F401, E402
