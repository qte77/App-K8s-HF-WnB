#!/usr/bin/env python
"""
Download and save components from providers, e.g. Hugging Face.

Components could be models, datasets, tokenizers, metrics etc.
"""

# TODO decorator or facade for handler functions to load provider components,
# e.g. load_hf_components

from dataclasses import dataclass
from os import environ as env
from typing import Union

from datasets import Metric
from datasets.dataset_dict import DatasetDict
from transformers import AutoModel, AutoTokenizer

from ..utils.handle_logging import debug_on_global, logging_facility
from ..utils.load_configs import get_keyfile_content
from .load_hf_components import (
    get_dataset_hf,
    get_list_of_metrics_to_load,
    get_model_hf,
    get_tokenizer_hf,
)
from .prepare_pipe_params import Parameters


@dataclass(repr=False, eq=False)  # slots only >=3.10
class Pipeline:
    """
    Holds structured data for the pipeline.

    - `parameters` as `Parameters`
    - `tokenizer` as `AutoTokenizer`
    - `dataset_tokenized` as `DatasetDict`
    - `model` as `AutoModel`
    - `metrics_loaded` as `list[Metric]`
    """

    parameters: Parameters
    tokenizer: AutoTokenizer
    dataset_tokenized: DatasetDict
    model: AutoModel
    metrics_loaded: list[Metric]


def prepare_pipe_data(parameters: Parameters) -> Pipeline:
    """
    Prepares the pipeline by loading Dataset, Tokenizer, Model and Metrics as well
    as setting parameter for the used provider in the system environment.

    Expects populated `Parameters` and returns a `Pipeline`.
    """

    _set_provider_env(parameters.sweep["provider"], parameters.provider_env)

    return _get_large_components(parameters)


def _get_large_components(parameters: Parameters) -> Pipeline:
    """
    Loads components needed for the dataclass `Pipeline`.

    * Tokenized dataset
    * Tokenizer
    * Model
    * List of metrics
    """

    dataset_plain = _get_dataset(
        parameters.dataset["dataset"],
        parameters.dataset["configuration"],
        parameters.save_dir,
    )

    tokenizer = _get_tokenizer(
        parameters.model_full_name,
        parameters.save_dir,
    )
    # tokenizer = ""

    dataset_tokenized = _get_sanitized_tokenized_dataset(
        dataset_plain,
        tokenizer,
        parameters.dataset["cols_to_tokenize"],
        parameters.dataset["cols_to_remove"],
    )
    # dataset_tokenized = ""

    num_labels = len(
        dataset_tokenized["train"].unique(parameters.dataset["col_to_rename"])
    )
    parameters.dataset["num_labels"] = num_labels
    if debug_on_global:
        logging_facility("log", f"The number of unique labels is {num_labels}")

    # paramdict.dataset["num_labels"] = 2

    model = _get_model(parameters.model_full_name, num_labels, parameters.save_dir)
    # model = ""

    metrics_loaded = _get_metrics_to_load_objects(
        parameters.metrics["metrics_to_load"], parameters.save_dir
    )
    # metrics_loaded = ""

    return Pipeline(
        parameters=parameters,
        tokenizer=tokenizer,
        dataset_tokenized=dataset_tokenized,
        model=model,
        metrics_loaded=metrics_loaded,
    )


def _get_dataset(
    name: str, configuration: str = None, save_dir: str = None
) -> Union[Exception, DatasetDict]:
    """
    Downloads the dataset by calling the appropriate provider handling function.

    To date only from Hugging Face.
    """

    return get_dataset_hf(name, configuration, save_dir)


def _get_tokenizer(model_full_name: str, save_dir: str = None) -> AutoTokenizer:
    """
    Downloads the tokenizer by calling the appropriate provider handling function.

    To date only from Hugging Face.
    """

    return get_tokenizer_hf(model_full_name, save_dir)


def _get_metrics_to_load_objects(
    metrics_to_load: list, save_dir: str = None
) -> list[Metric]:
    """
    Downloads metrics objects by calling the appropriate provider handling function.

    To date only from Hugging Face.
    """

    return get_list_of_metrics_to_load(metrics_to_load, save_dir)


def _get_model(
    model_full_name: str = None, num_labels: int = None, save_dir: str = None
):
    """
    Downloads the model by calling the appropriate provider handling function.

    To date only from Hugging Face.
    """
    return get_model_hf(model_full_name, num_labels, save_dir)


def _get_sanitized_tokenized_dataset(
    dataset_plain: DatasetDict,
    tokenizer: AutoTokenizer,
    cols_to_tokenize: list[str],
    cols_to_remove: list[str],
) -> DatasetDict:
    """
    Returns the sanitized tokenized dataset stripped of columns not needed.

    TODO save a local copy of the tokenized dataset to avoid overhead
    May not be useful inside container
    """

    if debug_on_global:
        for msg in [
            f"Tokenizing dataset with {len(cols_to_tokenize)} columns to tokenize.",
            f"Removing {cols_to_tokenize=} and {cols_to_remove=}.",
        ]:
            logging_facility("log", msg)

    try:
        ds_tokenized = (
            _get_raw_tokenized_dataset(dataset_plain, tokenizer, cols_to_tokenize)
            .remove_columns(cols_to_tokenize)
            .remove_columns(cols_to_remove)
        )
    except Exception as e:
        logging_facility("excepetion", e)
        return e

    if debug_on_global:
        ds_tokenized_train_slice = ds_tokenized["train"][0]
        logging_facility("log", f"{ds_tokenized_train_slice=}")

    return ds_tokenized


def _get_raw_tokenized_dataset(
    dataset_plain: DatasetDict, tokenizer: object, cols_to_tok: list[str]
) -> DatasetDict:
    """Returns the raw tokenized dataset with all columns"""

    def _tokenize(dataset):
        """Tokenizes the columns of `dataset` selected by `cols_to_tok`"""
        cols = [dataset[col] for col in cols_to_tok]
        return tokenizer(*cols, truncation=True)

    return dataset_plain.map(_tokenize, batched=True)


def _set_provider_env(provider: str, provider_env: dict) -> None:
    """
    Sets the environment parameters for the sweep provider including API keys.

    Sets all environment variables in upper case.
    """

    provider_label = provider.upper()

    try:
        env[f"{provider_label}_API_KEY"] = get_keyfile_content(provider)[
            f"{provider_label}_API_KEY"
        ]
        for k, v in provider_env[provider].items():
            env[k] = v
    except Exception as e:
        logging_facility("exception", e)
        return e

    if debug_on_global:
        logging_facility("log", f"Environment set for {provider_label}")
        for s in env:
            if f"{provider_label}_" in s:
                msg = f"{s}=***" if "API_KEY" in s else f"{s}={env[s]}"
                logging_facility("log", msg)
