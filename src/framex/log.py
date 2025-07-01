import sys
from typing import TYPE_CHECKING

import loguru

if TYPE_CHECKING:
    # avoid sphinx autodoc resolve annotation failed
    # because loguru module do not have `Logger` class actually
    from loguru import Logger, Record

logger: "Logger" = loguru.logger


# class LoguruHandler(logging.Handler):  # pragma: no cover
#     def emit(self, record: logging.LogRecord):
#         try:
#             level = logger.level(record.levelname).name
#         except ValueError:
#             level = record.levelno

#         frame, depth = inspect.currentframe(), 0
#         while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
#             frame = frame.f_back
#             depth += 1

#         logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def default_filter(record: "Record"):
    log_level = record["extra"].get("log_level", "DEBUG")
    levelno = logger.level(log_level).no if isinstance(log_level, str) else log_level
    return record["level"].no >= levelno


default_format: str = (
    "<g>{time:MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "<c><u>{name}</u></c> | "
    # "<c>{function}:{line}</c>| "
    "{message}"
)

logger.remove()
logger_id = logger.add(
    sys.stdout,
    level=0,
    diagnose=False,
    filter=default_filter,
    format=default_format,
)

__autodoc__ = {"logger_id": False}
