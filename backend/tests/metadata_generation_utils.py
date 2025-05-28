#!/usr/bin/env python3
"""
Generate metadata for test files.
"""

import logging
import pathlib
import random
import sys
from datetime import date, datetime, time, timedelta
from json import JSONEncoder
from typing import Any, Dict, List

import numpy as np
import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.tests.data_generation_utils import generate_dummy_upload_files

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
API_BASE_URL = "http://localhost:8000/v1"
DATA_PATH = pathlib.Path("data")


class DateTimeEncoder(JSONEncoder):
    """JSON encoder that can handle datetime objects."""

    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()
        return super().default(o)


def create_session_with_retries() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def softmax(x: np.ndarray) -> np.ndarray:
    """Calculate softmax values for the input array."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing configuration data
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError) as e:
        logger.error("Failed to load config: %s", e)
        raise


def generate_metadata_for_files(
    config: Dict[str, Any], filepaths: List[pathlib.Path]
) -> List[Dict[str, Any]]:
    """
    Generate metadata for a list of files based on the provided config.

    Args:
        config: Configuration dictionary
        filepaths: List of pathlib.Path objects for files

    Returns:
        List of generated metadata dictionaries
    """
    metadata_list = []
    for file_path in filepaths:
        # Randomly select parameters
        species = random.choice(config["SPECIES"])
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
        filesize = file_path.stat().st_size

        # Generate metadata
        file_context = {
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
            "experimenter": random.sample(
                config["EXPERIMENTERS"], random.randint(1, 3)
            ),
            "lab": random.sample(config["LABS"], 1),
            "date": experiment_date.strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "experimentName": f"{organ_type} {cell_type} Study",
            "sampleID": random.randint(0, 9999),
            "ageDIV": random.randint(7, 28),
            "ageDAP": random.randint(1, 60) if random.choice([True, False]) else None,
            "numInfluenceGroups": len(influence_groups),
            "influenceGroups": influence_groups,
            "labDeviceType": device_type,
            "labDevice": lab_device,
            "creationDate": creation_date.isoformat(),
            "filepath": str(file_path),
        }

        if not file_context["brainRegion"]:
            del file_context["brainRegion"]

        file_context["experimentName"] = (
            f"exp_{datetime.now().strftime('%Y%m%d')}_{'-'.join(file_context['experimenter'])}_{'-'.join(file_context['keywords'])}"  # pylint: disable=C0301
        )

        metadata = {
            "filecontext": file_context,
            "filepath": str(file_path),
            "filesize": filesize,
            "filetype": file_path.suffix[1:],
        }
        metadata_list.append(metadata)
    logger.info("Generated metadata for %d files", len(metadata_list))
    return metadata_list


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate metadata for test files")
    parser.add_argument(
        "--config",
        type=str,
        default="./backend/tests/resources/labdata.yml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--files", type=int, default=8, help="Number of files to generate"
    )
    parser.add_argument(
        "--upload-dir",
        type=str,
        default="share/upload",
        help="Directory to store generated files",
    )
    parser.add_argument(
        "--generate-files",
        action="store_true",
        help="Generate dummy files before creating metadata",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        logger.info("Loading configuration from %s", args.config)
        config = load_config(args.config)

        # Generate files if requested
        if args.generate_files:
            logger.info("Generating %d dummy files in %s", args.files, args.upload_dir)
            generate_dummy_upload_files(
                output_folder=args.upload_dir,
                num_files=args.files,
                min_size_kb=10000,
                max_size_kb=1000000,
            )

        # Generate metadata
        logger.info("Generating metadata for files")
        filepaths = [
            pathlib.Path(args.upload_dir) / f
            for f in pathlib.Path(args.upload_dir).iterdir()
            if f.is_file()
        ]
        generate_metadata_for_files(config, filepaths)

        logger.info("Metadata generation complete")

    except Exception as e:
        logger.error("Error running script: %s", e, exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
