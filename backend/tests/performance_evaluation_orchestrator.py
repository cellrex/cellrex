#!/usr/bin/env python3
"""
Incremental data generation and ingestion with performance testing.
"""
# pylint: disable=missing-function-docstring,import-outside-toplevel

import argparse
import json
import logging
import pathlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from data_generation_utils import generate_dummy_files
from metadata_generation_utils import generate_metadata_for_files
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging to both console and file
LOG_FILE = "./performance_test.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, mode="a")],
)
logger = logging.getLogger(__name__)

# Default stages for incremental testing
DEFAULT_STAGES = [10, 50, 100, 500, 1000, 10000, 100000, 250000, 500000, 1000000]
RESULTS_DIR = pathlib.Path("./performance_results")
API_BASE_URL = "http://localhost:8000/v1"


# --- Performance Tracker ---
class PerformanceTracker:
    """Track and report performance metrics for each stage."""

    def __init__(self, output_dir: pathlib.Path = RESULTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.session = create_session_with_retries()
        self.results = []
        self.start_time = time.time()
        self.total_files = 0
        self.total_successful = 0
        self.api_response_times = []

    def record_stage(
        self,
        stage_name: str,
        files_generated: int,
        files_processed: int,
        generation_time: float,
        processing_time: float,
        success_rate: float,
        additional_metrics: Optional[dict] = None,
    ) -> dict:
        self.total_files += files_generated
        self.total_successful += int(files_processed * success_rate)
        total_time = time.time() - self.start_time
        stage_result = {
            "stage": stage_name,
            "timestamp": datetime.now().isoformat(),
            "files_in_stage": files_generated,
            "files_processed_in_stage": files_processed,
            "generation_time_seconds": generation_time,
            "processing_time_seconds": processing_time,
            "generation_files_per_second": files_generated / generation_time
            if generation_time > 0
            else 0,
            "processing_files_per_second": files_processed / processing_time
            if processing_time > 0
            else 0,
            "success_rate": success_rate,
            "cumulative_metrics": {
                "total_files": self.total_files,
                "total_successful": self.total_successful,
                "total_elapsed_time": total_time,
                "overall_files_per_second": self.total_files / total_time
                if total_time > 0
                else 0,
            },
        }
        if additional_metrics:
            stage_result["additional_metrics"] = additional_metrics
        self.results.append(stage_result)
        self._save_results()
        self._log_stage_summary(stage_result)
        return stage_result

    def _log_stage_summary(self, result: dict) -> None:
        logger.info("=== Stage %s Complete ===", result["stage"])
        logger.info("Files generated: %s", result["files_in_stage"])
        logger.info("Files processed: %s", result["files_processed_in_stage"])
        logger.info("Generation time: %.2f seconds", result["generation_time_seconds"])
        logger.info("Processing time: %.2f seconds", result["processing_time_seconds"])
        logger.info(
            "Generation rate: %.2f files/sec", result["generation_files_per_second"]
        )
        logger.info(
            "Processing rate: %.2f files/sec", result["processing_files_per_second"]
        )
        logger.info("Success rate: %.2f%%", result["success_rate"] * 100)
        logger.info(
            "Cumulative total: %s files", result["cumulative_metrics"]["total_files"]
        )
        logger.info(
            "Overall rate: %.2f files/sec",
            result["cumulative_metrics"]["overall_files_per_second"],
        )

    def _save_results(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.output_dir / f"performance_results_{timestamp}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "results": self.results,
                    "summary": {
                        "total_files": self.total_files,
                        "total_successful": self.total_successful,
                        "total_time": time.time() - self.start_time,
                    },
                },
                f,
                indent=2,
            )
        logger.info("Results saved to %s", result_file)


