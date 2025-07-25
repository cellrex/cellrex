"""
2__Search.py

This tab is used to search for files based on the metadata of the files.
You can select multiple options for each category.
"""

import json

import pandas as pd
import streamlit as st
from component.search import session_general_row  # make_divider,
from component.search import device_row, session_influence_row, subject_row
from component.sidebar import sidebar_logo_component
from core.utils import check_backend, post_request
from core.utils_json import DateTimeEncoder

st.set_page_config(page_title="Search", page_icon=":microbe:", layout="wide")

sidebar_logo_component()

if not check_backend():
    st.toast(":red[**Status: Database is not ready**] :x:")

st.write("## Search")
with st.expander("**How the search works:**"):
    st.write(
        "The search is based on the filecontext of the files. "
        "You can select multiple options for each category. If you select multiple options for a category, "
        "the search will return all files that match at least one of the selected options (logical OR). "
        "If you select multiple options for different categories, the search will return all "
        "files that match all of the selected categories (logical AND)."
    )

search_data = {}

st.markdown(
    """
    <style>
    div [data-baseweb=select]  {
    max-height: 140px;
    overflow: auto;
    }
    </style>""",
    unsafe_allow_html=True,
)

### Subject ###
# make_divider("Subject", "virus")
subject_row(search_data, col_args=6)


### Session General ###
# make_divider("Session", "calendar2-week-fill")
session_general_row(search_data, col_args=3 * [0.1625] + [2 * 0.1625] + [0.1625])

### Session Influence ###
# make_divider("Influences", "capsule")
session_influence_row(search_data, col_args=6)

### Session Device ###
# make_divider("Device", "cpu-fill")
device_row(search_data, col_args=6)

search_data = json.loads(json.dumps(search_data, cls=DateTimeEncoder))

st.write("## Search Results")
# st.write(search_data)
search_data = {k: v for k, v in search_data.items() if v}
# st.write(search_data)

response = post_request(
    "biofiles", "search", parameter={"offset": 0, "limit": 10}, data=search_data
)
if response.status_code == 200:
    data = response.json()  # List[BiofileResponse]
    total_items = data["total"]
    limit = 100
    current_offset = 0

    biofiles = []

    while True:
        response = post_request(
            "biofiles",
            "search",
            parameter={"offset": current_offset, "limit": limit},
            data=search_data,
        )
        response.raise_for_status()
        data = response.json()

        biofiles.extend(data["items"])

        if current_offset + limit >= total_items:
            break

        current_offset += limit

    dataframe_columns = st.columns([1 / 12, 11 / 12])
    flattening_level = dataframe_columns[0].number_input(
        "Flattening level", min_value=1, max_value=3, value=3
    )

    df = pd.json_normalize(
        [row["filecontext"] for row in biofiles], max_level=flattening_level
    )

    visible_columns = dataframe_columns[1].multiselect(
        "Visible columns", options=df.columns
    )
    if visible_columns is None:
        visible_columns = df.columns
    # TODO: Pagination
    st.text(
        f"Items found: {response.json()['total']}",
        help="Note that several items (files) may belong to a single measurement.",
    )
    st.dataframe(df, column_order=visible_columns, use_container_width=True)

    with st.expander("Advanced search results", expanded=False):
        st.write(
            "In the following JSON, you can see the raw search results. "
            "Expand the JSON to see the full results or copy the JSON to "
            "analyze it in a different environment."
        )
        st.json(data, expanded=False)
elif response.status_code == 404:
    st.info("No data found")

else:
    st.error("Error retrieving data. " + str(response.status_code))
