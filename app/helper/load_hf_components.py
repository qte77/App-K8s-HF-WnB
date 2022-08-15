#!/usr/bin/env python
"""
Load components from Hugging Face or local if already present
"""
# TODO load and save locally, use save path from defaults.yml

from logging import error
from os import environ as env
from os import makedirs
from os.path import exists, join
from typing import Final

from datasets import load_dataset, load_metric
from datasets.dataset_dict import DatasetDict
from transformers import AutoModelForSequenceClassification, AutoTokenizer

if "APP_DEBUG_IS_ON" in env:
    from logging import debug

    global debug_on_global
    debug_on_global: Final = True

from .sanitize_path import sanitize_path


def get_dataset_hf(
    dataset_name: str, configuration: str = None, save_dir: str = None
) -> DatasetDict:
    """
    Load and save vanilla dataset from Hugging Face
    https://huggingface.co/docs/datasets/v1.2.1/loading_datasets.html
    https://huggingface.co/docs/datasets/loading#local-and-remote-files
    """

    dataset = DatasetDict
    msg_download = f"{configuration=} from " if configuration else ""
    save_path, path_exists = _check_and_create_path(
        f"{save_dir}/Datasets/{dataset_name}/{configuration}"
    )

    if path_exists:
        try:
            # data_files = "train"
            if debug_on_global:
                debug(f"Loading local copy of dataset from {save_path}")
            dataset = (
                load_dataset(
                    path=dataset_name,
                    name=configuration,
                    data_dir=save_path,
                    # data_files=data_files,
                )
                if configuration
                else load_dataset(path=dataset_name, data_dir=save_path)
            )
        except Exception as e:
            return e
    else:
        try:
            if debug_on_global:
                debug(f"Downloading {msg_download}dataset {dataset_name=}")
            dataset = (
                load_dataset(dataset_name, configuration)
                if configuration
                else load_dataset(dataset_name)
            )
            if debug_on_global:
                debug(f"Saving to {save_path=}")
            dataset.save_to_disk(save_path)
        except Exception as e:
            return e

    if debug_on_global:
        ds_train_slice = dataset["train"][0]
        print(f"{ds_train_slice=}")

    return dataset


def get_tokenizer_hf(
    model_name: str = None, save_dir: str = None
) -> AutoTokenizer:  # TODO check return type
    """
    Downloads tokenizer for the specified model
    A tokenizer converts the input tokens to vocabulary indices and pads the data
    """

    tokenizer = AutoTokenizer
    save_path, path_exists = _check_and_create_path(
        f"{save_dir}/Tokenizer/{model_name}"
    )

    if path_exists:
        try:
            if debug_on_global:
                debug(f"Loading local copy of tokenizer from {save_path}")
            tokenizer = AutoTokenizer.from_pretrained(save_path)
        except Exception as e:
            return e
    else:
        try:
            if debug_on_global:
                debug(f"Downloading tokenizer for {model_name=}")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name, use_fast=True, truncation=True, padding=True
            )
            if debug_on_global:
                debug(f"Saving to {save_path=}")
            tokenizer.save_pretrained(save_path)
        except Exception as e:
            return e

    if debug_on_global:
        tok_msg = "This is a test sentence."
        tok_res = tokenizer.encode(tok_msg)
        debug(f"Tokenizing '{tok_msg}': {tok_res}")

    return tokenizer


def get_model_hf(
    model_full_name: str, num_labels: int
) -> AutoModelForSequenceClassification:  # TODO check return type
    """Downloads specified model"""

    # _check_and_create_path(f"{save_dir}/Models/{modelname}")
    # try:
    # if not os.path.exists(model_dir):
    #     print(green, f'Downloading and saving model to {model_dir}')
    #     os.makedirs(model_dir)
    #     modelobj = AutoModelForSequenceClassification.from_pretrained(
    #       modelname, num_labels=num_labels)
    #     modelobj.save_pretrained(model_dir)
    # else:
    #     print(green, f'Loading model from {model_dir}')
    #     modelobj = AutoModelForSequenceClassification.from_pretrained(model_dir)
    # except Exception as e:
    # print(red, e)

    # model_dir = None; del model_dir

    # colab
    # try:
    #     if not os.path.exists(model_dir):
    #     print(green, f'Downloading and saving model to {model_dir}')
    #     os.makedirs(model_dir)
    #     modelobj = AutoModelForSequenceClassification.from_pretrained(
    #         model_name,
    #         num_labels = num_labels
    #     )
    #     modelobj.save_pretrained(model_dir)
    #     else:
    #     print(green, f'Loading model from {model_dir}')
    #     modelobj = AutoModelForSequenceClassification.from_pretrained(model_dir)
    # except Exception as e:
    #     print(red, e)

    if debug_on_global:
        debug(f"Downloading {model_full_name=} with {num_labels=}")

    return AutoModelForSequenceClassification.from_pretrained(
        model_full_name, num_labels=num_labels
    )


def get_metrics_to_load_objects_hf(metrics_to_load: list) -> list[dict]:
    """Downloads Hugging Face Metrics Builder Scripts"""

    # TODO metrics save and load locally possible ?
    # TODO error handling, what about empty metrics?

    if debug_on_global:
        debug(f"Loading HF Metrics Builder Scripts for {metrics_to_load!r}")

    metrics_loaded = []

    for met in metrics_to_load:

        if debug_on_global:
            debug(f"Trying to load {met!r}")

        try:
            metrics_loaded.append(load_metric(met))
        except Exception as e:
            # TODO handle error while loading metrics from HF
            error(e)

    return metrics_loaded


def _check_and_create_path(path_to_check: str) -> tuple[str, bool]:
    """TODO"""

    dir = sanitize_path(path_to_check)
    dir_path = join(dir["dir"], dir["base"])

    try:
        if not exists(dir_path):
            makedirs(dir_path)
            return (dir_path, False)
        else:
            return (dir_path, True)
    except Exception as e:
        return e
