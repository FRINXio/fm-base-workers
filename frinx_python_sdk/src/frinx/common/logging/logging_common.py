import json
import logging
import logging.config
import os
from pathlib import Path

import urllib3
from frinx.common.logging import LOGGING_CONFIG
from urllib3.exceptions import InsecureRequestWarning

LOGGING_CONFIG_ENV: str = "LOG_CFG"


def configure_logging(
    logging_config_env: str = LOGGING_CONFIG_ENV, logging_config: Path = LOGGING_CONFIG
) -> None:
    """
    Configure the logging using a config file, this function should be called as early as
    possible, even before our imports.
    An environment variable is used if set, even if it points to a non-existent config file.
    Paths can be either absolute or relative.
    Disable urllib3.InsecureRequestWarning to not to flood logs with requests to uniconfig.
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
        with config_file.open() as f:
            config = json.load(f)
            logging.config.dictConfig(config)
    else:
        raise FileNotFoundError("Couldn't configure the logger using %s", repr(config_file))

    urllib3.disable_warnings(InsecureRequestWarning)
