"""
3__Dashboard.py

This tab is used to display the data in the database in a dashboard format.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from component.sidebar import sidebar_logo_component
from core.utils import check_backend, get_request

st.set_page_config(page_title="Dashboard", page_icon=":microbe:", layout="wide")

# Layout configuration
p_width = 350
p_height = 300
gap = "small"
legend = dict(orientation="h", yanchor="bottom", y=1.2, xanchor="center", x=0.5)
theme = "streamlit"

sidebar_logo_component()

if not check_backend():
    st.toast(":red[**Status: Database is not ready**] :x:")

st.write("## Dashboard")

response = get_request(
    "biofiles", "all", parameter={"offset": 0, "limit": 10}, timeout=10
)
if response.status_code == 200:
    data = response.json()
    total_items = data["total"]
    limit = 100
    current_offset = 0

    biofiles = []

    while True:
        response = get_request(
            "biofiles",
            "all",
            parameter={"offset": current_offset, "limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        biofiles.extend(data["items"])

        if current_offset + limit >= total_items:
            break

        current_offset += limit

    df_all = pd.json_normalize(row for row in biofiles)

    line_1_1, line_1_2, line_1_3 = st.columns(3, gap=gap)

    with line_1_1:
        total_data_count = len(df_all)
        st.metric(
            label="Total count",
            value=total_data_count,
            help="Note that several items (files) may belong to a single measurement.",
        )

    with line_1_2:
        total_data_size = round(df_all["filesize"].sum() * 1e-9, 2)
        st.metric(label="Total size", value=f"{total_data_size} GB")

    df = pd.json_normalize([row["filecontext"] for row in biofiles])

    line_2_1, line_2_2, line_2_3 = st.columns(3, gap=gap)

    with line_2_1:
        df_date = df["date"]
        df_date = df_date.value_counts().reset_index().sort_values("date")

        df_upload = df["creationDate"]
        df_upload = pd.to_datetime(df_upload)
        df_upload = (
            df_upload.dt.date.value_counts().reset_index().sort_values("creationDate")
        )

        fig = make_subplots(specs=[[{"secondary_y": False}]])
        fig.add_trace(
            go.Scatter(x=df_date["date"], y=df_date["count"], name="experiment"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df_upload["creationDate"], y=df_upload["count"], name="upload"
            ),
            secondary_y=False,
        )
        fig.update_yaxes(title_text="count", secondary_y=False)
        fig.update_xaxes(title_text="date")
        fig.update_layout(
            title_text="Activity", width=p_width, height=p_height, legend=legend
        )
        st.plotly_chart(fig, theme=theme)

    with line_2_2:
        df_fs = df
        df_fs["filesize"] = df_all["filesize"]
        df_fs_sum = (
            df_fs.groupby("date")["filesize"].sum().reset_index().sort_values("date")
        )
        df_fs_mean = (
            df_fs.groupby("date")["filesize"].mean().reset_index().sort_values("date")
        )
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=df_fs_sum["date"],
                y=round(df_fs_sum["filesize"] * 1e-9, 2),
                name="sum",
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df_fs_mean["date"],
                y=round(df_fs_mean["filesize"] * 1e-9, 2),
                name="mean",
            ),
            secondary_y=True,
        )
        fig.update_yaxes(title_text="sum", secondary_y=False)
        fig.update_yaxes(title_text="mean", secondary_y=True)
        fig.update_xaxes(title_text="date")
        fig.update_layout(
            title_text="Filesize", width=p_width, height=p_height, legend=legend
        )
        st.plotly_chart(fig, theme=theme)

    with line_2_3:
        df_sun = df
        df_sun["filesize"] = df_all["filesize"]
        fig = px.sunburst(
            df_sun,
            path=["species", "origin", "organType", "cellType"],
            values="filesize",
        )
        fig.update_layout(width=p_width, height=p_height)
        st.plotly_chart(fig, theme=theme)

    line_3_1, line_3_2, line_3_3 = st.columns(3, gap=gap)

    with line_3_1:
        df_species = df["species"].value_counts().reset_index()
        fig = px.bar(df_species, x="count", y="species", orientation="h")
        fig.update_layout(
            title_text="Species",
            width=p_width,
            height=p_height,
            yaxis=dict(title=None, showticklabels=True),
        )
        st.plotly_chart(fig, theme=theme)

    with line_3_2:
        df_experimenter = df["experimenter"].explode().value_counts().reset_index()
        fig = px.bar(df_experimenter, x="count", y="experimenter", orientation="h")
        fig.update_layout(
            title_text="Experimenter",
            width=p_width,
            height=p_height,
            yaxis=dict(title=None, showticklabels=True),
        )
        st.plotly_chart(fig, theme=theme)

    with line_3_3:
        df_labDeviceType = df["labDeviceType"].value_counts().reset_index()
        fig = px.bar(df_labDeviceType, x="count", y="labDeviceType", orientation="h")
        fig.update_layout(
            title_text="Device",
            width=p_width,
            height=p_height,
            yaxis=dict(title=None, showticklabels=True),
        )
        st.plotly_chart(fig, theme=theme)

else:
    st.error("Error retrieving data. " + str(response.status_code))
