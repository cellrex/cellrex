from datetime import datetime
import json
from typing import Any, Dict
from pathlib import Path
import streamlit as st
from core.utils import (
    check_existence_of_filepath,
    create_db_entry,
    post_request,
    read_protocol_file,
    get_request,
    get_hash_calc,
    get_file_paths_of_existing_hash,
)
from core.utils_labdata import PrefillList
from core.utils_json import DateTimeEncoder
from core.utils import (
    BRAIN_REGIONS,
    CELL_TYPE,
    EXPERIMENTERS,
    KEYWORDS,
    LABS,
    MULTI_CELL_TYPES,
    ORGAN_TYPE,
    ORIGIN,
    PROTOCOLS,
    SPECIES,
)

data_path = Path("data")
upload_path = Path("upload")


def subject_specification_component(experiment_data: Dict[str, Any]):
    experiment_data["species"] = st.radio(
        "Species",
        options=SPECIES,
        horizontal=True,
        index=SPECIES.getindexdefault("species", experiment_data),
    )

    experiment_data["origin"] = st.radio(
        "Origin",
        options=ORIGIN,
        horizontal=True,
        index=ORIGIN.getindexdefault("origin", experiment_data),
    )

    experiment_data["organType"] = st.radio(
        "Organ type",
        options=ORGAN_TYPE,
        horizontal=True,
        index=ORGAN_TYPE.getindexdefault("organType", experiment_data),
    )

    experiment_data["cellType"] = st.radio(
        "Cell type",
        options=CELL_TYPE[experiment_data["organType"]],
        horizontal=True,
        index=CELL_TYPE[experiment_data["organType"]].getindexdefault(
            "cellType", experiment_data
        ),
    )

    if experiment_data["cellType"] in MULTI_CELL_TYPES:
        experiment_data["brainRegion"] = st.multiselect(
            "Brain region",
            options=BRAIN_REGIONS,
            default=BRAIN_REGIONS.getlistdefault("brainRegion", experiment_data),
        )


def subject_protocol_component(experiment_data: Dict[str, Any], key):
    if experiment_data["protocols"].get(key) is None:
        protocol_dict = experiment_data["protocols"][key] = {
            "name": key,
            "path": PROTOCOLS[key],
        }
        try:
            protocol_dict["text"] = read_protocol_file(PROTOCOLS[key])
        except FileNotFoundError:
            st.error(
                f"Protocol file {PROTOCOLS[key]} not found. Please check the path."
            )
    else:
        protocol_dict = experiment_data["protocols"][key]

    protocol_dict["notes"] = st.text_area(
        label="Protocol Notes for " + key,
        placeholder="Protocol changes, if applicable",
        value=protocol_dict.get("notes", None),
        height=100,
        key=key,
    )

    with st.expander("Show protocol"):
        if protocol_dict.get("text"):
            st.write(protocol_dict["text"])
        else:
            st.warning("No protocol text available.")


def subject_meta_protocol_cellid_component(experiment_data: Dict[str, Any]):
    experiment_data["protocolNames"] = st.multiselect(
        "Protocol name",
        options=PROTOCOLS.keys(),
        default=PROTOCOLS.getlistdefault("protocolNames", experiment_data),
        help=(
            "Each time you run this, protocols are freshly loaded "
            "from the path specified in the 'labdata.yml' file."
        ),
    )

    if experiment_data.get("protocolNames"):
        protocol_tabs = st.tabs(
            [
                f"Protocol {i}"
                for i in range(1, len(experiment_data["protocolNames"]) + 1)
            ]
        )
        if experiment_data.get("protocols") is None:
            experiment_data["protocols"] = {}
        for index, protocol_tab in enumerate(protocol_tabs, start=0):
            with protocol_tab:
                # influence_specification_component(experiment_data, key=f"influenceGroup{index}")
                subject_protocol_component(
                    experiment_data,
                    key=experiment_data["protocolNames"][index],
                )
        # Remove protocol options that are not selected anymore
        for option in PROTOCOLS.keys():
            if option not in experiment_data["protocolNames"]:
                experiment_data["protocols"].pop(option, None)

    experiment_data["cellID"] = st.text_input(
        "Cell ID",
        value=experiment_data.get("cellID", None),
        help=(
            "Unique identifier for the cells. Can be the ID given by the manufacturer "
            "or a custom ID given by the lab."
        ),
        placeholder="Identifier for the cells, e.g. 90090",
    )


