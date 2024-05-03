from typing import Any, Dict, List, Optional, Union

from model.biofile import Biofile, Filecontext
from pydantic import BaseModel, Field, field_validator


class GeneralResponse(BaseModel):
    data: Dict[str, Union[Any, List[Biofile]]]
    code: int
    message: str


class BiofileResponse(BaseModel, extra="forbid"):
    id: Optional[str] = Field(default=None, alias="_id")
    filecontext: Filecontext = None
    filepath: str = None
    filesize: int = None
    filehash: str = None
    filetype: str = None

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v):
        return str(v) if v is not None else None


class FileListResponse(BaseModel):
    data: List[str]
    code: int
    message: str


class ServerErrorResponse(BaseModel):
    error: str = "Internal Server Error"
    code: int = 500
    message: str = "An error occurred"


class NotFoundResponse(BaseModel):
    error: str = "Not Found"
    code: int = 404
    message: str = "Biofile doesn't exist."


class CacheExpiredResponse(BaseModel):
    error: str = "Cache Expired"
    code: int = 408
    message: str = "Cache entry has expired"


class DatabaseErrorResponse(BaseModel):
    error: str = "Database Error"
    code: int = 503
    message: str = "An error occurred while interacting with the database"
