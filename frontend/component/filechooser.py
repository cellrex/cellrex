from pathlib import Path
from typing import Optional

import streamlit as st
from core.utils import get_request


def sticky_file_component(search_path: str = "upload") -> Optional[Path]:
    header = st.container()
    header_con = header.empty()

    # Custom CSS for the sticky header
    # BUG: Currently dark theme is not supported for automatic switching
    # see: https://discuss.streamlit.io/t/check-if-the-app-is-in-dark-mode-or-light-mode-at-runtime/20222/3
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)
    st.markdown(
        """
    <style>
        div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
            position: sticky;
            top: 2.875rem;
            background-color: white;
            z-index: 999;
        }
    
        .fixed-header {
            border-bottom: 1.5px solid red;
        }

        */
    </style>
        """,
        unsafe_allow_html=True,
    )

    # Get the list of files in the upload folder
    result_filelist = get_request("filemanagement", "filelist", "upload")

    match result_filelist.status_code:
        case 200:
            chosen_file = header_con.selectbox(
                "Select file for which to specify metadata.",
                options=result_filelist.json()["data"],
            )

            return Path(chosen_file)
        case 404:
            header_con.warning(
                "No file found in the upload folder. Please also check for supported filetypes. "
                "Upload all files to the upload folder.",
                icon="⚠️",
            )
            return None
        case _:
            header_con.error(
                f"An error occurred while fetching the file list. Error code: {result_filelist.status_code}",
                icon="⚠️",
            )
            return None