def session_metadata_component(experiment_data: Dict[str, Any]):
    experiment_data["keywords"] = st.multiselect(
        "Keywords(s)",
        options=KEYWORDS,
        placeholder="Select keywords(s)",
        max_selections=5,
        default=KEYWORDS.getlistdefault("keywords", experiment_data),
    )

    experiment_data["experimenter"] = st.multiselect(
        "Experimenter(s)",
        options=EXPERIMENTERS,
        placeholder="Select experimenter(s)",
        default=EXPERIMENTERS.getlistdefault("experimenter", experiment_data),
    )

    experiment_data["lab"] = st.multiselect(
        "Lab(s)",
        options=LABS,
        placeholder="Select lab(s)",
        default=LABS.getlistdefault("lab", experiment_data),  # LABS[0]
    )

    col_datetime1, col_datetime2 = st.columns(2)
    experiment_data["date"] = col_datetime1.date_input(
        "Date of measurement",
        value=experiment_data.get("date", datetime.now()),
        format="DD.MM.YYYY",
    )

    experiment_data["time"] = col_datetime2.time_input(
        "Time of measurement",
        step=60,
        value=experiment_data.get("time", None),
    )

    # Create and check for experimentName
    response = post_request(
        "biofiles",
        "filepath",
        data={
            "experiment_data": json.loads(
                json.dumps(experiment_data, cls=DateTimeEncoder)
            ),
            "key_order": ["species", "origin", "organType", "cellType"],
        },
    )
    if response.status_code != 200:
        st.error(f"Error: {response.json()['detail']}")
        st.stop()
    filepath_so_far = Path(response.json()["data"]["experiment_path"])

    st.write(f"The filepath so far: :red[**{filepath_so_far}**]")

    experimenters = "-".join(experiment_data["experimenter"])
    keywords = "-".join(experiment_data["keywords"][:3])
    new_experiment_name = "_".join(
        ["exp", str(experiment_data["date"]), experimenters, keywords]
    )

    response = get_request(
        "filemanagement", "exists", (data_path / filepath_so_far).as_posix()
    )
    if response.status_code == 200:
        existing_folders = get_request(
            "filemanagement", "list", (data_path / filepath_so_far).as_posix()
        ).json()["data"]
    else:
        existing_folders = []

    available_experimentNames = set(existing_folders + [new_experiment_name])
    selected_folder = st.selectbox(
        "Select experiment folder and define **'experimentName'**: \n\n :blue[exp_<date-of-first-measurement>_ <experimenter(s)>_<keyword(s)>]",
        options=available_experimentNames,
        index=PrefillList(available_experimentNames).getindexdefault(
            "experimentName", experiment_data
        ),
    )
    if (
        selected_folder == new_experiment_name
        and selected_folder not in existing_folders
    ):
        st.info("This folder will be newly created.")
    experiment_data["experimentName"] = selected_folder
    # NOTE: works with template, but it is possible to assign different experimenters to experimentName (which currently definded by experimenters)

    experiment_data["precursorExperimentNames"] = st.multiselect(
        "Precursor experiment(s)",
        options=existing_folders,
        default=PrefillList(existing_folders).getlistdefault(
            "precursorExperimentNames", experiment_data
        ),
        help="Select precursor experiment(s) to link the current experiment to them.",
    )
    if selected_folder in experiment_data["precursorExperimentNames"]:
        st.warning(
            "The current **'experimentName'** is also selected as a precursor experiment. This is not recommended.",
            icon="⚠️",
        )
    experiment_data["sampleID"] = st.number_input(
        "Sample ID",
        min_value=0,
        max_value=None,
        value=experiment_data.get("sampleID", None),
        step=1,
    )

    col_age1, col_age2 = st.columns(2)
    experiment_data["ageDIV"] = col_age1.number_input(
        "Age (DIV)",
        min_value=0,
        max_value=None,
        value=experiment_data.get("ageDIV", None),
        step=1,
    )

    experiment_data["ageDAP"] = col_age2.number_input(
        "Age (DAP)",
        min_value=0,
        max_value=None,
        value=experiment_data.get("ageDAP", None),
        step=1,
    )

    # location: x y z - Coordinates (not required!)
    # sample rate (not required!)


def session_notes_component(experiment_data: Dict[str, Any]):
    experiment_data["notes"] = st.text_area(
        label="Notes", placeholder="Notes about the experiment", height=100
    )

    experiment_data["smiley"] = None

    if st.checkbox(
        "Raw data has been reviewed.",
        help="Raw data has been reviewed. On this basis the data and the experiment can be rated.",
    ):
        experiment_data["smiley"] = st.slider(
            label="Smiley :slightly_smiling_face:",
            value=5,
            step=1,
            min_value=0,
            max_value=10,
        )

    experiment_data["creationDate"] = datetime.now()


