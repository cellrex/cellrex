import json
import time
import urllib.parse
from typing import Dict, Optional

import requests
import streamlit as st
from core.utils_json import DateTimeEncoder
from core.utils_yml import parse_labdata

BASE_URL_STATIC = "http://cellrex-backend:8000"
BASE_URL_API = "http://cellrex-backend:8000/v1"


def read_protocol_file(protocol_file):
    url = f"{BASE_URL_API}/{protocol_file}"

    response = requests.get(url)

    if response.status_code == 200:
        protocol = response.text
    else:
        raise FileNotFoundError(f"File {protocol_file} not found.")

    # TODO: Add type hinting for yaml files:
    # https://stackoverflow.com/questions/61483082/what-is-the-proper-way-to-add-type-hints-after-loading-a-yaml-file
    # Maybe add pydantic or dataclasses for these variables?

    return protocol


def get_request(
    route: str,
    *endpoint: str,
    parameter: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> dict:
    endpoint = [str(ep) for ep in endpoint]

    url = f"{BASE_URL_API}/{route}/{'/'.join(endpoint)}"
    if parameter is not None:
        # Use urlencode to convert the dictionary into a query string
        query_string = urllib.parse.urlencode(parameter)
        url += f"?{query_string}"
    response = requests.get(url, timeout=timeout)
    return response


def post_request(
    route: str,
    *endpoint: str,
    parameter: Optional[Dict[str, str]] = None,
    data: dict,
    timeout: int = 10,
) -> dict:
    endpoint = [str(ep) for ep in endpoint]

    url = f"{BASE_URL_API}/{route}/{'/'.join(endpoint)}"

    if parameter is not None:
        # Use urlencode to convert the dictionary into a query string
        query_string = urllib.parse.urlencode(parameter)
        url += f"?{query_string}"

    response = requests.post(url, json=data, timeout=timeout)
    return response


def get_labdata():
    url = f"{BASE_URL_STATIC}/config/labdata.yml"
    dummy_url = f"{BASE_URL_STATIC}/static/labdata_dummy.yml"

    response = requests.get(url)

    if response.status_code == 200:
        labdata = parse_labdata(url)
    else:
        labdata = parse_labdata(dummy_url)

    # TODO: Add type hinting for yaml files:
    # https://stackoverflow.com/questions/61483082/what-is-the-proper-way-to-add-type-hints-after-loading-a-yaml-file
    # Maybe add pydantic or dataclasses for these variables?

    # Create variables programmatically
    for key, value in labdata.items():
        globals()[key] = value


get_labdata()  # Load labdata from backend for import into frontend


def get_file_paths_of_existing_hash(hash):
    result = get_request("biofiles", "hash", hash)
    paths = []
    if result.status_code == 200:
        paths = [dic["filepath"] for dic in result.json()]
    return (len(paths) > 0), paths


def check_existence_of_filepath(path):
    result = get_request("biofiles", "path", path)
    paths = []
    if result.status_code != 404:
        paths = [dic["filepath"] for dic in result.json()]
    return len(paths) > 0


def get_hash_calc(filename: str):
    hash_info = None
    while hash_info is None:
        response = get_request("filemanagement", "hash", filename)

        match response.status_code:
            case 200:
                return response.json()["data"]["hash"]
            case 404:
                time.sleep(2)

        st.empty()  # to break loop on streamlit reload

    return hash_info


def check_backend():
    response = get_request("biofiles", "check", "database")
    if response.status_code == 200:
        return True
    return False


def create_db_entry(path_to_filename, experiment_data, file_size, file_hash):
    response = post_request(
        "biofiles",
        data={
            "filecontext": json.loads(
                json.dumps(experiment_data, cls=DateTimeEncoder),
            ),
            "filepath": str(path_to_filename),
            "filesize": file_size,
            "filehash": file_hash,
            "filetype": path_to_filename.suffix,
        },
    )

    if response.status_code == 201:
        st.success("Entry created successfully.")
        return True
    else:
        st.error(f"Error creating entry with status code: {response.status_code}")
        if response.status_code == 422:
            st.info("Please check whether all mandatory fields have been filled in.")
        return False


def create_demo_files(path, num_files=1, file_size_in_bytes=1024):
    # Total filesize fits not perfectly file_size_in_bytes
    for i in range(1, num_files + 1):
        filename, first_line = f"demofile{i}.txt", f"Content for file {i}\n"
        with open((path / filename).as_posix(), "w") as file:
            file.write(first_line)
            remaining_size = file_size_in_bytes - len(first_line)
            file.write("\n".join(["A" * 80] * (remaining_size // 80)) + "\n")
