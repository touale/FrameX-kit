import inspect
import logging
import sys
from typing import TYPE_CHECKING, TextIO

import loguru

if TYPE_CHECKING:
    # avoid sphinx autodoc resolve annotation failed
    # because loguru module do not have `Logger` class actually
    from loguru import Logger, Record

logger: "Logger" = loguru.logger


class LoguruHandler(logging.Handler):  # pragma: no cover
    def emit(self, record: logging.LogRecord) -> None:
        from framex.config import settings

        msg = record.getMessage()
        if settings.log.simple_log and (
            (record.name == "ray.serve" and msg.startswith(settings.log.ignored_prefixes)) or record.name == "filelock"
        ):
            return
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, msg)


class StderrFilter:  # pragma: no cover
    def __init__(self, original_stderr: TextIO, keyword_to_filter: str):
        self.original_stderr = original_stderr
        self.keyword_to_filter = keyword_to_filter
        self._buffer = ""

    def write(self, message: str) -> None:
        self._buffer += message
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if self.keyword_to_filter not in line:
                self.original_stderr.write(line + "\n")

    def flush(self) -> None:
        if self._buffer and self.keyword_to_filter not in self._buffer:
            self.original_stderr.write(self._buffer)
        self._buffer = ""
        self.original_stderr.flush()

    def fileno(self) -> int:
        # Required for compatibility with Ray's faulthandler
        return self.original_stderr.fileno()

    def isatty(self) -> bool:
        return self.original_stderr.isatty()

    def close(self) -> None:
        self.original_stderr.close()


def default_filter(record: "Record") -> bool:
    log_level = record["extra"].get("log_level", "DEBUG")
    levelno = logger.level(log_level).no if isinstance(log_level, str) else log_level
    ingore_prefixes = ("http", "vcr")
    if record["name"] and (
        record["name"].startswith(ingore_prefixes)
        or (record["name"].startswith("sentry") and record["level"].name == "DEBUG")
    ):  # pragma: no cover
        return False

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


def setup_logger() -> None:  # pragma: no cover
    # Update log config
    import logging

    for name in logging.root.manager.loggerDict:
        if name.startswith("ray"):
            logging.getLogger(name).handlers = [LoguruHandler()]