def output_filepath_component(experiment_data: Dict[str, Any], filename):
    st.write(
        "The following path will be used to save the file. The template is given in blue while the actual path is given in red:"
    )
    response = post_request(
        "biofiles",
        "filepath",
        data={
            "experiment_data": json.loads(
                json.dumps(experiment_data, cls=DateTimeEncoder)
            )
        },
    )
    if response.status_code != 200:
        st.error(f"Error: {response.json()['detail']}")
        st.stop()
    experiment_path = Path(response.json()["data"]["experiment_path"])

    complete_filepath: Path = data_path / experiment_path / filename

    experiment_data["filepath"] = (experiment_path / filename).as_posix()

    st.write(
        ":blue[species/origin/organType/cellType/experimentName/influence/sampleID/age/labDevice]"
    )
    st.write(f":red[{experiment_path}]")

    if not (data_path / experiment_path).exists():
        st.info(
            "The chosen filepath does not currently exist. "
            "New subfolders will be created, which is the desired outcome.",
            icon="⚠️",
        )
    return complete_filepath


def output_check_component(
    experiment_data: Dict[str, Any], complete_filepath, filename
):
    for i in range(1, experiment_data.get("numInfluenceGroups") + 1):
        if not experiment_data["influenceGroups"].get(f"influenceGroup{i}"):
            st.warning(
                f"No **influence** is chosen in **influenceGroup{i}**. "
                "Choose at least one **influence**.",
                icon="⚠️",
            )

    if experiment_data.get("sampleID") is None:
        st.warning(
            "**'sampleID'** value is **None** (it is not specified). \n\n"
            "*'sIDNone'* will be used as placeholder. Any data already existing in a *'sIDNone'* folder "
            "will be overwritten. There is risk of data loss!",
            icon="⚠️",
        )

    if experiment_data.get("ageDIV") is None and experiment_data.get("ageDAP") is None:
        st.warning(
            "Both **'Age (DIV)'** and **'Age (DAP)'** values are **None** (they are not specified). \n\n"
            "*'ageNone'* will be used as placeholder. Any data already existing in a *'ageNone'* folder "
            "will be overwritten. There is risk of data loss!",
            icon="⚠️",
        )

    if experiment_data.get("experimentName") is None:
        st.warning(
            "**'experimentName'** value is **None** (it is not specified). \n\n"
            "*'None'* will be used as placeholder. Any data already existing in a *'None'* folder "
            "will be overwritten. There is risk of data loss!",
            icon="⚠️",
        )

    # check for duplicate file in destination folder
    if complete_filepath.is_file():
        st.warning(
            f"Caution: The file **{filename}** already exists at the destination. \n\n"
            "The file will be overwritten. There is risk of data loss!",
            icon="⚠️",
        )

    if check_existence_of_filepath(complete_filepath):
        st.warning("Caution: The filepath already exists in the database.", icon="⚠️")

    with st.spinner("Calculating hash..."):
        hash_info = get_hash_calc(filename)

    response = get_request("filemanagement", "filesize", upload_path / filename)
    match response.status_code:
        case 200:
            filesize_info = response.json()["data"]["size"]
        case _:
            st.error("Error retrieving file size.")

    filehash_exists, filepaths_for_hash = get_file_paths_of_existing_hash(hash_info)

    if filehash_exists:
        st.warning(
            "**Duplicate Detected:** The file you're trying to upload "
            "already exists in the database at the following locations:",
            icon="⚠️",
        )
        st.write(filepaths_for_hash)

    return filesize_info, hash_info


def output_submit_component(
    experiment_data: Dict[str, Any],
    complete_filepath,
    filename,
    filesize_info,
    hash_info,
):
    if st.checkbox(
        "I've reviewed the details and acknowledge the warnings. Ready to upload."
    ):
        if st.button("Create file structure and move files"):
            if _ := create_db_entry(
                complete_filepath,
                experiment_data,
                filesize_info,
                hash_info,
            ):
                response = post_request(
                    route="filemanagement",
                    endpoint="move",
                    data={
                        "filename": filename.as_posix(),
                        "srcpath": upload_path.as_posix(),
                        "dstpath": complete_filepath.parent.as_posix(),
                        "filecontext": json.loads(
                            json.dumps(experiment_data, cls=DateTimeEncoder)
                        ),
                    },
                )
                if response.status_code == 200:
                    st.success(
                        f"File **{filename}** moved and metadata file created sucessfully."
                    )
                else:
                    st.error(
                        f"Error moving files with status code: {response.status_code}. Look for incomplete files."
                    )
