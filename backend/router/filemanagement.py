# pylint: disable=W0602
import errno
import hashlib
import json
import logging
import os
import pathlib
import shutil
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import (
    APIRouter,
    Body,
    FastAPI,
    HTTPException,
    status,
)
from fastapi.encoders import jsonable_encoder
from model.filemanagement import FileMove
from model.response import (
    FileListResponse,
    GeneralResponse,
    NotFoundResponse,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

# Configure logging for Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global variables
HASH_CACHE = {}
UPLOAD_PATH = "upload"
OBSERVER = None
EXECUTOR = None


class FileWatcher(FileSystemEventHandler):
    """File system event handler to monitor changes in the upload directory."""

    def on_any_event(self, event):
        """Handle file system events."""
        logger.info("Event: %s - %s", event.event_type, event.src_path)

        # Handle deletion events first
        if event.event_type == "deleted":
            key = pathlib.Path(event.src_path).name
            HASH_CACHE.pop(key, None)
            logger.info("Removed hash for %s", key)
            return

        # For other events, submit to thread pool
        global EXECUTOR
        assert EXECUTOR is not None, "Executor not initialized"

        if event.is_directory:
            EXECUTOR.submit(
                self.calculate_folder_hash,
                event.src_path if event.event_type != "moved" else event.dest_path,
            )
        else:
            EXECUTOR.submit(
                self.calculate_hash,
                event.src_path if event.event_type != "moved" else event.dest_path,
            )

        # For moved events, remove old hash
        if event.event_type == "moved":
            key = pathlib.Path(event.src_path).name
            HASH_CACHE.pop(key, None)

    def calculate_hashes_on_startup(self, directory_path):
        """Calculate hashes for all files in directory."""
        path = pathlib.Path(directory_path)
        files = [f for f in path.glob("*")]
        logger.info("Items in upload folder: %s", len(files))

        # Use thread pool for parallel processing
        global EXECUTOR
        assert EXECUTOR is not None, "Executor not initialized"
        futures = []

        for item in files:
            if item.is_file():
                futures.append(EXECUTOR.submit(self.calculate_hash, item))
            elif item.is_dir():
                futures.append(EXECUTOR.submit(self.calculate_folder_hash, item))

        # Wait for all calculations to complete
        for future in futures:
            try:
                result = future.result()
                if result is not None:
                    HASH_CACHE[result["filename"]] = result
                    logger.info("Added hash for %s", result["filename"])
            except Exception as e:
                logger.error(
                    "Error calculating hash: %s\n%s", e, traceback.format_exc()
                )

    def calculate_hash(self, filepath, retries=3, delay=2):
        """Calculate hash for a file with optimized parameters."""
        logger.debug("Calculating hash for file: %s", filepath)
        filepath = pathlib.Path(filepath)
        key = filepath.name

        start_time = time.time()
        sha256_hash = hashlib.sha256()

        buffer_size = 1024 * 1024  # 1MB buffer

        for attempt in range(retries):
            try:
                with open(filepath, "rb") as f:
                    # Read and update hash in chunks
                    for byte_block in iter(lambda: f.read(buffer_size), b""):  # pylint: disable=W0640
                        sha256_hash.update(byte_block)
                break
            except IOError as e:
                if e.errno == errno.EBUSY and attempt < retries - 1:
                    logger.warning("File is busy, retrying in %d seconds...", delay)
                    time.sleep(delay)
                else:
                    logger.error("Error calculating hash: %s", e)
                    return None

        hash_value = sha256_hash.hexdigest()
        duration = time.time() - start_time
        logger.debug("Hash calculation completed in %.2fs: %s", duration, filepath)

        result = {
            "filename": key,
            "hash": hash_value,
            "timestamp": time.time(),
        }

        # Update the cache
        HASH_CACHE[key] = result
        return result

    def calculate_folder_hash(self, folderpath, retries=3, delay=2):
        """Calculate hash for a folder with optimized parameters."""
        logger.debug("Calculating hash for folder: %s", folderpath)
        folderpath = pathlib.Path(folderpath)
        key = folderpath.name

        start_time = time.time()
        sha256_hash = hashlib.sha256()

        buffer_size = 1024 * 1024  # 1MB buffer

        try:
            # Get a sorted list of all files for consistent hashing
            all_files = []
            for root, _, files in os.walk(folderpath):
                for file in files:
                    all_files.append(os.path.join(root, file))
            all_files.sort()

            # Hash each file
            for file_path in all_files:
                rel_path = os.path.relpath(file_path, folderpath)
                sha256_hash.update(
                    rel_path.encode()
                )  # Include the path in the hash # TODO: Is this desired? Currently chnaging childfolders changes the hash

                for attempt in range(retries):
                    try:
                        with open(file_path, "rb") as f:
                            for byte_block in iter(lambda: f.read(buffer_size), b""):  # pylint: disable=W0640
                                sha256_hash.update(byte_block)
                        break
                    except IOError as e:
                        if e.errno == errno.EBUSY and attempt < retries - 1:
                            logger.warning(
                                "File is busy, retrying in %d seconds...", delay
                            )
                            time.sleep(delay)
                        else:
                            logger.error("Error processing file %s: %s", file_path, e)
                            return None

            hash_value = sha256_hash.hexdigest()
            duration = time.time() - start_time
            logger.debug(
                "Folder hash calculation completed in %.2fs: %s", duration, folderpath
            )

            result = {
                "filename": key,
                "hash": hash_value,
                "timestamp": time.time(),
            }

            # Update the cache
            HASH_CACHE[key] = result
            return result

        except Exception as e:
            logger.error(
                "Error calculating folder hash: %s\n%s", e, traceback.format_exc()
            )
            return None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    global OBSERVER, EXECUTOR

    logger.info("Application startup - initializing file watcher")

    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_PATH, exist_ok=True)

    # Initialize thread pool
    EXECUTOR = ThreadPoolExecutor(max_workers=os.cpu_count())

    # Create file watcher
    event_handler = FileWatcher()

    try:
        # Calculate initial hashes
        logger.info("Calculating initial file hashes...")
        event_handler.calculate_hashes_on_startup(UPLOAD_PATH)
        logger.info(
            "Initial hash calculation complete - %d items cached", len(HASH_CACHE)
        )

        # Start file observer
        OBSERVER = PollingObserver()
        OBSERVER.schedule(event_handler, UPLOAD_PATH, recursive=False)
        OBSERVER.start()
        logger.info("File observer started successfully")

        # Yield control back to FastAPI
        yield

    except Exception as e:
        logger.error("Error during startup: %s\n%s", e, traceback.format_exc())
        # Still yield control to allow proper shutdown
        yield
    finally:
        # Shutdown logic
        logger.info("Application shutting down - cleaning up resources")

        # Stop the observer
        if OBSERVER and OBSERVER.is_alive():
            OBSERVER.stop()
            OBSERVER.join(timeout=5)
            logger.info("File observer stopped")

        # Shutdown thread pool
        if EXECUTOR:
            EXECUTOR.shutdown(wait=False)
            logger.info("Thread pool shut down")

        # Clear cache
        HASH_CACHE.clear()
        logger.info("Hash cache cleared")


