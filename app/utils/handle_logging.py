#!/usr/bin/env python
""""
Offers logging facilities.

- Load [logger_name] from [root]/[config_path]/[config_fn]
- Logging functions `logger`, `metrics`, `analytics`
"""

from logging import getLogger, root
from logging.config import fileConfig
from os.path import abspath, dirname, exists, join, split
from sys import _getframe
from typing import Final

logger_cfglog = getLogger(__name__)
logging_types: Final = {
    "log": "debug",
    "warn": "warning",
    "error": "error",
    "exception": "exception",
    "metrics": "debug",
    "analytics": "debug",
}


def toggle_global_debug_state(toggle_debug: bool = False):
    """Toggle `global debug_on_global` to `debug_on`"""

    global debug_on_global
    debug_on_global = toggle_debug


def configure_logger(config_fn: str = "logging.conf", config_path: str = "config"):
    """Loads a logger configuration from the provided config file.

    The path to the config is constructed from 'root/[config_path]/[config_fn]'.
    See Python documentation for [logging](\
https://docs.python.org/3/library/logging.html\
) and [logging.config.fileConfig](\
https://docs.python.org/3/library/logging.config.html#logging.config.fileConfig\
) as well as the [Logging HOWTO](https://docs.python.org/3/howto/logging.html) and \
the [Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html).
    """

    abs_path = split(dirname(abspath(__file__)))[0]
    abs_path = join(abs_path, config_path, config_fn)

    if not exists(abs_path):
        if debug_on_global:
            logger_cfglog.error(f"Could not find config in {abs_path=}")
        return FileNotFoundError

    try:
        fileConfig(abs_path)
    except Exception as e:
        logger_cfglog.exception(e)
        return e


def logging_facility(log_type: str, log_message: str):
    """
    TODO Description: Offers logging.

    Accepts the following logging types:

    log, warn, error, exception, metrics, analytics
    """

    if _check_log_type_is_valid(log_type):
        try:
            _log_by_name_and_type(_get_log_caller(), log_type, log_message)
        except Exception as e:
            logger_cfglog.exception(e)
            return e
    else:
        return ValueError


def _check_log_type_is_valid(log_type) -> bool:
    """
    TODO
    """

    log_type_is_valid = log_type in logging_types.keys()
    if not log_type_is_valid and debug_on_global:
        logger_cfglog.error(f"{log_type=} not in pre-defined logging_types")
    return log_type_is_valid


def _get_log_caller():
    """
    TODO
    """

    # getframe of parent 2 because called by function
    caller = _getframe(2).f_globals["__name__"]
    if caller not in root.manager.loggerDict.keys():
        _create_logger_in_root_dict(caller)
    return caller


def _create_logger_in_root_dict(logger_name: str):
    """
    TODO Description: Logs with dynamic logger and creates logger if not present
    """

    try:
        getLogger(logger_name)
    except Exception as e:
        logger_cfglog.exception(e)
        return e


# FIXME use other way to dynamically call logger functions
# use logger.adapter() instead of eval ?
# https://towardsdatascience.com/8-advanced-python-logging-features-that-you-shouldnt-miss-a68a5ef1b62d
def _log_by_name_and_type(logger_name: str, log_type: str, log_message: str):
    """
    TODO Description: Logs with dynamic logger and creates logger if not present
    """

    if _check_log_type_is_valid(log_type):

        logger = f'root.manager.loggerDict["{logger_name}"]'
        logfun = f'{logging_types[log_type]}("{log_message}")'

        try:
            eval(f"{logger}.{logfun}")
        except Exception as e:
            logger_cfglog.exception(e)
            return e
    else:
        return ValueError
