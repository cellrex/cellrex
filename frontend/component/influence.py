from typing import Any, Dict

import streamlit as st
from core.utils import (
    DISEASE,
    DRUG,
    DRUG_UNIT,
    INFLUENCE,
    IRRADIATION_DEVICE,
    RADIATION,
    RADIATION_UNIT,
    TIME_UNIT,
    WELLS,
)


def influence_specification_component(experiment_data: Dict[str, Any], key):
    influence_options = st.multiselect(
        "Influence",
        options=[i.title() for i in INFLUENCE],
        label_visibility="collapsed",
        default=[
            i.title()
            for i in INFLUENCE.getlistdefault(key, experiment_data["influenceGroups"])
        ],
        key=key,
    )

    if experiment_data["influenceGroups"].get(key) is None:
        influence_group_dict = experiment_data["influenceGroups"][key] = {}
    else:
        influence_group_dict = experiment_data["influenceGroups"][key]

    for influence_option in sorted(
        influence_options, key=lambda x: INFLUENCE.index(x.lower())
    ):
        match influence_option:
            case "Control":
                influence_control_component(
                    influence_group_dict, influence_options, key=key
                )
            case "Sham":
                influence_sham_component(
                    influence_group_dict, influence_options, key=key
                )
            case "Radiation":
                influence_radiation_component(influence_group_dict, key=key)
            case "Pharmacology":
                influence_pharmacology_component(influence_group_dict, key=key)
            case "Stimulus":
                influence_stimulus_component(influence_group_dict, key=key)
            case "Disease":
                influence_disease_component(influence_group_dict, key=key)

    # Remove influence options that are not selected anymore
    for option in INFLUENCE:
        if option.title() not in influence_options:
            influence_group_dict.pop(
                option.lower(), None
            )  # influence_options are .title()ed

    # write the influence data to the experiment_data dict
    experiment_data["influenceGroups"][key] = influence_group_dict


def influence_meta_specification_component(experiment_data: Dict[str, Any]):
    experiment_data["numInfluenceGroups"] = st.number_input(
        "Number of influence groups",
        min_value=1,
        max_value=6,  # This defines the sqlite structure!
        value=experiment_data.get("numInfluenceGroups", 1),
        disabled=False,
        help=(
            "Select multiple influence groups only for :red[multiwell plates].\n\n"
            "Each group represents a unique grouping of influences on different wells. "
            "Influence groups allows easy referencing of influence locations to their "
            "respective control and sham locations."
        ),
    )

    influence_tabs = st.tabs(
        [
            f"Influence group {i}"
            for i in range(1, experiment_data["numInfluenceGroups"] + 1)
        ]
    )
    if experiment_data.get("influenceGroups") is None:
        experiment_data["influenceGroups"] = {}
    for index, influence_tab in enumerate(influence_tabs, start=1):
        with influence_tab:
            influence_specification_component(
                experiment_data, key=f"influenceGroup{index}"
            )


def influence_control_component(influence_data, influence_options, key):
    con_control = st.container()

    con_control.write("###### :red[Control]")
    if len(influence_options) > 1:
        con_control.warning(
            "You are choosing a control and another influence. "
            "Pay attention to the influences chosen.",
            icon="⚠️",
        )
    if influence_data.get("control") is None:
        case_dict = influence_data["control"] = {}
    else:
        case_dict = influence_data["control"]

    case_dict["name"] = "Control"

    # NOTE: It would be possible to hide the well selection if there is only one influenceGroup
    case_dict["wells"] = con_control.multiselect(
        "Well(s) - Control",
        options=WELLS,
        default=WELLS.getlistdefault("wells", case_dict),
        key=f"{key}_control_wells",
    )


def influence_sham_component(influence_data, influence_options, key):
    con_sham = st.container()
    con_sham.write("###### :red[Sham]")

    if len(influence_options) > 1:
        con_sham.warning(
            "You are choosing a control (sham) and another influence. "
            "Pay attention to the influences chosen.",
            icon="⚠️",
        )

    if influence_data.get("sham") is None:
        case_dict = influence_data["sham"] = {}
    else:
        case_dict = influence_data["sham"]

    case_dict["name"] = "Sham"

    case_dict["wells"] = con_sham.multiselect(
        "Well(s) - Sham",
        options=WELLS,
        default=WELLS.getlistdefault("wells", case_dict),
        key=f"{key}_sham_wells",
    )
    case_dict["notes"] = con_sham.text_area(
        label="Notes",
        placeholder="how, when, location",
        height=100,
        key=f"{key}_sham_notes",
        value=case_dict.get("notes", ""),
    )


