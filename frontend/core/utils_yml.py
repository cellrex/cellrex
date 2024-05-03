"""
This module contains functions for parsing YAML files
describing specific data used in the lab.
"""

from typing import Dict, Union

import yaml
import requests

from core.utils_labdata import PrefillDict, PrefillList


def custom_list_constructor(loader, node):
    # Convert YAML list into an instance of CustomList
    return PrefillList(loader.construct_sequence(node, deep=True))


def custom_dict_constructor(loader, node):
    # Convert YAML dict into an instance of CustomDict
    return PrefillDict(loader.construct_mapping(node, deep=True))


def parse_labdata(
    labdata_file: str,
) -> Dict[str, Union[PrefillDict, PrefillList]]:
    # Add the custom constructor to the YAML loader
    yaml.SafeLoader.add_constructor("tag:yaml.org,2002:seq", custom_list_constructor)
    yaml.SafeLoader.add_constructor("tag:yaml.org,2002:map", custom_dict_constructor)

    # Get the YAML file from the server
    response = requests.get(labdata_file)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            data = yaml.safe_load(response.text)
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse {labdata_file}: {exc}")
    else:
        print(f"Failed to get {labdata_file}: {response.status_code}")
        data = {}

    # Change type of top-level mapping
    labdata: Dict[str, Union[PrefillDict, PrefillList]] = dict(data)

    return labdata
