"""Pydantic class validation for REST API"""

import re
from datetime import datetime
from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
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
    file_path: str
    last_modified: datetime
    size_bytes: int

    @field_validator("file_path")
    @classmethod
    def _validate_file_path(cls, file_path):
        if INVALID_FILE_PATH.search(file_path):
            raise ValueError("file_path must not start with '/' or '.', " "contain '//' or '%', or include whitespace")
        return file_path


class PutFileResponse(BaseModel):
    file_path: str
    message: str


class GetFilesResponse(BaseModel):
    files: List[FileMetadata]
    next_page_token: Optional[str]


class GetFilesQueryParams(BaseModel):
    page_size: int = Field(
        DEFAULT_GET_FILES_PAGE_SIZE, le=DEFAULT_GET_FILES_MAX_PAGE_SIZE, ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE
    )
    directory: Optional[str] = DEFAULT_GET_FILES_DIRECTORY
    page_token: Optional[str] = None

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
    message: str
