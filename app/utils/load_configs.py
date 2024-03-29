#!/usr/bin/env python
"""Load configuration files"""

from os.path import join
from typing import Any, Literal, Optional, Union

from omegaconf import OmegaConf

from .handle_logging import debug_on_global, logging_facility
from .handle_paths import sanitize_path


def load_defaults_into_load_configs_module(
    cfg_defaults_fn: str = "defaults", cfg_path: str = "app/config"
):
    """
    Load the defaults from '<cfg_defaults_fn>' and creates
    a global copy inside the module
    """

    global default_configs
    default_configs = _load_config(cfg_defaults_fn, cfg_path)

    if debug_on_global:
        logging_facility("log", f"{default_configs=}")


def get_defaults(key_to_search_and_return: str) -> str:
    """
    Searches for '<key_to_search_and_return>' inside 'defaults.yml'
    and returns its value if found
    """
    return default_configs[key_to_search_and_return]


def get_config_content(
    cfg_filename_ex_ext: str = "defaults", cfg_path: str = "app/config"
) -> dict[str, str]:
    """Returns config objects"""

    # FIXME catch
    if debug_on_global:
        defaults_dbg_msg = f"'{cfg_filename_ex_ext}' found in defaults."
        if _check_or_get_default("config_fn", cfg_filename_ex_ext):
            logging_facility("log", defaults_dbg_msg)
        else:
            logging_facility(
                "log", f"No {defaults_dbg_msg} Trying to find the file anyway."
            )

    return _load_config(cfg_filename_ex_ext, cfg_path)


def get_keyfile_content(provider: str = "wandb") -> dict:
    """Returns keyfile objects. Only WandB implemented !"""

    if not provider.casefold() == "wandb":
        logging_facility("error", NotImplementedError)
        return NotImplementedError

    try:
        # TODO handle multiple keyfiles
        keyfile_default = "~/wandb.key.yml" if provider == "wandb" else "~/key.yml"
        keyfiles = default_configs.get("keyfiles", keyfile_default)
        keyfile = sanitize_path(keyfiles[provider])
        if debug_on_global:
            logging_facility("log", f"{keyfile=}")
        return _load_config(keyfile["base"], keyfile["dir"])
    except Exception as e:
        logging_facility("exception", e)
        return e


def _load_config(
    cfg_filename_ex_ext: str = "defaults", cfg_path: str = "app/config"
) -> Union[dict[str, Any], Exception]:
    """
    Loads and returns a config.

    TODO Only accepts .yml extension right now. Account for .yaml too.
    """

    if debug_on_global:
        logging_facility("log", f"Loading {cfg_filename_ex_ext=}")
    try:
        # TODO sanitization of yml extension.
        config = OmegaConf.load(join(cfg_path, f"{cfg_filename_ex_ext}.yml"))
        return OmegaConf.to_object(config)
    except Exception as e:
        logging_facility("exception", e)
        return e


# FIXME refactor check and get out
def _check_or_get_default(
    cfg_value_to_search: str = None,
    mode_check_get: Optional[Literal["check", "get"]] = "check",
) -> Union[bool, str, ValueError]:
    """Checks whether a default exists or returns it if 'get' is provided"""

    if mode_check_get not in ["check", "get"]:
        mode_check_get = "check"

    if cfg_value_to_search:
        values_exists = default_configs.__contains__(cfg_value_to_search)
        if mode_check_get == "check":
            return values_exists
        elif values_exists:
            return default_configs[cfg_value_to_search]
        else:
            logging_facility("error", ValueError)
            return ValueError
    else:
        return default_configs
