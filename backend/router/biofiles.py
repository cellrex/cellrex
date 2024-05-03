import os
from typing import List, Optional
import pathlib

from database.sqlite import SQLiteDatabase
from fastapi import APIRouter, Body, HTTPException, Path, status
from fastapi.encoders import jsonable_encoder
from model.biofile import Biofile, FilecontextOptional
from model.response import (
    BiofileResponse,
    DatabaseErrorResponse,
    GeneralResponse,
    NotFoundResponse,
    ServerErrorResponse,
)
from model.search import SearchModel

router = APIRouter()

if os.getenv("DATABASE_BACKEND") == "sqlite":
    DB: SQLiteDatabase = SQLiteDatabase()
else:
    raise NotImplementedError("Only SQLite is supported at the moment")


@router.get(
    "/all",
    summary="Retrieve all biofiles present in the database",
    response_model=List[BiofileResponse],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
    },
    response_model_exclude_none=True,
)
async def get_biofiles():
    biofiles = await DB.retrieve_biofiles()

    if not biofiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return biofiles


@router.post(
    "/",
    summary="Add a new biofile into to the database",
    status_code=status.HTTP_201_CREATED,
    response_model=GeneralResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ServerErrorResponse},
    },
)
async def add_biofile(biofile: Biofile = Body(...)):
    biofile_id: str = await DB.add_biofile(biofile)

    if not biofile_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(ServerErrorResponse()),
        )

    return GeneralResponse(
        data={"id": biofile_id},
        message="Biofile added successfully",
        code=status.HTTP_201_CREATED,
    )


@router.get(
    "/id/{id}",
    summary="Retrieve a biofile with a matching ID",
    response_model=BiofileResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse}},
    response_model_exclude_none=True,
)
async def get_biofile_data_by_id(id: str):
    biofile: Biofile = await DB.retrieve_biofile_by_id(id)

    if not biofile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return biofile


@router.put(
    "/id/{id}",
    summary="Update a biofile with a matching ID",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BiofileResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse},
    },
    response_model_exclude_none=True,
)
async def update_biofile_data_by_id(id: str, biofile: Biofile = Body(...)):
    updated_biofile = await DB.update_biofile_by_id(id, biofile)

    if not updated_biofile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return updated_biofile


@router.delete(
    "/id/{id}",
    summary="Delete a biofile with a matching ID",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse}},
)
async def delete_biofile_data_by_id(id: str):
    del_biofile = await DB.delete_biofile_by_id(id)

    if not del_biofile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )

    return GeneralResponse(
        data={"id": id},
        message="Biofile deleted successfully",
        code=status.HTTP_200_OK,
    )


@router.get(
    "/path/{filepath:path}",
    summary="Retrieve biofiles with a matching path",
    response_model=List[BiofileResponse],
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse}},
    response_model_exclude_none=True,
)
async def get_biofile_data_by_path(filepath: str = Path(...)):
    biofiles = await DB.retrieve_biofiles_by_key("filepath", filepath)
    if not biofiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )
    return biofiles


@router.get(
    "/hash/{filehash}",
    summary="Retrieve biofiles with a matching hash",
    response_model=List[BiofileResponse],
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse}},
    response_model_exclude_none=True,
)
async def get_biofile_data_by_hash(filehash: str):
    biofiles = await DB.retrieve_biofiles_by_key("filehash", filehash)
    if not biofiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )
    return biofiles


@router.post(
    "/search",
    summary="Retrieve biofiles by search model",
    response_model=List[BiofileResponse],
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundResponse}},
    response_model_exclude_none=True,
)
async def get_biofiles_by_search(search: SearchModel = Body(...)):
    biofiles = await DB.retrieve_biofiles_by_search(search)
    if not biofiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(NotFoundResponse()),
        )
    return biofiles


@router.get(
    "/check/database",
    summary="Check if the database is available",
    response_model=GeneralResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": DatabaseErrorResponse}},
)
async def check_database():
    database_available = await DB.check_database()
    if not database_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=jsonable_encoder(DatabaseErrorResponse()),
        )
    return GeneralResponse(
        data={"status": database_available},
        message="Database is available",
        code=status.HTTP_200_OK,
    )


@router.post(
    "/filepath",
    summary="Calculate the experiment_path from the experiment data",
    responses={status.HTTP_200_OK: {"model": GeneralResponse}},
)
async def create_filepath(
    experiment_data: FilecontextOptional = Body(...),
    key_order: Optional[List[str]] = Body(None),
):
    try:
        experiment_data = experiment_data.model_dump(exclude_none=False)
        if key_order is None:
            key_order: List = [
                "species",
                "origin",
                "organType",
                "cellType",
                "experimentName",
                "influenceGroups",
                "sampleID",
                "ageDIV",
                "labDevice",
            ]

        experiment_path = pathlib.Path("./")

        chosen_value = "ageNone"
        if experiment_data.get("ageDAP") is not None:
            chosen_value = "DAP" + str(experiment_data["ageDAP"])
        elif experiment_data.get("ageDIV") is not None:
            chosen_value = "DIV" + str(experiment_data["ageDIV"])

        for key in key_order:
            # Skip keys that have already been processed
            if key in ["ageDIV", "ageDAP"]:
                continue
            elif key == "influenceGroups":
                influence_groups_dict = [
                    experiment_data["influenceGroups"][key]
                    for key in experiment_data["influenceGroups"]
                    if key.startswith("influence")
                ]
                # get all values from the nested dict where the key is 'name'
                influence_groups = [
                    value["name"]
                    for influence_group in influence_groups_dict
                    for value in influence_group.values()
                    if value is not None
                ]
                # make the list unique keeping the order
                unique_influence_groups = list(dict.fromkeys(influence_groups))
                experiment_path /= pathlib.Path("_".join(unique_influence_groups))

            # Ensure the key is in the experiment_data
            if key in experiment_data:
                value = experiment_data.get(key)

                # Check if the value is a dictionary, then concatenate nested keys
                # This is the case for the device name
                if isinstance(value, dict):
                    nested_keys = list(value.keys())

                    # Concatenate the values of "name" keys with an underscore
                    nested_values = "_".join(
                        str(value[nested_key]["name"])
                        for nested_key in nested_keys
                        if value[nested_key] is not None and "name" in value[nested_key]
                    )

                    # Concatenate the nested values to the file path
                    experiment_path /= pathlib.Path(nested_values)
                else:
                    # Ensure value is a string representation
                    value_str = str(value)

                    if key == "sampleID":
                        value_str = "sID" + value_str

                    # Concatenate value to the file path
                    experiment_path /= pathlib.Path(value_str)

                # Insert the chosen value after 'experimentName'
                if key == "sampleID" and chosen_value is not None:
                    experiment_path /= pathlib.Path(chosen_value)
            elif key == "influence":
                continue
            else:
                raise KeyError(f"Key '{key}' not found in experiment_data.")

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating file path: {e}",
        ) from e

    return GeneralResponse(
        data={"experiment_path": experiment_path},
        message="Experiment path retrieved successfully",
        code=status.HTTP_200_OK,
    )
