import asyncio
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
        if event.is_directory:
            return
        hash_cache.pop(pathlib.Path(event.src_path).name, None)
        logger.info(f"File {event.src_path} has been {event.event_type}")
        if event.event_type in ["created", "modified", "moved", "closed"]:
            key = pathlib.Path(event.src_path).name
            hash_cache[key] = self.calculate_hash(event.src_path)

    def calculate_hashes_on_startup(self, directory_path):
        with ProcessPoolExecutor() as executor:
            path = pathlib.Path(directory_path)
            files = [f for f in path.glob("*") if f.is_file()]
            logger.info(f"files in upload folder: {files}")
            results = executor.map(self.calculate_hash, files)

        for result in results:
            if result is not None:
                hash_cache[result["filename"]] = result

    def calculate_hash(self, filepath):
        filepath = pathlib.Path(filepath)
        key = filepath.name

        start_time = time.time()
        if not filepath.is_file():
            logger.error(f"Hash calculation: File not found at {filepath}")
            return

        sha256_hash = hashlib.sha256()

        try:
            with open(filepath, "rb") as f:
                # Read and update hash in chunks of 64KB
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculating hash: {e}",
            ) from e

        logger.info(
            "Hash calculation completed (%.2fs | %s: %s)",
            time.time() - start_time,
            filepath,
            sha256_hash.hexdigest(),
        )

        return {
            "filename": key,
            "hash": sha256_hash.hexdigest(),
            "timestamp": time.time(),
        }


def run_observer():
    # TODO: Refactor to use environment variable here and in other places
    path = "data/upload"
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
    # TODO: Better way to fix the bug?
    if pathlib.Path(filename).suffix == ".invalid":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

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
    upload_folder = pathlib.Path("data/upload")

    file_list = [f.name for f in upload_folder.iterdir() if f.is_file()]

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
