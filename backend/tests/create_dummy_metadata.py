import os
import json
import pathlib
import random
from datetime import datetime, timedelta, date, time
import secrets
import yaml
import requests
from json import JSONEncoder
import numpy as np

from create_dummy_data import generate_dummy_upload_files


def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


class DateTimeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()


def load_config(config_content):
    """
    Load configuration from the provided content.

    Args:
        config_content (str): Configuration content

    Returns:
        dict: Parsed configuration
    """
    return yaml.safe_load(config_content)


def create_db_entry(path_to_filename, experiment_data, file_size, file_hash):
    response = requests.post(
        url="http://localhost:8000/biofiles/",
        json={
            "filecontext": json.loads(
                json.dumps(experiment_data, cls=DateTimeEncoder),
            ),
            "filepath": str(path_to_filename),
            "filesize": file_size,
            "filehash": file_hash,
            "filetype": path_to_filename.suffix,
        },
    )
    assert response.status_code == 200


data_path = pathlib.Path("data")


def output_filepath_component(experiment_data, filename):
    response = requests.post(
        "http://localhost:8000/biofiles/filepath",
        json={
            "experiment_data": json.loads(
                json.dumps(experiment_data, cls=DateTimeEncoder)
            )
        },
    )

    experiment_path = pathlib.Path(response.json()["data"]["experiment_path"])

    complete_filepath: pathlib.Path = data_path / experiment_path / filename

    return complete_filepath


