import logging

from bson.errors import InvalidId
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from router.biofiles import router as BiofilesRouter
from router.filemanagement import router as FilemanagementRouter
from router.filemanagement import lifespan

description = """
This is the API for the CellRex project. It is a FastAPI application that provides endpoints for uploading and managing biofiles.

The API has two main parts:
- Biofiles: This part is responsible for handling the biofiles. It provides endpoints for uploading, downloading, and deleting biofiles.
- Filemanagement: This part is responsible for managing the files. It provides endpoints for listing the files and getting the metadata of a file.
"""

api_v1_router = APIRouter()
api_v1_router.include_router(BiofilesRouter, tags=["Biofiles"], prefix="/biofiles")
api_v1_router.include_router(
    FilemanagementRouter, tags=["Filemanagement"], prefix="/filemanagement"
)

app_v1 = FastAPI(
    title="CellRex API",
    description=description,
    version="0.1",
    contact={
        "name": "CellRex",
        "url": "https://github.com/cellrex/cellrex",
        "email": "cellrex@outlook.com",
    },
)
app_v1.include_router(api_v1_router)


app = FastAPI(
    title="CellRex API",
    description=description,
    version="0.1",
    contact={
        "name": "CellRex",
        "url": "https://github.com/cellrex/cellrex",
        "email": "cellrex@outlook.com",
    },
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the error details
    logging.error("Validation error for %s: %s", request.url.path, exc.errors())

    # Return the response as JSON
    return JSONResponse(
        status_code=422,
        content={"detail": [str(e) for e in exc.errors()], "body": str(exc.body)},
    )


@app.exception_handler(InvalidId)
async def invalidId_exception_handler(request: Request, exc: InvalidId):
    # Log the error details
    logging.error("InvalidId error for %s: %s", request.url.path, str(exc))

    # Return the response as JSON
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app_v1.get("/", tags=["Root"])
async def read_root_v1():
    return {"message": "Welcome to CellRex API!"}


@app.get("/", response_class=RedirectResponse, tags=["Root"])
async def read_root():
    return "/v1"


# Mount the routers
app.mount("/v1", app_v1)

# Mount the StaticFiles for serving of labdata files. static for dummy data, config for mounted docker
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.mount("/config", StaticFiles(directory="config", html=True), name="config")
app.mount("/protocols", StaticFiles(directory="protocols", html=True), name="protocols")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