# --- API/DB helpers ---
def create_session_with_retries() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def create_db_entry(metadata: dict, session: requests.Session) -> bool:
    try:
        response = session.post(
            url=f"{API_BASE_URL}/biofiles/",
            json={
                "filecontext": metadata["filecontext"],
                "filepath": metadata["filepath"],
                "filesize": metadata["filesize"],
                "filetype": metadata["filetype"],
                "filehash": metadata["filehash"],
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Failed to create DB entry: %s", e)
        return False


def move_file_api(
    filename: str,
    srcpath: str,
    dstpath: str,
    filecontext: dict,
    session: requests.Session,
) -> bool:
    try:
        response = session.post(
            f"{API_BASE_URL}/filemanagement/move",
            json={
                "filename": filename,
                "srcpath": srcpath,
                "dstpath": dstpath,
                "filecontext": filecontext,
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Failed to move file: %s", e)
        return False


# --- Main Orchestration ---
def generate_and_ingest_incrementally(
    config: Dict[str, Any],
    output_dir: str,
    stages: List[int],
    min_size_kb: int = 10,
    max_size_kb: int = 500,
) -> None:
    """
    Generate and ingest files incrementally, recording performance at each stage.

    Args:
        config_path: Configuration dictionary
        output_dir: Directory to store generated files
        stages: List of cumulative file counts for each stage
        min_size_kb: Minimum file size in KB
        max_size_kb: Maximum file size in KB
    """
    # Initialize performance tracker
    tracker = PerformanceTracker()

    # Ensure stages are in ascending order
    stages = sorted(stages)
    upload_path = pathlib.Path(output_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    prev_stage = 0
    tracker = PerformanceTracker()
    session = tracker.session
    for stage in stages:
        files_to_generate = stage - prev_stage
        if files_to_generate <= 0:
            logger.warning(
                "Stage %s is not greater than previous stage %s. Skipping.",
                stage,
                prev_stage,
            )
            continue
        logger.info(
            "Starting stage %s: Generating %s new files", stage, files_to_generate
        )
        stage_start_time = time.time()
        # Step 1: Generate dummy files
        generation_start = time.time()
        generated_files = generate_dummy_files(
            output_folder=str(upload_path),
            num_files=files_to_generate,
            min_size_kb=min_size_kb,
            max_size_kb=max_size_kb,
        )
        generation_time = time.time() - generation_start
        # Step 2: Generate metadata for these files
        filepaths = [upload_path / fname for fname in generated_files]
        metadata_list = generate_metadata_for_files(config, filepaths)
        # Step 3: Create DB entries and move files via API
        processing_start = time.time()
        successful = 0
        for meta, fname in zip(metadata_list, generated_files):
            db_ok = create_db_entry(meta, session)
            move_ok = move_file_api(
                filename=fname,
                srcpath=str(upload_path),
                dstpath=str(upload_path),  # Adjust as needed for your workflow
                filecontext=meta["filecontext"],
                session=session,
            )
            if db_ok and move_ok:
                successful += 1
        processing_time = time.time() - processing_start
        success_rate = successful / files_to_generate if files_to_generate > 0 else 0
        tracker.record_stage(
            stage_name=f"files_{stage}",
            files_generated=files_to_generate,
            files_processed=files_to_generate,
            generation_time=generation_time,
            processing_time=processing_time,
            success_rate=success_rate,
            additional_metrics={
                "stage_total_time": time.time() - stage_start_time,
            },
        )
        prev_stage = stage
    logger.info("=== Incremental Generation and Ingestion Complete ===")


def main():
    parser = argparse.ArgumentParser(
        description="Incrementally generate and ingest files with performance testing"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="resources/labdata.yml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="share/performance_test",
        help="Base directory to store generated files",
    )
    parser.add_argument(
        "--stages",
        type=int,
        nargs="+",
        default=DEFAULT_STAGES,
        help=f"File count stages for incremental testing (default: {DEFAULT_STAGES})",
    )
    parser.add_argument(
        "--min-size-kb", type=int, default=10, help="Minimum file size in KB"
    )
    parser.add_argument(
        "--max-size-kb", type=int, default=500, help="Maximum file size in KB"
    )
    args = parser.parse_args()
    # Load config (implement or import load_config as needed)
    import yaml

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    try:
        generate_and_ingest_incrementally(
            config=config,
            output_dir=args.output_dir,
            stages=args.stages,
            min_size_kb=args.min_size_kb,
            max_size_kb=args.max_size_kb,
        )
    except Exception as e:
        logger.error("Error running incremental generation: %s", e, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
