from __future__ import annotations

import json
import logging
import logging.config
import os
from pathlib import Path
from typing import Any
from typing import List

import urllib3
from frinx.common.logging import LOGGING_CONFIG
from pydantic import BaseModel
from pydantic import Field
from urllib3.exceptions import InsecureRequestWarning

LOGGING_CONFIG_ENV: str = "LOG_CFG"


class Verbose(BaseModel):
    format: str = Field(
        default="%(asctime)s | %(threadName)s | %(levelname)s | %(name)s.%(funcName)s | %(message)s"
    )
    datefmt: str = Field(default="%F %T")


class Formatters(BaseModel):
    verbose: Verbose = Field(default=Verbose())


class Console(BaseModel):
    class_: str = Field(default="logging.StreamHandler", alias="class")
    level: str = Field(default="DEBUG")
    formatter: str = Field(default="verbose")


class File(BaseModel):
    class_: str = Field(default="logging.handlers.RotatingFileHandler", alias="class")
    filename: str = Field(default="workers.log")
    maxBytes: int = Field(default=10485760)
    backupCount: int = Field(default=10)
    level: str = Field(default="INFO")
    formatter: str = Field(default="verbose")


class Handlers(BaseModel):
    console: Console = Field(default=Console())
    file: File = Field(default=File())


class Urllib3(BaseModel):
    level: str = Field(default="INFO")


class Loggers(BaseModel):
    urllib3: Urllib3 = Field(default=Urllib3())


class Root(BaseModel):
    level: str = Field(default="NOTSET")
    handlers: List[str] = Field(default=["console", "file"])


class LoggerConfig(BaseModel):
    version: int = Field(default=1)
    formatters: Formatters = Field(default=Formatters())
    handlers: Handlers = Field(default=Handlers())
    loggers: Loggers = Field(default=Loggers())
    root: Root = Field(default=Root())
    disable_existing_loggers: bool = Field(default=False)


def configure_logging(model: LoggerConfig | dict[str, Any] | str | None = None) -> None:
    match model:
        case str():
            logging.config.dictConfig(json.loads(model))
        case dict():
            logging.config.dictConfig(model)
        case LoggerConfig():
            logging.config.dictConfig(json.loads(model.json(by_alias=True)))
        case None:
            logging.config.dictConfig(json.loads(LoggerConfig().json(by_alias=True)))


def configure_logging_from_file(
    logging_config_env: str = LOGGING_CONFIG_ENV, logging_config: Path = LOGGING_CONFIG
) -> None:
    """
    Configure the logging using a config file, this function should be called as early as
    possible, even before our imports.
    An environment variable is used if set, even if it points to a non-existent config file.
    Paths can be either absolute or relative.
    Disable urllib3.InsecureRequestWarning to not flood logs with requests to uniconfig.
    Args:
        logging_config_env: an environment variable that contains a path
        logging_config: a path to a logging config JSON file
    """

    print(logging_config)

    override = os.getenv(logging_config_env)

    if override is not None:
        config_file = Path(override)
    else:
        config_file = logging_config

    if config_file.exists():
        with config_file.open() as file:
            config = json.load(file)
            logging.config.dictConfig(config)
    else:
        raise FileNotFoundError("Couldn't configure the logger using %s", repr(config_file))

    urllib3.disable_warnings(InsecureRequestWarning)
