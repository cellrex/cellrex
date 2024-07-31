"""
1__Upload.py

The upload tab is used to upload files and specify metadata for the files.
The metadata is stored in a JSON file and the file is moved to a specified
location. The metadata is also stored in a SQLite database.
"""

from typing import Any, Dict, Union
from pathlib import Path
import streamlit as st
from component.device import session_device_component
from component.filechooser import sticky_file_component
from component.general import (
    session_metadata_component,
    session_notes_component,
    subject_meta_protocol_cellid_component,
    subject_specification_component,
    output_filepath_component,
    output_check_component,
    check_empty_upload_folder,
    output_submit_component,
)
from component.influence import influence_meta_specification_component
from component.sidebar import (
    sidebar_download_component,
    sidebar_logo_component,
    sidebar_upload_component,
)
from core.utils import (
    check_backend,
)

# Page configuration
st.set_page_config(page_title="Upload", page_icon=":microbe:", layout="centered")

# Sidebar components
sidebar_logo_component()
experiment_data_from_template = sidebar_upload_component()

if experiment_data_from_template is None:
    st.info(
        "No template is selected! "
        "Have a look into the sidebar to select one or start from scratch. :slightly_smiling_face:"
    )
    experiment_data: Dict[str, Any] = {}
else:
    experiment_data = experiment_data_from_template

if not check_backend():
    st.toast(":red[**Status: Database is not ready**] :x:")

# Actual page
st.write("## Upload")
upload_path = Path("upload")

if not upload_path.exists():
    st.error(f"Upload folder does not exist. Please create it first at '{upload_path}'")
    st.stop()

# Sticky file component to select the file to be specified
filename: Union[str | None] = sticky_file_component(search_path=upload_path)

if filename is not None:
    # Delegate to the correct file handler
    match filename.suffix.lower():
        # case ".csv":
        #     file_handler = CSVHandler(filename)
        case ".demofile":
            st.error("Demofile selected!")
        case _:
            # st.error("File type not supported")
            pass

# file_metadata = file_handler.file_metadata
# if st.toggle("Allow information from file to overwrite template"):
#     experiment_data_from_template.update(file_metadata)
# TODO: Use file_metadata to update the experiment_data dict

# Render the sections, remember experiment_data is a mutable object
st.write("## Subject")
subject_specification_component(experiment_data)
subject_meta_protocol_cellid_component(experiment_data)

st.write("---")
st.write("## Session")

st.write("#### :gray[General]")
session_metadata_component(experiment_data)

st.write("#### :gray[Influence]")

influence_meta_specification_component(experiment_data)

st.write("#### :gray[Device]")
session_device_component(experiment_data)


st.write("---")
st.write("## General")
session_notes_component(experiment_data)

st.write("---")
check_empty_upload_folder(filename)
st.write("## Output")

st.write("##### File path")
complete_filepath = output_filepath_component(experiment_data, filename)
# TODO: Feature: before moving: replace blanks with underscores
st.write("##### Meta data")
st.json(experiment_data, expanded=False)

filesize_info, hash_info = output_check_component(
    experiment_data, complete_filepath, filename
)
with st.expander("Advanced meta data", expanded=False):
    st.json(
        {
            "filename": filename,
            "filesize": filesize_info,
            "filehash": hash_info,
            "filepath": complete_filepath,
        }
    )
output_submit_component(
    experiment_data, complete_filepath, filename, filesize_info, hash_info
)

# Fill sidebar with download component
st.sidebar.write("####")
sidebar_download_component(json_data=experiment_data)
