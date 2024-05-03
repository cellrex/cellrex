import streamlit as st
from component.sidebar import sidebar_logo_component
from core.utils import check_backend

# Page configuration
st.set_page_config(page_title="Welcome", page_icon=":microbe:", layout="centered")

if not check_backend():
    st.toast(":red[**Status: Database is not ready**] :x:")

sidebar_logo_component()

st.image("static/CellRex_Swoosh.svg", use_column_width=True)
st.write("## Welcome to CellRex!")

col1, col2 = st.columns(2)
col1.markdown(
    """
    <style>
    .img-container {
        border-radius: 15px;
        overflow: hidden;
    }
    </style>
    <div class="img-container">
        <img src="app/static/CellRex-Logo_freigestellt.png" width="100%">
    </div>
    """,
    unsafe_allow_html=True,
)

with col2:
    st.write(
        "This application is designed to help you organise your biological data and files. "
        "There are a few things you should know before you start. We have three main sections:"
    )
    st.write("1. **Upload**: Here you can upload your files and add metadata to them.")
    st.write("2. **Search**: Here you can search for files based on their metadata.")
    st.write(
        "3. **Dashboard**: Here you can see an overview of all your files. (This is still a work in progress.)"
    )
    st.write("You can navigate to these sections using the sidebar on the left.")

st.write("### For Firefox users")
st.write(
    "To enable all functionality: \n",
    "Go to [about\:config](about:config) in your browser search bar and search for **layout.css.has-selector.enabled**. ",
    "Set this to **true** and you should be able to see all functionality.",
)