# Create FastAPI app and router
router = APIRouter()


# Add your existing routes to the router
@router.get(
    "/hash/{filename}",
    summary="Retrieve hash of a file",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
        status.HTTP_200_OK: {"model": GeneralResponse},
    },
)
async def get_hash(filename: str):
    hash_info = HASH_CACHE.get(filename)

    if hash_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return GeneralResponse(
        data={"hash": hash_info["hash"]},
        message="Hash retrieved successfully",
        code=status.HTTP_200_OK,
    )


@router.get(
    "/filesize/{filepath:path}",
    summary="Retrieve size of a file",
    responses={status.HTTP_200_OK: {"model": GeneralResponse}},
)
async def get_filesize(filepath: str):
    file_size = os.path.getsize(pathlib.Path(filepath))

    return GeneralResponse(
        data={"size": file_size},
        message="File size retrieved successfully",
        code=status.HTTP_200_OK,
    )


@router.get(
    "/filelist/upload",
    summary="List files in the upload folder",
    responses={
        status.HTTP_200_OK: {"model": GeneralResponse},
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
    },
)
async def get_upload_files():
    upload_folder = pathlib.Path(UPLOAD_PATH)

    # only add file non-busy files to the list
    file_list = []
    for f in upload_folder.iterdir():
        try:
            if f.is_file():
                with open(f, "rb"):
                    file_list.append(f.name)
            elif f.is_dir():
                # walk through the directory to check if all files are accessible
                for root, _, files in os.walk(f):
                    for file in files:
                        with open(os.path.join(root, file), "rb"):
                            pass
                file_list.append(f.name)
            else:
                logger.warning("File %s is not a file or directory.", f.name)
        except IOError as e:
            if e.errno == errno.EBUSY:
                logger.warning("File %s is busy and cannot be accessed.", f.name)
            else:
                raise

    if not file_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return FileListResponse(
        data=file_list,
        message="File list retrieved successfully",
        code=status.HTTP_200_OK,
    )


@router.get(
    "/exists/{filepath:path}",
    summary="Check if a path exists",
    responses={
        status.HTTP_200_OK: {"model": GeneralResponse},
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
    },
)
async def check_path_exists(filepath: str):
    if not pathlib.Path(filepath).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return GeneralResponse(
        data={"exists": True},
        message="Path exists",
        code=status.HTTP_200_OK,
    )


@router.get(
    "/list/{filepath:path}",
    summary="List files or directories in a path",
    responses={
        status.HTTP_200_OK: {"model": FileListResponse},
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
    },
)
async def list_files(filepath: str):
    path = pathlib.Path(filepath)

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    file_list = [f.name for f in path.iterdir()]

    logger.info("Listing files in %s: %s", filepath, file_list)

    return FileListResponse(
        data=file_list,
        message="File list retrieved successfully",
        code=status.HTTP_200_OK,
    )


@router.post(
    "/move",
    summary="Move a data file with accompanying metadata json-file",
    responses={status.HTTP_200_OK: {"model": GeneralResponse}},
)
async def move_file(file_move: FileMove = Body(...)):
    try:
        file_move.dstpath.mkdir(parents=True, exist_ok=True)

        with open(
            file_move.srcpath / file_move.jsonfilename, "w", encoding="utf-8"
        ) as json_file:
            json.dump(file_move.filecontext.model_dump(exclude_unset=True), json_file)

        shutil.move(
            file_move.srcpath / file_move.filename,
            file_move.dstpath / file_move.filename,
        )

        shutil.move(
            file_move.srcpath / file_move.jsonfilename,
            file_move.dstpath / file_move.jsonfilename,
        )

        logger.info("Moved file from %s to %s", file_move.srcpath, file_move.dstpath)
        logger.info("Moved json from %s to %s", file_move.srcpath, file_move.dstpath)

    except Exception as e:
        print(f"Error moving file: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error moving file: {e}; Files in upload: {os.listdir(file_move.srcpath)}",
        ) from e

    return GeneralResponse(
        data={"status": True},
        message="Files moved successfully",
        code=status.HTTP_200_OK,
    )
