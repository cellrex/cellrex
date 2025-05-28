#!/usr/bin/env python3
"""
Generate dummy files for performance testing.
"""

import logging
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def generate_dummy_upload_files(
    output_folder="share/upload", num_files=30, min_size_kb=1, max_size_kb=500
) -> list[str]:
    """
    Generate dummy files for performance testing with unique names and varied sizes.

    Args:
        output_folder (str): Path to the folder where files will be saved
        num_files (int): Number of files to generate
        min_size_kb (int): Minimum file size in KB
        max_size_kb (int): Maximum file size in KB

    Returns:
        list: List of generated filenames
    """
    # Ensure the output folder exists
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    generated_files = []

    # File extensions to use
    extensions = [".dat", ".txt", ".csv", ".xml", ".bin", ".d3d"]

    # Track progress for large file counts
    report_interval = max(1, min(1000, num_files // 10))

    logger.info("Generating %d files in '%s'...", num_files, output_folder)

    for i in range(num_files):
        # Generate a unique filename using timestamp and random characters
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        random_chars = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        extension = random.choice(extensions)

        # Create a unique filename guaranteed not to collide
        filename = f"test_{timestamp}_{random_chars}{extension}"
        filepath = output_path / filename

        # Generate random file size between min and max
        size_kb = random.randint(min_size_kb, max_size_kb)
        size_bytes = size_kb * 1024

        # Create file with random data for efficiency
        with open(filepath, "wb") as f:
            # Write in chunks for memory efficiency
            chunk_size = min(size_bytes, 64 * 1024)  # 64KB chunks
            remaining = size_bytes

            while remaining > 0:
                # Generate random bytes - more efficient than text for large files
                write_size = min(remaining, chunk_size)
                f.write(os.urandom(write_size))
                remaining -= write_size

        generated_files.append(filename)

        # Progress reporting for large file counts
        if (i + 1) % report_interval == 0 or i + 1 == num_files:
            elapsed = time.time() - start_time
            files_per_second = (i + 1) / elapsed if elapsed > 0 else 0
            logger.info(
                "Progress: %d/%d files created (%.1f%%) - Rate: %.1f files/sec",
                i + 1,
                num_files,
                (i + 1) / num_files * 100,
                files_per_second,
            )

    total_time = time.time() - start_time
    avg_time_per_file = total_time / num_files if num_files > 0 else 0
    total_size_mb = sum(os.path.getsize(output_path / f) for f in generated_files) / (
        1024 * 1024
    )

    logger.info(
        "\n=== Performance Summary ===\n"
        "Total files created   : %d\n"
        "Total time taken      : %.2f seconds\n"
        "Average time per file : %.2f ms\n"
        "Files per second      : %.2f\n"
        "Total data generated  : %.2f MB\n"
        "==========================\n",
        num_files,
        total_time,
        avg_time_per_file * 1000,
        num_files / total_time,
        total_size_mb,
    )

    return generated_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate dummy files with random bytes inside for performance testing"
    )
    parser.add_argument(
        "--files", type=int, default=30, help="Number of files to generate"
    )
    parser.add_argument(
        "--folder", type=str, default="share/upload", help="Output folder"
    )
    parser.add_argument(
        "--min-size", type=int, default=1, help="Minimum file size in KB"
    )
    parser.add_argument(
        "--max-size", type=int, default=500, help="Maximum file size in KB"
    )

    args = parser.parse_args()

    files = generate_dummy_upload_files(
        output_folder=args.folder,
        num_files=args.files,
        min_size_kb=args.min_size,
        max_size_kb=args.max_size,
    )
    print(f"\nGenerated {len(files)} files in '{args.folder}'")
