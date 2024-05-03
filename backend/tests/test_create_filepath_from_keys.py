import json
import pytest
from pathlib import Path

from typing import List, Optional

import streamlit as st

# TODO: Add imports from frontend and labdata
SPECIES = ["Human", "Rat", "Mouse", "Fish", "Chicken", "\Chicken", "\\Chicken"]
ORIGINS = ["Primary", "iPSC"]
ORGAN_TYPES = ["Cardio", "Neuro"]
CELL_TYPES = ["Cardiospheres"]


def create_filepath_from_keys(
    input_dict,
    key_order: Optional[List[str]] = None,
    input_optionals: Optional[List[str]] = None,
    base_path: str = "./data",
) -> Path:
    """
    ATTENTION: This is just copy-pasted code from the frontend.
    """
    if key_order is None:
        key_order = [
            "species",
            "origin",
            "organType",
            "cellType",
            "experimentName",
            "influenceGroups",
            "sampleID",
            "ageDIV",
            "labDevice",
        ]
    if input_optionals is None:
        input_optionals = []

    file_path = Path(base_path)

    chosen_value = "ageNone"
    if input_dict.get("ageDAP") is not None:
        chosen_value = "DAP" + str(input_dict["ageDAP"])
    elif input_dict.get("ageDIV") is not None:
        chosen_value = "DIV" + str(input_dict["ageDIV"])

    for key in key_order:
        # Skip keys that have already been processed
        if key in ["ageDIV", "ageDAP"]:
            continue
        elif key == "influenceGroups":
            influence_groups_dict = [
                input_dict["influenceGroups"][key]
                for key in input_dict["influenceGroups"]
                if key.startswith("influence")
            ]
            # get all values from the nested dict where the key is 'name'
            influence_groups = [
                value["name"]
                for influence_group in influence_groups_dict
                for value in influence_group.values()
                if value is not None
            ]
            # make the list unique keeping the order
            unique_influence_groups = list(dict.fromkeys(influence_groups))
            file_path /= Path("_".join(unique_influence_groups))

        # Ensure the key is in the input_dict
        if key in input_dict:
            value = input_dict.get(key)

            # Check if the value is a dictionary, then concatenate nested keys
            # This is the case for the device name
            if isinstance(value, dict):
                nested_keys = list(value.keys())

                # Concatenate the values of "name" keys with an underscore
                nested_values = "_".join(
                    str(value[nested_key]["name"])
                    for nested_key in nested_keys
                    if value[nested_key] is not None and "name" in value[nested_key]
                )

                # Concatenate the nested values to the file path
                file_path /= Path(nested_values)
            else:
                # Ensure value is a string representation
                value_str = str(value)

                if key == "sampleID":
                    value_str = "sID" + value_str

                # Concatenate value to the file path
                file_path /= Path(value_str)

            # Insert the chosen value after 'experimentName'
            if key == "sampleID" and chosen_value is not None:
                file_path /= Path(chosen_value)
        elif key == "influence":
            continue
        else:
            st.error(f"Key '{key}' not found in input_dict.")
            raise KeyError(f"Key '{key}' not found in input_dict.")

    return file_path


@pytest.fixture
def input_dict():
    # load from resources file
    with open("backend/tests/resources/template_base.json", "r") as f:
        base_metadata = json.load(f)

    return base_metadata


# ORDER
# species/origin/organType/cellType/experimentName/influence/sampleID/age/labDevice


def test_smoke():
    assert True


def test_correct_working(input_dict):
    expected_output = Path(
        "./data/Human/Primary/Cardio/Cardiospheres/exp_2024-04-23_ADau-AHes_mea-lsd-neuron/Control_Bicuculline/sID1/DAP3/MEA_1-MultiWell"
    )
    assert (
        create_filepath_from_keys(input_dict).as_posix() == expected_output.as_posix()
    )


