from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic_core import ValidationError

from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object
from files_api.schemas import (
    FileMetadata,
    FilePathValidator,
    GetFilesQueryParams,
    GetFilesResponse,
    PutFileResponse,
)
from files_api.settings import Settings

# from pkg_resources import FileMetadata


ROUTER = APIRouter()


@ROUTER.put("/v1/files/{file_path:path}")
async def upload_file(request: Request, file: UploadFile, file_path: str, response: Response) -> PutFileResponse:
    """Upload a file."""
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    object_already_exists = object_exists_in_s3(settings.s3_bucket_name, file_path)
    if object_already_exists:
        message = f"Existing file updated at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    file_content = await file.read()
    upload_s3_object(settings.s3_bucket_name, file_path, file_content=file_content, content_type=file.content_type)

    return PutFileResponse(file_path=file_path, message=message)


@ROUTER.get("/v1/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),
) -> GetFilesResponse:
    """List files with pagination."""
    settings: Settings = request.app.state.settings
    if query_params.page_token:
        objects, next_token = fetch_s3_objects_using_page_token(
            bucket_name=settings.s3_bucket_name,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )
    else:
        objects, next_token = fetch_s3_objects_metadata(
            bucket_name=settings.s3_bucket_name, prefix=query_params.directory, max_keys=query_params.page_size
        )

    file_metadata = [
        FileMetadata(file_path=file.get("Key"), last_modified=file.get("LastModified"), size_bytes=file.get("Size"))
        for file in objects
    ]
    return GetFilesResponse(files=file_metadata, next_page_token=next_token)


@ROUTER.head("/v1/files/{file_path:path}")
async def get_file_metadata(request: Request, file_path: str, response: Response) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(bucket_name=settings.s3_bucket_name, object_key=file_path)
    if not object_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    get_object_response = fetch_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.status_code = status.HTTP_200_OK
    return response


@ROUTER.get("/v1/files/{file_path:path}")
async def get_file(
    request: Request,
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(bucket_name=settings.s3_bucket_name, object_key=file_path)
    if not object_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    get_object_response = fetch_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    headers = {
        "Content-Length": str(get_object_response["ContentLength"]),
        "Content-Type": get_object_response["ContentType"],
    }
    return StreamingResponse(
        content=get_object_response["Body"], media_type=get_object_response["ContentType"], headers=headers
    )


@ROUTER.delete("/v1/files/{file_path:path}")
async def delete_file(request: Request, file_path: str, response: Response) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(bucket_name=settings.s3_bucket_name, object_key=file_path)
    if not object_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    delete_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
