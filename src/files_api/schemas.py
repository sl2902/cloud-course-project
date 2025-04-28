"""Pydantic class validation for REST API"""

import re
from datetime import datetime
from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from typing_extensions import Self

DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 100
DEFAULT_GET_FILES_DIRECTORY = ""

INVALID_FILE_PATH = re.compile(
    r"""
                            ^
                            [\/.]+
                            |.*\/\/
                            |.*%
                            |.*\s+
                            """,
    re.VERBOSE,
)


class FilePathValidator(BaseModel):
    """File path validator"""

    file_path: str = Field(
        ...,
        # pattern=r'^(?![\/.])(?!.*//)(?!.*%)\S+$',
        description=("Relative path (no leading slash or dot), " "no empty segments, no percent-encoding, no spaces"),
    )

    @field_validator("file_path")
    @classmethod
    def _validate_file_path(cls, file_path):
        if INVALID_FILE_PATH.search(file_path):
            raise ValueError("file_path must not start with '/' or '.', " "contain '//' or '%', or include whitespace")
        return file_path


# read (cRud)
class FileMetadata(BaseModel):
    """Metadata of a file."""

    file_path: str = Field(
        description="The path of the file.",
        json_schema_extra={"example": "path/to/pyproject.toml"},
    )
    last_modified: datetime = Field(description="The last modified date of the file.")
    size_bytes: int = Field(description="The size of the file in bytes.")

    @field_validator("file_path")
    @classmethod
    def _validate_file_path(cls, file_path):
        if INVALID_FILE_PATH.search(file_path):
            raise ValueError("file_path must not start with '/' or '.', " "contain '//' or '%', or include whitespace")
        return file_path


class PutFileResponse(BaseModel):
    """Response model for `PUT /v1/files/:file_path`."""

    file_path: str = Field(
        description="The path of the file.",
        json_schema_extra={"example": "path/to/pyproject.toml"},
    )
    message: str = Field(description="A message about the operation.")


class GetFilesResponse(BaseModel):
    """Response model for `GET /v1/files`."""

    files: List[FileMetadata]
    next_page_token: Optional[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": [
                    {
                        "file_path": "path/to/pyproject.toml",
                        "last_modified": "2022-01-01T00:00:00Z",
                        "size_bytes": 512,
                    },
                    {
                        "file_path": "path/to/Makefile",
                        "last_modified": "2022-01-01T00:00:00Z",
                        "size_bytes": 256,
                    },
                ],
                "next_page_token": "next_page_token_example",
            }
        }
    )


class GetFilesQueryParams(BaseModel):
    """Query parameters for `GET /v1/files`."""

    page_size: int = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
    )
    directory: Optional[str] = Field(
        DEFAULT_GET_FILES_DIRECTORY,
        description="The directory to list files from.",
    )
    page_token: Optional[str] = Field(
        None,
        description="The token for the next page.",
    )

    @model_validator(mode="after")
    def check_mutual_exclusivity(self) -> Self:
        if self.page_token:
            get_files_query_params = self.model_dump(exclude_unset=True)
            page_size_set = "page_size" in get_files_query_params.keys()
            directory_path_set = "directory" in get_files_query_params.keys()
            if page_size_set or directory_path_set:
                raise ValueError("page_token is mutually exclusive with page_size and directory")
        return self


class DeleteFileResponse(BaseModel):
    """Response model for `DELETE /v1/files/:file_path`."""

    message: str