def influence_radiation_component(influence_data, key):
    con_radiation = st.container()
    con_radiation.write("###### :red[Radiation]")

    # If influence is not yet defined in the template, create a new dict
    if influence_data.get("radiation") is None:
        case_dict = influence_data["radiation"] = {}
    else:
        case_dict = influence_data["radiation"]
    # st.write(experiment_data)
    case_dict["name"] = con_radiation.selectbox(
        "Name",
        options=RADIATION,
        index=RADIATION.getindexdefault("name", case_dict),
        key=f"{key}_rad_name",
    )

    # Components
    col_rad = con_radiation.columns(4)

    case_dict["dosage"] = col_rad[0].number_input(
        "Dosage",
        min_value=0.0,
        max_value=1000000.0,
        value=case_dict.get("dosage", 0.0),
        step=0.1,
        format="%0.3f",
        key=f"{key}_rad_dosage",
    )
    case_dict["dosageUnit"] = col_rad[1].selectbox(
        "Dosage unit",
        options=RADIATION_UNIT,
        index=RADIATION_UNIT.getindexdefault("dosageUnit", case_dict),
        key=f"{key}_rad_dosageUnit",
    )
    case_dict["exposure"] = col_rad[2].number_input(
        "Exposure time",
        min_value=0.0,
        max_value=100000.0,
        value=case_dict.get("exposure", 0.0),
        step=0.1,
        key=f"{key}_rad_exposure",
    )
    case_dict["exposureUnit"] = col_rad[3].selectbox(
        "Exposure time unit",
        options=TIME_UNIT,
        index=TIME_UNIT.getindexdefault("exposureUnit", case_dict),
        help=(
            "time period during which the cells were exposed to the radiation:\n"
            "s - seconds, m - minutes, h - hours, d - days, inf - permanent"
        ),
        key=f"{key}_rad_exposureUnit",
    )

    case_dict["irradiationDevice"] = con_radiation.selectbox(
        "Irradiation device",
        options=IRRADIATION_DEVICE,
        index=IRRADIATION_DEVICE.getindexdefault("irradiationDevice", case_dict),
        key=f"{key}_rad_irradiationDevice",
    )

    case_dict["wells"] = con_radiation.multiselect(
        "Well(s) - Radiation",
        options=WELLS,
        default=WELLS.getlistdefault("wells", case_dict),
        key=f"{key}_rad_wells",
    )
    case_dict["notes"] = con_radiation.text_area(
        label="Notes",
        placeholder="how, when, location",
        height=100,
        key=f"{key}_rad_notes",
        value=case_dict.get("notes", ""),
    )


def influence_pharmacology_component(influence_data, key):
    con_pharmacology = st.container()
    con_pharmacology.write("###### :red[Pharmacology]")

    # If influence is not yet defined in the template, create a new dict
    if influence_data.get("pharmacology") is None:
        case_dict = influence_data["pharmacology"] = {}
    else:
        case_dict = influence_data["pharmacology"]

    # Components
    case_dict["name"] = con_pharmacology.selectbox(
        "Name",
        options=DRUG,
        index=DRUG.getindexdefault("name", case_dict),
        key=f"{key}_pha_name",
    )

    col_pha = con_pharmacology.columns(4)

    case_dict["concentration"] = col_pha[0].number_input(
        "Concentration",
        min_value=0.0,
        max_value=1000000.0,
        value=case_dict.get("concentration", 0.0),
        step=0.1,
        format="%0.3f",
        key=f"{key}_pha_concentration",
    )
    case_dict["concentrationUnit"] = col_pha[1].selectbox(
        "Concentration unit",
        options=DRUG_UNIT,
        index=DRUG_UNIT.getindexdefault("concentrationUnit", case_dict),
        key=f"{key}_pha_concentrationUnit",
    )
    case_dict["exposure"] = col_pha[2].number_input(
        "Exposure time",
        min_value=0.0,
        max_value=100000.0,
        value=case_dict.get("exposure", 0.0),
        step=0.1,
        key=f"{key}_pha_exposure",
    )
    case_dict["exposureUnit"] = col_pha[3].selectbox(
        "Exposure time unit",
        options=TIME_UNIT,
        index=TIME_UNIT.getindexdefault("exposureUnit", case_dict),
        help=(
            "time period during which the cells were exposed to the drug:\n"
            "s - seconds, m - minutes, h - hours, d - days, inf - permanent"
        ),
        key=f"{key}_pha_exposureUnit",
    )

    case_dict["wells"] = con_pharmacology.multiselect(
        "Well(s) - Pharmacology",
        options=WELLS,
        default=WELLS.getlistdefault("wells", case_dict),
        key=f"{key}_pha_wells",
    )
    case_dict["notes"] = con_pharmacology.text_area(
        label="Notes",
        placeholder="how, when, location",
        height=100,
        key=f"{key}_pha_notes",
        value=case_dict.get("notes", ""),
    )


# TODO: define stimulus component
def influence_stimulus_component(influence_data, key):
    con_stimulus = st.container()

    con_stimulus.write("###### :red[Stimulus]")
    if influence_data.get("stimulus") is None:
        case_dict = influence_data["stimulus"] = {}
    else:
        case_dict = influence_data["stimulus"]

    case_dict["name"] = "Stimulus"

    # case_dict["wells"] = con_stimulus.multiselect(
    #     "Well(s)", options=WELLS, default=WELLS.getlistdefault("wells", case_dict)
    # )
    con_stimulus.info("Coming Soon :-)")


def influence_disease_component(influence_data, key):
    con_disease = st.container()
    con_disease.write("###### :red[Disease]")

    # If influence is not yet defined in the template, create a new dict
    if influence_data.get("disease") is None:
        case_dict = influence_data["disease"] = {}
    else:
        case_dict = influence_data["disease"]

    # Components
    case_dict["name"] = con_disease.selectbox(
        "Name",
        options=DISEASE,
        index=DISEASE.getindexdefault("name", case_dict),
        key=f"{key}_dis_name",
    )

    case_dict["wells"] = con_disease.multiselect(
        "Well(s) - Disease",
        options=WELLS,
        default=WELLS.getlistdefault("wells", case_dict),
        key=f"{key}_dis_wells",
    )
    case_dict["notes"] = con_disease.text_area(
        label="Notes",
        placeholder="how, when, location",
        height=100,
        key=f"{key}_dis_notes",
        value=case_dict.get("notes", ""),
    )
