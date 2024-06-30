import inspect
import logging
import sys
from typing import Any

from loguru import logger

import core.utils as ut
from core.settings import settings


@ut.singleton
class LogEngine:
    def __init__(self) -> None:
        self._logger = logger
        self.setup()
        self.log_level = settings.LOG_LEVEL
        if ut.has("sqlalchemy"):
            self._configure_sqlalchemy()

    def setup(self):
        log_format = (
            "<green>[{time:YYYY-MM-DD HH:mm:ss.SSS}]</green> "
            "<level>{level: <6}</level> "
            "<cyan>{name}.py</cyan> "
            "<cyan>{line}</cyan> => "
            "<level>{message}</level>"
        )
        self._logger.add(sys.stdout, format=log_format, level="INFO")

    def get_caller_info(self, skip=3) -> dict[str, str]:
        """
        Return information about the caller.

        Reference: https://gist.github.com/techtonik/2151727

        Args:
            skip (int): Number of frames to skip when retrieving caller information. Default is 3.

            - skip=1 means "who calls me"
            - skip=2 "who calls my caller".
        """

        caller_info = {
            "package": "",
            "module": "",
            "classname": "",
            "caller": "",
            "line": "",
        }
        stack = inspect.stack()
        start = 0 + skip
        if len(stack) < start + 1:
            return caller_info
        frame = stack[start][0]

        # Get information about the caller
        module_info = inspect.getmodule(frame)
        if module_info:
            mod = module_info.__name__.split(".")
            caller_info["package"] = mod[0]
            caller_info["module"] = ".".join(mod[1:])

        # class name
        if "self" in frame.f_locals:
            caller_info["classname"] = frame.f_locals["self"].__class__.__name__

        # caller
        if frame.f_code.co_name != "<module>":  # top level usually
            caller_info["caller"] = frame.f_code.co_name

        # Line number
        caller_info["line"] = str(frame.f_lineno)

        return caller_info

    def _get_level(self, level: str) -> int:
        level_map = {
            "DEBUG": 0,
            "INFO": 1,
            "WARN": 2,
            "ERROR": 3,
            "FATAL": 4,
        }
        return level_map.get(str(level.upper()), 1)

    def log(self, level="DEBUG", *items: Any) -> None:
        if not settings.DEBUG or self._get_level(level) < self._get_level(self.log_level):
            return
        self._logger.remove()
        caller_info = self.get_caller_info()
        context = {
            "original_name": f"{caller_info['package']}.{caller_info['module']}",
            "original_line": caller_info["line"],
            "original_class": caller_info["classname"],
            "original_caller": caller_info["caller"],
        }
        log_format = (
            "<green>[{time:YYYY-MM-DD HH:mm:ss.SSS}]</green> "
            "<level>{level: <6}</level> "
            "<cyan>{extra[original_name]}.{extra[original_class]}.{extra[original_caller]}::"
            "{extra[original_line]}</cyan>  "
            ">>> <level>{message}</level>"
        )
        self._logger.add(sys.stdout, colorize=True, format=log_format, backtrace=True, diagnose=True)
        message = " ".join([str(i) for i in items])
        self._logger.bind(**context).log(level, message)

    def __call__(self, *items: Any) -> None:
        self.log("DEBUG", *items)

    def info(self, *items: Any) -> None:
        self.log("INFO", *items)

    def error(self, *items: Any) -> None:
        self.log("ERROR", *items)

    def warning(self, *items: Any) -> None:
        self.log("WARNING", *items)

    def debug(self, *items: Any) -> None:
        self.log("DEBUG", *items)

    def critical(self, *items: Any) -> None:
        self.log("CRITICAL", *items)

    def exception(self, *items: Any) -> None:
        self.log("EXCEPTION", *items)

    def _configure_sqlalchemy(self):
        from sqlalchemy import Engine, event

        # Configure SQLAlchemy to use custom logger
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(logging.INFO)

        class SQLAlchemyLogHandler(logging.Handler):
            def __init__(self, engine_instance):
                super().__init__()
                self.engine_instance = engine_instance

            def emit(self, record):
                log_entry = self.format(record)
                self.engine_instance.debug(log_entry)

        handler = SQLAlchemyLogHandler(self)
        sqlalchemy_logger.addHandler(handler)

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """
            listen for the 'before_cursor_execute' event

            Reference: https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.ConnectionEvents.before_cursor_execute
            """
            self.info("Executing SQL:\n", "```sql\n", f"{statement}", "\n```\nParameters:\n", f"{parameters}")

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """
            listen for the 'after_cursor_execute' event

            Reference: https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.ConnectionEvents.before_cursor_execute
            """