def generate_metadata(config, filepath, num_files: int = 30):
    """
    Generate metadata for files in the specified directory.

    Args:
        config (dict): Configuration dictionary
        generated_files_dir (str): Directory containing generated files

    Returns:
        list: List of generated metadata dictionaries
    """

    filelist = os.listdir(filepath)
    metadata_list = []  # noqa: F841

    for file in filelist:
        # Randomly select parameters
        species_weights = softmax(np.arange(len(config["SPECIES"])))
        species = random.choices(config["SPECIES"], weights=species_weights, k=1)[0]
        origin = random.choice(config["ORIGIN"])
        organ_type = random.choice(config["ORGAN_TYPE"])
        cell_types = config["CELL_TYPE"][organ_type]
        cell_type = random.choice(cell_types)

        # Create influence groups
        influence_groups = {}
        num_groups = random.randint(1, 3)
        influence_types = random.sample(config["INFLUENCE"], num_groups)

        for i, influence in enumerate(influence_types):
            group_key = f"group_{i + 1}"
            if influence == "control":
                influence_groups[group_key] = {
                    "control": {
                        "name": f"Control Group {i + 1}",
                        "wells": random.sample(config["WELLS"], random.randint(1, 3)),
                    }
                }
            elif influence == "sham":
                influence_groups[group_key] = {
                    "sham": {
                        "name": f"Sham Group {i + 1}",
                        "wells": random.sample(config["WELLS"], random.randint(1, 3)),
                        "notes": "Sham procedure performed",
                    }
                }
            elif influence == "pharmacology":
                influence_groups[group_key] = {
                    "pharmacology": {
                        "name": random.choice(config["DRUG"]),
                        "concentration": round(random.uniform(0.1, 100.0), 2),
                        "concentrationUnit": random.choice(config["DRUG_UNIT"]),
                        "exposure": round(random.uniform(0.1, 24.0), 2),
                        "exposureUnit": random.choice(config["TIME_UNIT"]),
                        "wells": random.sample(config["WELLS"], random.randint(1, 3)),
                    }
                }
            elif influence == "radiation":
                influence_groups[group_key] = {
                    "radiation": {
                        "name": random.choice(config["RADIATION"]),
                        "dosage": round(random.uniform(0.1, 10.0), 2),
                        "dosageUnit": random.choice(config["RADIATION_UNIT"]),
                        "exposure": round(random.uniform(0.1, 24.0), 2),
                        "exposureUnit": random.choice(config["TIME_UNIT"]),
                        "irradiationDevice": random.choice(
                            config["IRRADIATION_DEVICE"]
                        ),
                        "wells": random.sample(config["WELLS"], random.randint(1, 3)),
                    }
                }
            elif influence == "disease":
                influence_groups[group_key] = {
                    "disease": {
                        "name": random.choice(config["DISEASE"]),
                        "wells": random.sample(config["WELLS"], random.randint(1, 3)),
                        "notes": "Disease model implementation",
                    }
                }
            elif influence == "stimulus":
                influence_groups[group_key] = {
                    "stimulus": {"name": random.choice(config["STIMULUS"])}
                }

        # Determine lab device
        device_type = random.choice(config["DEVICES"])
        if device_type == "MEA":
            lab_device = {
                "mea": {
                    "name": random.choice(config["DEVICE_MEA"]),
                    "chipType": random.choice(config["MEA_CHIP_TYPE"]),
                    "chipId": random.randint(1000, 9999),
                    "recDur": random.randint(60, 600),
                    "rate": random.choice([20000, 25000, 30000]),
                }
            }
        else:  # Microscope
            lab_device = {
                "microscope": {
                    "type": "Confocal",
                    "name": random.choice(config["DEVICE_MICROSCOPE"]),
                    "magnification": [random.choice(config["MAGNIFICATIONS"])],
                    "task": random.choice(config["MICROSCOPE_TASKS"]),
                    "ifStaining" if random.choice([True, False]) else "ca2Imaging": {
                        "numAntibodies": str(random.randint(1, 3)),
                        "abCon": None,
                        "dyeOth": None,
                        "antibodyGroups": {
                            "antibodyGroup1": {
                                "prim": random.choice(config["ANTIBODY_PRIMARY"]),
                                "sec": random.choice(config["ANTIBODY_SECONDARY"]),
                            }
                        },
                    },
                }
            }

        experiment_date = datetime.now() - timedelta(days=random.randint(0, 30))
        creation_date = experiment_date + timedelta(days=random.randint(1, 29))
        filesize = random.randint(1, 5) * 3e8

        # Generate metadata
        metadata = {
            "filecontext": {
                "species": species,
                "origin": origin,
                "organType": organ_type,
                "cellType": cell_type,
                "brainRegion": [random.choice(config["BRAIN_REGIONS"])]
                if random.choice([True, False])
                else None,
                "protocolNames": [list(config["PROTOCOLS"].keys())[0]]
                if config["PROTOCOLS"]
                else None,
                "protocols": {
                    list(config["PROTOCOLS"].keys())[0]: {
                        "name": list(config["PROTOCOLS"].keys())[0],
                        "path": list(config["PROTOCOLS"].values())[0],
                        "text": "Sample protocol text",
                    }
                }
                if config["PROTOCOLS"]
                else None,
                "keywords": random.sample(config["KEYWORDS"], random.randint(1, 3)),
                "experimenter": np.random.choice(
                    config["EXPERIMENTERS"],
                    size=random.randint(1, 3),
                    replace=False,
                    p=np.divide(
                        np.arange(len(config["EXPERIMENTERS"])),
                        sum(np.arange(len(config["EXPERIMENTERS"]))),
                    ),
                ).tolist(),
                "lab": random.sample(config["LABS"], 1),
                "date": experiment_date.strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "experimentName": f"{organ_type} {cell_type} Study",
                "sampleID": random.randint(0, 9999),
                "ageDIV": random.randint(7, 28),
                "ageDAP": random.randint(1, 60)
                if random.choice([True, False])
                else None,
                "numInfluenceGroups": len(influence_groups),
                "influenceGroups": influence_groups,
                "labDeviceType": device_type,
                "labDevice": lab_device,
                "creationDate": creation_date.isoformat(),
                "filepath": os.path.join(filepath, file),
            },
            "filepath": pathlib.Path(os.path.join(filepath, file)),
            "filesize": filesize,
            "filehash": secrets.token_urlsafe(32),
            "filetype": os.path.splitext(file)[1][1:].upper(),
        }
        if not metadata["filecontext"]["brainRegion"]:
            del metadata["filecontext"]["brainRegion"]

        metadata["filecontext"]["experimentName"] = (
            f"exp_{datetime.now().strftime('%Y%m%d')}_{'-'.join(metadata['filecontext']['experimenter'])}_{'-'.join(metadata['filecontext']['keywords'])}"
        )

        metadata["filepath"] = output_filepath_component(metadata["filecontext"], file)
        metadata["filecontext"]["filepath"] = output_filepath_component(
            metadata["filecontext"], file
        ).as_posix()

        create_db_entry(
            metadata["filepath"],
            metadata["filecontext"],
            metadata["filesize"],
            metadata["filehash"],
        )

        response = requests.post(
            "http://localhost:8000/filemanagement/move",
            json={
                "filename": file,
                "srcpath": "upload",
                "dstpath": pathlib.Path(metadata["filepath"]).parent.as_posix(),
                "filecontext": json.loads(
                    json.dumps(metadata["filecontext"], cls=DateTimeEncoder)
                ),
            },
        )

        assert response.status_code == 200

        print(f"Generated metadata for: {file}")

    return


# Example usage
if __name__ == "__main__":
    # Load configuration
    with open("./backend/tests/resources/labdata.yml", "r") as f:
        config = load_config(f)

    num_files = 8

    # Generate metadata
    generate_dummy_upload_files(output_folder="share/upload", num_files=num_files)
    generate_metadata(config, filepath="share/upload")

    print("\nGenerated metadata for files.")
