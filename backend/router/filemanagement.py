# Ignore W1203
import asyncio
import errno
import hashlib
import json
import logging
import os
import pathlib
import shutil
import time
from concurrent.futures import ProcessPoolExecutor

from fastapi import (
    APIRouter,
    Body,
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

logger = logging.getLogger(__name__)

router = APIRouter()

hash_cache = {}


class FileWatcher(FileSystemEventHandler):
    def on_any_event(self, event):
        hash_cache.pop(pathlib.Path(event.src_path).name, None)
        logger.debug(event)

        if event.is_directory:
            hash_func = self.calculate_folder_hash
        else:
            hash_func = self.calculate_hash

        match event.event_type:
            case "created" | "modified" | "closed":
                key = pathlib.Path(event.src_path).name
                hash_cache[key] = hash_func(event.src_path)
            case "moved":
                key = pathlib.Path(event.dest_path).name
                hash_cache[key] = hash_func(event.dest_path)

    def calculate_hashes_on_startup(self, directory_path):
        with ProcessPoolExecutor() as executor:
            path = pathlib.Path(directory_path)
            files = [f for f in path.glob("*")]
            logger.info(f"items in upload folder: {files}")

            futures = []
            for item in files:
                if item.is_file():
                    futures.append(executor.submit(self.calculate_hash, item))
                elif item.is_dir():
                    futures.append(executor.submit(self.calculate_folder_hash, item))

            for future in futures:
                result = future.result()
                if result is not None:
                    hash_cache[result["filename"]] = result

    def calculate_hash(self, filepath, retries=5, delay=4):
        logger.info(f"Calculating hash for file: {filepath}")
        filepath = pathlib.Path(filepath)
        key = filepath.name

        start_time = time.time()

        sha256_hash = hashlib.sha256()

        # deal with files being still tranferred (busy file error)
        for attempt in range(retries):
            try:
                with open(filepath, "rb") as f:
                    # Read and update hash in chunks of 64KB
                    for byte_block in iter(lambda: f.read(65536), b""):
                        sha256_hash.update(byte_block)
                break  # If successful, break out of the retry loop
            except IOError as e:
                if e.errno == errno.EBUSY and attempt < retries - 1:
                    logger.warning(f"File is busy, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error calculating hash: {e}",
                    ) from e

        logger.info(
            "Hash calculation for file completed (%.2fs | %s: %s)",
            time.time() - start_time,
            filepath,
            sha256_hash.hexdigest(),
        )

        return {
            "filename": key,
            "hash": sha256_hash.hexdigest(),
            "timestamp": time.time(),
        }

    def calculate_folder_hash(self, folderpath, retries=5, delay=4):
        logger.info(f"Calculating hash for folder: {folderpath}")
        folderpath = pathlib.Path(folderpath)
        key = folderpath.name

        start_time = time.time()

        sha256_hash = hashlib.sha256()

        for root, _, files in os.walk(folderpath):
            for file in sorted(files):  # Sort files to ensure consistent hash
                file_path = os.path.join(root, file)
                for attempt in range(retries):
                    try:
                        with open(file_path, "rb") as f:
                            for byte_block in iter(lambda: f.read(65536), b""):
                                sha256_hash.update(byte_block)
                        break  # If successful, break out of the retry loop
                    except IOError as e:
                        if e.errno == errno.EBUSY and attempt < retries - 1:
                            logger.warning(
                                f"File is busy, retrying in {delay} seconds..."
                            )
                            time.sleep(delay)
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error calculating hash: {e}",
                            ) from e

        logger.info(
            "Hash calculation for folder completed (%.2fs | %s: %s)",
            time.time() - start_time,
            folderpath,
            sha256_hash.hexdigest(),
        )

        return {
            "filename": key,
            "hash": sha256_hash.hexdigest(),
            "timestamp": time.time(),
        }


upload_path = "upload"


def run_observer():
    path = upload_path
    event_handler = FileWatcher()
    event_handler.calculate_hashes_on_startup(path)
    observer = PollingObserver()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


async def startup_event():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_observer)


router.add_event_handler("startup", startup_event)


@router.get(
    "/hash/{filename}",
    summary="Retrieve hash of a file",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
        status.HTTP_200_OK: {"model": GeneralResponse},
    },
)
async def get_hash(filename: str):
    hash_info = hash_cache.get(filename)

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
    upload_folder = pathlib.Path(upload_path)

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
                logger.warning(f"File {f.name} is not a file or directory.")
        except IOError as e:
            if e.errno == errno.EBUSY:
                logger.warning(f"File {f.name} is busy and cannot be accessed.")
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

    except Exception as e:
        print(f"Error moving file: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error moving file: {e}",
        ) from e

    return GeneralResponse(
        data={"status": True},
        message="Files moved successfully",
        code=status.HTTP_200_OK,
    )
