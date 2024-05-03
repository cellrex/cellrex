# CellRex

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/streamlit/roadmap)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Welcome to CellRex, a user-friendly full stack application built with Python and Streamlit. This application allows you to upload, download, and manage your research data with ease.
CellRex is a platform that establishes a link between biological metadata and experimentally generated files. 
## Features

CellRex is built as a multipage app with three main pages:

1. **Upload**: This page allows you to upload data files by dragging and dropping them into a dedicated upload folder on your filesystem or your NAS and filling out a form with relevant information. The **template and check features** streamline the upload process, ensuring consistency and accuracy in the information provided.

https://github.com/cellrex/cellrex/assets/163431168/1f9fd925-8441-480b-8661-2b4070f53fbd


2. **Search**: This page provides a search mask that you can use to specify search criteria and easily find data files.

https://github.com/cellrex/cellrex/assets/163431168/2addf28a-d053-48f5-9b07-4b4f13b022b0


3. **Dashboard**: This page provides insights about your data and helps you manage and organize your data efficiently.

## Getting Started

Follow these steps to get started with CellRex:

1. Create an `.env-File` with the following variables that will be used for docker-compose:
```env
LOCAL_DATA_PATH = Path to your local or network storage where the upload folder should reside

LOCAL_DATA_PATH_SQLITE = Path to the folder where the .sqlite-File will reside
```

2. Build and start the container via docker-compose
```commandline
docker compose up
```

3. Open your web browser to access the app.
```
Local URL:      http://localhost:8501
Network URL:    http://ip.of.your.server:8501
```
4. Navigate to the **Upload** page and follow the instructions to upload your data.

5. Switch to the **Search** page and specify search criteria in the search mask to find data files.

6. Download the relevant data files from the search results.

7. Use the **Dashboard** page to manage and organize your data.

## Architecture

The architecture of CellRex is divided into two main parts: the frontend and the backend.

### Frontend

The frontend of CellRex is built with Streamlit. The frontend provides a user-friendly interface for uploading, searching, and managing data files. It communicates with the backend through a RESTful API, sending requests and receiving responses in the form of JSON data.

### Backend

The backend of CellRex is built with FastAPI. It is responsible for managing the data files and metadata.

The data files are stored in a hierarchical folder structure, with each data file accompanied by a corresponding metadata JSON file. This structure allows for efficient organization and retrieval of data files.

The metadata for each data file is also stored in a SQLite database, which provides a robust and efficient method for querying and retrieving metadata.

### Docker

Both the frontend and backend are containerized using Docker, which ensures that the application runs in a consistent environment. Docker Compose is used to manage the application services, making it easy to start and stop the application with a single command.

## Contributing

We welcome contributions to CellRex! Here's how you can set up the development environment:

1. Clone the repository:

```bash
git clone https://github.com/cellrex/cellrex.git
cd cellrex
```

2. Install the development requirements:

```bash
pip install -r requirements-dev.txt
```

3. Set up the pre-commit hooks:
```bash
pre-commit install
```

Now you're ready to start contributing! Please make sure to run the tests before you commit your changes:
```bash
pytest
```

If the tests pass, you can commit your changes and create a pull request.

Thank you for your contribution!

## License

Copyright 2024 CellRex. All rights reserved.
