from typing import Any, Dict

import streamlit as st
from core.utils import (
    ANTIBODY_CONJUGATED,
    ANTIBODY_PRIMARY,
    ANTIBODY_SECONDARY,
    DEVICE_MEA,
    DEVICE_MICROSCOPE,
    DEVICES,
    DYE_CA2_IMAGING,
    DYE_OTHER,
    MAGNIFICATIONS,
    MEA_CHIP_TYPE,
    MICROSCOPE_TASKS,
)


def session_device_component(experiment_data: Dict[str, Any]):
    experiment_data["labDeviceType"] = st.radio(
        "Device",
        options=DEVICES,
        horizontal=True,
        label_visibility="collapsed",
        index=DEVICES.getindexdefault("labDeviceType", experiment_data),
    )

    if experiment_data.get("labDevice") is None:
        experiment_data["labDevice"] = {}

    match experiment_data["labDeviceType"]:
        case "Microscope":
            microscope_device_component(experiment_data)
            experiment_data["labDevice"].pop("mea", None)
        case "MEA":
            mea_device_component(experiment_data)
            experiment_data["labDevice"].pop("microscope", None)


def microscope_device_component(experiment_data):
    if experiment_data["labDevice"].get("microscope") is None:
        device_dict = experiment_data["labDevice"]["microscope"] = {}
    else:
        device_dict = experiment_data["labDevice"]["microscope"]

    device_dict["type"] = "microscope"

    device_dict["name"] = st.selectbox(
        "Lab device",
        options=DEVICE_MICROSCOPE,
        index=DEVICE_MICROSCOPE.getindexdefault("name", device_dict),
    )
    device_dict["magnification"] = st.multiselect(
        "Magnification",
        options=MAGNIFICATIONS,
        default=MAGNIFICATIONS.getlistdefault("magnification", device_dict),
    )  # (multiselect for confocal lb)

    # CA2+Imaging (CA2 dyes) IF-staining (antibodies, other dyes)
    device_dict["task"] = st.radio(
        "Task",
        options=MICROSCOPE_TASKS,
        horizontal=True,
        index=MICROSCOPE_TASKS.getindexdefault("task", device_dict),
    )

    match device_dict["task"]:
        case "Brightfield":
            st.write(
                "You are choosing :red[Brightfield-imaging] for which "
                "no further options are available."
            )
            # If influence is not yet defined in the template, create a new dict
            if device_dict.get("brightfield") is None:
                case_dict = device_dict["brightfield"] = {}
            else:
                case_dict = device_dict["brightfield"]

            device_dict.pop("ca2Imaging", None)
            device_dict.pop("ifStaining", None)

            # Components

        case "CA2+Imaging":
            # If task is not yet defined in the template, create a new dict
            if device_dict.get("ca2Imaging") is None:
                case_dict = device_dict["ca2Imaging"] = {}
            else:
                case_dict = device_dict["ca2Imaging"]

            device_dict.pop("brightfield", None)
            device_dict.pop("ifStaining", None)

            # Components
            case_dict["dye"] = st.selectbox(
                "Calcium imaging dyes",
                options=DYE_CA2_IMAGING,
                index=DYE_CA2_IMAGING.getindexdefault("dye", case_dict),
                key="dye_cai",
            )

        case "IF-staining":
            if_staining_component(device_dict)

            device_dict.pop("brightfield", None)
            device_dict.pop("ca2Imaging", None)


def if_staining_component(device_dict):
    # If task is not yet defined in the template, create a new dict
    if device_dict.get("ifStaining") is None:
        case_dict = device_dict["ifStaining"] = {}
    else:
        case_dict = device_dict["ifStaining"]

    # Components
    case_dict["numAntibodies"] = st.number_input(
        "Enter the number of used antibodies",
        min_value=0,
        max_value=5,
        value=case_dict.get("numAntibodies", 0),
        step=1,
    )

    # Initialize containers dynamically
    containers = [st.container() for _ in range(case_dict.get("numAntibodies", 0))]
    containers_keys = [f"antibodyGroup{i}" for i in range(1, len(containers) + 1)]
    if case_dict.get("antibodyGroups") is None:
        case_dict["antibodyGroups"] = {}

    def antibody_specification_component(case_dict: Dict[str, Any], key):
        if case_dict["antibodyGroups"].get(key) is None:
            antibody_group_dict = case_dict["antibodyGroups"][key] = {}
        else:
            antibody_group_dict = case_dict["antibodyGroups"][key]
        col_container = container.columns(2)
        antibody_group_dict["prim"] = col_container[0].selectbox(
            "primary antibody",
            options=ANTIBODY_PRIMARY,
            index=ANTIBODY_PRIMARY.getindexdefault(f"prim", antibody_group_dict),
            key=f"{key}Prim",
        )
        antibody_group_dict["sec"] = col_container[1].selectbox(
            "secondary antibody",
            options=ANTIBODY_SECONDARY,
            index=ANTIBODY_PRIMARY.getindexdefault(f"sec", antibody_group_dict),
            key=f"{key}Sec",
        )
    # Use the containers as needed
    for container, key in zip(containers, containers_keys):
        with container:
            st.write(f":red[ANTIBODY {''.join(filter(str.isdigit, key))}]")
            antibody_specification_component(
                 case_dict, key=key
            )

    # Remove antibody groups that are not selected anymore
    for key in set(case_dict["antibodyGroups"].keys()).difference(containers_keys):
        case_dict["antibodyGroups"].pop(key, None)

    st.write("###### General")
    case_dict["abCon"] = st.selectbox(
        "Conjugated antibodies",
        options=ANTIBODY_CONJUGATED,
        index=ANTIBODY_CONJUGATED.getindexdefault("abCon", case_dict),
        key="ab_con",
    )
    case_dict["dyeOth"] = st.selectbox(
        "Other dyes",
        options=DYE_OTHER,
        key="dye_oth",
        index=DYE_OTHER.getindexdefault("dyeOth", case_dict),
    )


def mea_device_component(experiment_data):
    if experiment_data["labDevice"].get("mea") is None:
        case_dict = experiment_data["labDevice"]["mea"] = {}
    else:
        case_dict = experiment_data["labDevice"]["mea"]

    case_dict["type"] = "mea"

    case_dict["type"] = "MEA"

    case_dict["name"] = st.selectbox(
        "Lab device",
        options=DEVICE_MEA,
        index=DEVICE_MEA.getindexdefault("name", case_dict),
    )
    case_dict["chipType"] = st.selectbox(
        "Chip type",
        options=MEA_CHIP_TYPE,
        index=MEA_CHIP_TYPE.getindexdefault("chipType", case_dict),
    )
    case_dict["chipId"] = st.text_input(
        "Chip ID",
        value=case_dict.get("chipId"),
    )

    col_mea = st.columns(2)
    case_dict["recDur"] = col_mea[0].number_input(
        "Recording duration (in seconds)",
        min_value=0,
        max_value=100000,
        value=case_dict.get("recDur", 0),
        step=1,
        key="mea_duration",
    )
    case_dict["rate"] = col_mea[1].number_input(
        "Sample rate (in Hz)",
        min_value=0,
        max_value=100000,
        value=case_dict.get("rate", 0),
        step=1,
        key="mea_rate",
    )
