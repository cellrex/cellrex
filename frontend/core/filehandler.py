from abc import ABC
from pathlib import Path
from typing import Any, Dict
import streamlit as st


class FileHandler(ABC):
    def __init__(self, filename: Path) -> None:
        self.file_metadata: Dict[str, Any] = {}

        self.filename = filename

    def render(self) -> None:
        pass

    def get_data(self):
        pass


class TiffHandler(FileHandler):
    def __init__(self) -> None:
        pass


class AiviaTiffHandler(TiffHandler):
    def __init__(self) -> None:
        pass

    def render(self, upload_file, i=0):
        st.write("HELLO WORLD")


class CSVHandler(FileHandler):
    """
    CSVHandler is a subclass of the FileHandler class. It is specifically
    designed to handle CSV files.
    """

    def parse_csv(self):
        """Parses the CSV file and returns the data as a dictionary."""
        pass

    def write_csv(self):
        """Writes the data to the CSV file."""
        pass
