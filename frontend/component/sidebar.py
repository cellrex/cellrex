import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st
from core.utils_json import DateTimeDecoder, DateTimeEncoder


def sidebar_upload_component() -> Optional[Dict[str, Any]]:
    st.sidebar.subheader(":black[Select template]")
    uploaded_file = st.sidebar.file_uploader("Import template data.", type=["json"])
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        try:
            # Parse the JSON content
            json_data = json.loads(file_content, cls=DateTimeDecoder)
            st.success("Template data imported successfully!")
            return json_data
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please import a valid JSON file.")
    return None


def sidebar_download_component(json_data: Dict[str, Any]):
    assert json_data is not None, "JSON data must not be None!"

    st.sidebar.subheader(":black[Save template]")
    template_name = st.sidebar.text_input(
        "Filename for saving the template",
        value=f"template_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json",
    )
    st.sidebar.download_button(
        "Save metadata as template",
        data=json.dumps(json_data, cls=DateTimeEncoder),
        file_name=template_name,
        mime="application/json",
    )


def sidebar_logo_component():
    logo_url = "static/CellRex_Swoosh.svg"
    logo = f"url(data:image/svg+xml;base64,{base64.b64encode(Path(logo_url).read_bytes()).decode()})"

    st.markdown(
        f"""
    <style>
        [data-testid="stSidebarNav"] {{
            background-image: {logo};
            background-repeat: no-repeat;
            padding-top: {50 - 40}px;
            background-position: 20px 40px;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )
