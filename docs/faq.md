# CellRex FAQ (Frequently Asked Questions)

-----
# General information

## What is CellRex?
CellRex is a user-friendly full stack application written in Python and built with Python FastAPI and Streamlit. It allows research groups to transfer and manage their research data efficiently, linking biological metadata with experimentally generated files.

## Is CellRex for me?
Yes, CellRex is designed to be inclusive and beneficial for all research groups. While it is particularly suited for workflows similar to ours, the concepts can be adapted for various research fields. We welcome contributions from others, as the open-source nature of CellRex allows users to adjust the code to fit their specific needs.

## Is CellRex free?
Yes, CellRex is free to use. While we hold the copyright, you can access the source code from our GitHub repository.

## How do I cite CellRex?
We are currently working on a publication. In the meantime, you can cite CellRex in APA format as follows:
```
CellRex. (2023). CellRex (1.0) [Software]. CellRex. https://github.com/cellrex
```

# Getting started

## How do I get started with CellRex?
To get started with CellRex, you can download the application from our GitHub repository. Follow the installation instructions provided in the documentation to set up the environment. Once installed, you can begin uploading and managing your research data.


## What are the system requirements for running CellRex?
CellRex requires a system that supports Docker or Podman, as it is containerized. Ensure that you have sufficient resources (CPU, RAM, and storage) to handle your data needs. Specific requirements may vary based on the size and complexity of your datasets.

In our setup, CellRex runs via Podman on an Ubuntu 24.04 lts (i7, 16GB RAM), which has mounted folders through a NAS (btrfs). Our largest files are about 25 GB in size, but it should be mentioned that the hash calculation takes longer for large files.


# Usage

## Is CellRex FAIR?
Indeed, CellRex was developed in accordance with FAIR (Findable, Accessible, Interoperable, and Reusable) principles from its inception. We prioritize these principles to ensure that our software meets the needs of researchers and users in a data-driven environment.

## Is CellRex save?
CellRex relies on the hardware, so we recommend RAID and backup for your infrastructure. The container approach allows applications to run consistently across different environments. This isolation helps manage dependencies and avoid conflicts, while also enabling efficient scaling and resource usage.

A variety of data consistency checking mechanisms have been implemented, but it should be noted that the project is open source and therefore the possibility of bugs remaining present cannot be ruled out.

## Where is the data stored in CellRex?
Uploaded files are moved to the destination specified in the metadata, creating a structured file path. Along with the uploaded file, the metadata is saved as a JSON file, using the original filename with a .json extension. Additionally, the metadata is stored in a SQLite database for faster searching and validation.

## Which file types are supported?
CellRex supports all file types except for .demofile. We currently have a trial implementation where you can interact with the app, but no entries will be written to the database, and no files will be moved. Please note that moving entire folders is not supported at this time, but we may implement this feature in the future if there is demand.
It is recommended that no spaces or special characters be included within the filename.

## Is there a maximum file size?
To the best of our knowledge, the maximum file size is limited by the underlying file system. In our setup, CellRex runs via Podman on an Ubuntu 24.04 lts (i7, 16GB RAM), which has mounted folders through a NAS (btrfs). Our largest files are about 25 GB in size, but it should be mentioned that the hash calculation takes longer for large files.

## How does a typical upload process via the GUI work?
To upload files using the GUI, follow these steps:
- Place the files you want to upload into the designated upload folder.
- Select the file from the list on the upload page.
- Adjust the metadata as needed on the upload page.
- Finally, click the upload button.

During the upload, the file path is created, and the file is moved from the upload folder to its destination. Pro tip: Download the metadata as a JSON template for your next upload. Make any necessary adjustments to the template and upload your file. You can always get a new template from a fitting reference experiment on you hard disk as they are compatible. 

## How do I update the metadata of an existing file?
To update the metadata of an existing file, select the same raw file on the upload page and adjust the metadata as needed. You will see warnings indicating that the file already exists in the database at that specific path. If the filepath changes due to metadata updates, you will need to manually remove the old path to avoid duplicates.

## How can I open .json file?
To open a .json file, you can use any text editor or a specialized JSON viewer. You can also use a web browser to display the contents of a JSON file directly. If you want to read the file within a Python script, you can use the built-in json module.

If you want to view or edit the file within CellRex, you can upload it through the upload page as template, and the application will process the data accordingly. Ensure that the JSON file is formatted correctly to avoid any errors during processing.

# Admin / Configuration

## How can I remove an entry from the database?
Removing an entry is straightforward. First, locate the file you wish to remove and obtain its _id using the search page. Note that the _id is not the same as the first number of every entry; it is an index from the search results. To delete the entry, use the API: first call GET /biofiles/id/{id} to verify the entry, and then use DELETE /biofiles/id/{id} to remove it. This process only deletes the database entry, not the file from the filepath.

## How can I add new keywords, experimenters, etc.?
Adding new keywords, experimenters, etc. is an easy task. You have to stop the containers by running docker compose down or podman-compose down in the directory containing the docker-compose.yml file (For more information on compose see the respective documentation). Then, update labdata.yml with the necessary changes. After saving labdata.yml, restart the containers with docker compose up or podman-compose up to see the changes in the upload page.

## How can I integrate a new protocol?
To integrate a new protocol, follow the same initial steps as adding new keywords or experimenters. First, stop the containers by running docker compose down or podman-compose down in the directory containing the docker-compose.yml file (For more information on compose see the respective documentation). Place your my_new_protocol.txt file, which describes the protocol, in the protocols folder. Then, update labdata.yml with the protocol name (the filename without the extension) and the path to the protocol file. After saving labdata.yml, restart the containers with docker compose up or podman-compose up to see the new protocol in the upload page.

## Can I adjust the ordering of the created file path?
Yes, you can adjust the ordering of the file path, but it is recommended to do this before using CellRex in a production environment. Changes made later are not supported. To adjust the ordering, you will need to modify the list within the backend router function. We have evaluated our file path composition and recommend sticking with the default settings for optimal performance.


# Troubleshooting

## Why does restarting CellRex take some time?
During the startup process of CellRex, the application calculates the hash values of all files located in the upload folder. To improve startup time, we recommend clearing the upload folder of unnecessary files before restarting.

## Does CellRex require special permissions?
CellRex only requires read and write permissions for the preconfigured folders. No additional permissions are necessary.
