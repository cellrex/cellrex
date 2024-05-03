from datetime import date

import streamlit as st
from core.utils import (
    BRAIN_REGIONS,
    CELL_TYPE,
    DEVICE_MEA,
    DEVICE_MICROSCOPE,
    DISEASE,
    DRUG,
    EXPERIMENTERS,
    KEYWORDS,
    LABS,
    MEA_CHIP_TYPE,
    MICROSCOPE_TASKS,
    ORGAN_TYPE,
    ORIGIN,
    PROTOCOLS,
    RADIATION,
    SPECIES,
    STIMULUS,
)

# import streamlit_antd_components as sac
# from streamlit_extras.stylable_container import stylable_container


# def make_divider(label, icon):
#    sac.divider(
#        label,
#        icon=icon,
#        align="center",
#        label_style={"font-size": "14px"},
#    )


# def vertical_label(column, label):
#    with column:
#        stylable_container(
#            "h6",
#            """h6{
#                transform-origin: 0 0;
#                transform: translateX(100%) translateY(20%) rotate(90deg);
#            }""",
#        ).write(f"###### {label}")


def subject_row(search_data, col_args):
    row_con = st.container()
    row_cols = row_con.columns(spec=col_args)

    search_data["species"] = row_cols[0].multiselect(
        "Species",
        options=SPECIES,
    )

    search_data["origin"] = row_cols[1].multiselect(
        "Origin",
        options=ORIGIN,
    )

    search_data["organType"] = row_cols[2].multiselect(
        "Organ type",
        options=ORGAN_TYPE,
    )

    search_data["cellType"] = row_cols[3].multiselect(
        "Cell type", options=sum(CELL_TYPE.values(), [])
    )

    search_data["brainRegion"] = row_cols[4].multiselect(
        "Brain region", options=BRAIN_REGIONS
    )

    search_data["protocolName"] = row_cols[5].multiselect(
        "Protocol",
        options=PROTOCOLS,
    )


def session_general_row(search_data, col_args):
    row_con = st.container()
    row_cols = row_con.columns(spec=col_args)

    search_data["keywords"] = row_cols[0].multiselect("Keywords", options=KEYWORDS)

    search_data["experimenter"] = row_cols[1].multiselect(
        "Experimenter", options=EXPERIMENTERS
    )

    search_data["lab"] = row_cols[2].multiselect("Laboratory", options=LABS)

    search_data["date_from"], search_data["date_to"] = row_cols[3].slider(
        "Experiment Date",
        min_value=date(2000, 1, 1),
        max_value=date.today(),
        value=(date(2000, 1, 1), date.today()),
        format="DD.MM.YYYY",
    )

    search_data["experimentName"] = row_cols[4].text_input(
        "Experiment name", placeholder="exp_2024-01-22_Tim-Jan_mea-lsd-neuron"
    )


def session_influence_row(search_data, col_args):
    row_con = st.container()
    row_cols = row_con.columns(spec=col_args)

    search_data["control"] = row_cols[0].multiselect("Control", options=["Control"])
    search_data["sham"] = row_cols[1].multiselect("Sham", options=["Sham"])
    search_data["pharmacology"] = row_cols[2].multiselect("Pharmacology", options=DRUG)
    search_data["radiation"] = row_cols[3].multiselect("Radiation", options=RADIATION)
    # TODO: Implement Stimulus
    search_data["stimulus"] = row_cols[4].multiselect(
        "Stimulus", options=STIMULUS, disabled=True
    )
    search_data["disease"] = row_cols[5].multiselect("Disease", options=DISEASE)


def device_row(search_data, col_args):
    row_con = st.container()
    row_cols = row_con.columns(col_args)

    search_data["deviceMEA"] = row_cols[0].multiselect(
        "MEA device",
        options=DEVICE_MEA,
    )

    search_data["chipTypeMEA"] = row_cols[1].multiselect(
        "MEA chip type",
        options=MEA_CHIP_TYPE,
    )

    search_data["deviceMicroscope"] = row_cols[2].multiselect(
        "Microscope device",
        options=DEVICE_MICROSCOPE,
    )

    search_data["taskMicroscope"] = row_cols[3].multiselect(
        "Microscope task",
        options=MICROSCOPE_TASKS,
    )