@pytest.mark.parametrize("species", SPECIES)
@pytest.mark.parametrize("origin", ORIGINS)
@pytest.mark.parametrize("organType", ORGAN_TYPES)
@pytest.mark.parametrize("cellType", CELL_TYPES)
def test_subject_specification(species, origin, organType, cellType, input_dict):
    input_dict.update(
        {
            "species": species,
            "origin": origin,
            "organType": organType,
            "cellType": cellType,
        }
    )

    expected_output = Path(
        f"./data/{species}/{origin}/{organType}/{cellType}/exp_2024-04-23_ADau-AHes_mea-lsd-neuron/Control_Bicuculline/sID1/DAP3/MEA_1-MultiWell"
    )

    assert (
        create_filepath_from_keys(input_dict).as_posix() == expected_output.as_posix()
    )


@pytest.mark.parametrize(
    "influenceGroups, expected_output",
    [
        ({}, ""),  # No influence groups
        (
            {"influenceGroup1": {"control": {"name": "Control"}}},
            "Control",
        ),  # One influence group with one influence
        (
            {
                "influenceGroup1": {
                    "control": {"name": "Control"},
                    "pharmacology": {"name": "Bicuculline"},
                }
            },
            "Control_Bicuculline",
        ),  # One influence group with multiple influences
        (
            {
                "influenceGroup1": {"control": {"name": "Control"}},
                "influenceGroup2": {"pharmacology": {"name": "Bicuculline"}},
            },
            "Control_Bicuculline",
        ),  # Multiple influence groups
        (
            {
                "influenceGroup1": {
                    "control": {"name": "Control"},
                    "radiation": {"name": "X-Ray"},
                },
                "influenceGroup2": {
                    "pharmacology": {"name": "Bicuculline"},
                    "control": {"name": "Control"},
                },
            },
            "Control_X-Ray_Bicuculline",
        ),  # Multiple influence groups with multiple influences
    ],
)
def test_influence_groups_in_filepath(influenceGroups, expected_output, input_dict):
    input_dict["influenceGroups"] = influenceGroups

    expected_filepath = Path(
        f"./data/Human/Primary/Cardio/Cardiospheres/exp_2024-04-23_ADau-AHes_mea-lsd-neuron/{expected_output}/sID1/DAP3/MEA_1-MultiWell"
    )

    assert (
        create_filepath_from_keys(input_dict).as_posix() == expected_filepath.as_posix()
    )


@pytest.mark.parametrize(
    "div_value, dap_value, div_dap_value",
    [(None, 3, "DAP3"), (4, None, "DIV4"), (4, 3, "DAP3"), (None, None, "ageNone")],
)
def test_age_specification(div_value, dap_value, div_dap_value, input_dict):
    input_dict.update(
        {
            "ageDIV": div_value,
            "ageDAP": dap_value,
        }
    )

    expected_output = Path(
        f"./data/Human/Primary/Cardio/Cardiospheres/exp_2024-04-23_ADau-AHes_mea-lsd-neuron/Control_Bicuculline/sID1/{div_dap_value}/MEA_1-MultiWell"
    )

    assert (
        create_filepath_from_keys(input_dict).as_posix() == expected_output.as_posix()
    )


def test_key_change_does_not_affect_output(input_dict):
    predefined_keys = [
        "species",
        "origin",
        "organType",
        "cellType",
        "experimentName",
        "influenceGroups",
        "sampleID",
        "ageDIV",
        "ageDAP",
        "labDevice",
    ]

    # Get a list of all keys in the dictionary that are not in the predefined set
    changeable_keys = [key for key in input_dict.keys() if key not in predefined_keys]

    for key in changeable_keys:
        output_with_original_key = create_filepath_from_keys(input_dict)

        input_dict[key] = "new_value"
        output_with_changed_key = create_filepath_from_keys(input_dict)

        # Check that the outputs are the same
        assert output_with_changed_key.as_posix() == output_with_original_key.as_posix()


@pytest.mark.parametrize(
    "required_key",
    [
        "species",
        "origin",
        "organType",
        "cellType",
        "experimentName",
        "influenceGroups",
        "sampleID",
        # "ageDIV",
        # "ageDAP",
        "labDevice",
    ],
)
def test_missing_keys(input_dict, required_key):
    del input_dict[required_key]

    # Try to get the output with the missing key
    try:
        _ = create_filepath_from_keys(input_dict)
        assert False, f"Expected KeyError for missing key: {required_key}"
    except KeyError:
        pass
