from typing import Annotated
import mimetypes
import httpx
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
from files_api import settings
from files_api.generate_files import  (
    get_text_chat_completion,
    generate_image,
)
from loguru import logger
from pydantic_core import ValidationError

from files_api.route_handler import RouteHandler
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
    GeneratedFileType,
    GeneratedFilesQueryParams,
    GeneratedImagesQueryParams,
    GetFilesQueryParams,
    GetFilesResponse,
    PutFileResponse,
    PutGeneratedFileResponse,
)
from files_api.settings import Settings

# from pkg_resources import FileMetadata


FILES_ROUTER = APIRouter(tags=["Files"])
GENERATED_FILES_ROUTER = APIRouter(tags=["GeneratedFiles"])

FILES_ROUTER.route_class = RouteHandler


@FILES_ROUTER.put(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_200_OK: {"model": PutFileResponse},
        status.HTTP_201_CREATED: {"model": PutFileResponse},
    },
)
async def upload_file(
    request: Request, file_content: UploadFile, file_path: str, response: Response
) -> PutFileResponse:
    """Upload a file."""
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    object_already_exists = object_exists_in_s3(settings.s3_bucket_name, file_path)
    logger.debug("object_already_exists: {exists}", exists=object_already_exists)
    if object_already_exists:
        message = f"Existing file updated at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    file_bytes = await file_content.read()
    logger.debug("trying to upload file to s3: {file_path}", file_path=file_path)
    upload_s3_object(
        settings.s3_bucket_name, file_path, file_content=file_bytes, content_type=file_content.content_type
    )

    logger.info(message)

    return PutFileResponse(file_path=file_path, message=message)


@FILES_ROUTER.get("/v1/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),
) -> GetFilesResponse:
    """List files with pagination."""
    settings: Settings = request.app.state.settings
    logger.debug("fetching files from s3: {dir}", dir=query_params.directory)
    logger.info(query_params.model_dump())
    # raise Exception('test')

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


@FILES_ROUTER.head(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "headers": {
                "Content-Type": {
                    "description": "The [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types) of the file.",
                    "example": "text/plain",
                    "schema": {"type": "string"},
                },
                "Content-Length": {
                    "description": "The size of the file in bytes.",
                    "example": 512,
                    "schema": {"type": "integer"},
                },
                "Last-Modified": {
                    "description": "The last modified date of the file.",
                    "example": "Thu, 01 Jan 2022 00:00:00 GMT",
                    "schema": {"type": "string", "format": "date-time"},
                },
            }
        },
    },
)
async def get_file_metadata(request: Request, file_path: str, response: Response) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    logger.debug("Checking if object exists in bucket='{bucket}' with key='{key}'", 
                 bucket=settings.s3_bucket_name, key=file_path)
    
    object_exists = object_exists_in_s3(bucket_name=settings.s3_bucket_name, object_key=file_path)
    if not object_exists:
        logger.info("File not found: key='{key}' in bucket='{bucket}'", 
                    key=file_path, bucket=settings.s3_bucket_name)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    get_object_response = fetch_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.status_code = status.HTTP_200_OK

    logger.info("File metadata retrieval succeeded for key='{key}'", key=file_path)

    return response


@FILES_ROUTER.get(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "description": "The file content.",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
    },
)
async def get_file(
    request: Request,
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    logger.info("GET request received for file_path='{file_path}'", file_path=file_path)

    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        logger.warning("Validation failed for key='{key}': {error}", 
                       key=file_path, 
                       error=err
                    )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    logger.debug("Checking if object exists in bucket='{bucket}' with key='{key}'", 
                 bucket=settings.s3_bucket_name, key=file_path)
    
    object_exists = object_exists_in_s3(bucket_name=settings.s3_bucket_name, object_key=file_path)
    if not object_exists:
        logger.info("File not found: key='{key}' in bucket='{bucket}'", 
                    key=file_path, bucket=settings.s3_bucket_name)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    
    logger.debug("Fetching object key='{key}' from bucket='{bucket}'", 
                 key=file_path, bucket=settings.s3_bucket_name)
    get_object_response = fetch_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    headers = {
        "Content-Length": str(get_object_response["ContentLength"]),
        "Content-Type": get_object_response["ContentType"],
    }
    logger.info("File retrieval succeeded for key='{key}'", key=file_path)
    return StreamingResponse(
        content=get_object_response["Body"], media_type=get_object_response["ContentType"], headers=headers
    )


@FILES_ROUTER.delete(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_204_NO_CONTENT: {
            "description": "File deleted successfully.",
        },
    },
)
async def delete_file(request: Request, file_path: str, response: Response) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    logger.info("DELETE /v1/files/{key} - Request received.", key=file_path)
    try:
        FilePathValidator(file_path=file_path)
    except ValidationError as err:
        logger.warning("Validation failed for key='{file_path}': {err}", 
                       file_path=file_path,
                       err=err
                    )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
    settings: Settings = request.app.state.settings
    logger.debug("Checking object existence in bucket='{bucket}' with key='{key}'", 
                 bucket=settings.s3_bucket_name, key=file_path)
    
    object_exists = object_exists_in_s3(bucket_name=settings.s3_bucket_name, object_key=file_path)
    if not object_exists:
        logger.info("File not found: key='{key}' in bucket='{bucket}'", 
                    key=file_path, bucket=settings.s3_bucket_name)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    
    logger.debug("Deleting object key='{key}' from bucket='{bucket}'", 
                 key=file_path, bucket=settings.s3_bucket_name)
    delete_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    response.status_code = status.HTTP_204_NO_CONTENT
    logger.info("File deleted successfully: key='{key}'", key=file_path)
    return response

@GENERATED_FILES_ROUTER.post(
    "/v1/files/generated/chat/completion/{file_path:path}",
    status_code=status.HTTP_201_CREATED,
    summary="AI Chat Completion",
    responses={
        status.HTTP_201_CREATED: {
            "model": PutGeneratedFileResponse,
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "examples": {
                        "text": PutGeneratedFileResponse.model_json_schema()["examples"][0],
                    },
                },
            },
        },
    },
)
async def generate_chat_completion(
    request: Request,
    response: Response,
    query_params: Annotated[GeneratedFilesQueryParams, Depends()], 
) -> PutGeneratedFileResponse:
    """
    Generate a File using AI.

    Supported file types:
    - **text**: `.txt`

    Note: the generated file type is derived from the file_path extension. So the file_path must have
    an extension matching one of the supported file types in the list above.
    """
    settings: Settings = request.app.state.settings
    s3_bucket_name = settings.s3_bucket_name

    file_content = await get_text_chat_completion(prompt=query_params.prompt)
    file_content_bytes: bytes = file_content.encode('utf-8')
    content_type = "text/plain"

    content_type: str |None = content_type or mimetypes.guess_type(query_params.file_path)[0] # type: ignore

    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=query_params.file_path,
        file_content=file_content_bytes,
        content_type=content_type,
    )

    response.status_code = status.HTTP_201_CREATED
    return PutGeneratedFileResponse(
        file_path=query_params.file_path,
        # message=f"New {query_params.file_type.value} file generated and uploaded at path: {query_params.file_path}",
        message=f"New {GeneratedFileType.TEXT.value} file generated and uploaded at path: {query_params.file_path}",
    )


@GENERATED_FILES_ROUTER.post(
    "/v1/files/generated/image/generation/{file_path:path}",
    status_code=status.HTTP_201_CREATED,
    summary="AI Image Generation",
    responses={
        status.HTTP_201_CREATED: {
            "model": PutGeneratedFileResponse,
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "examples": {
                        "text": PutGeneratedFileResponse.model_json_schema()["examples"][1],
                    },
                },
            },
        },
    },
)
async def generate_image_completion(
    request: Request,
    response: Response,
    query_params: Annotated[GeneratedImagesQueryParams, Depends()], 
) -> PutGeneratedFileResponse:
    """
    Generate an Image using AI.

    Supported file types:
    - **text**: `png|jpg|jpeg`

    Note: the generated file type is derived from the file_path extension. So the file_path must have
    an extension matching one of the supported file types in the list above.
    """
    settings: Settings = request.app.state.settings
    s3_bucket_name = settings.s3_bucket_name
    content_type = None

    image_url = await generate_image(prompt=query_params.prompt)
    async with httpx.AsyncClient() as client:
        image_response = await client.get(image_url)  # pylint: disable=missing-timeout
    file_content_bytes = image_response.content

    content_type: str |None = content_type or mimetypes.guess_type(query_params.file_path)[0] # type: ignore

    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=query_params.file_path,
        file_content=file_content_bytes,
        content_type=content_type,
    )

    response.status_code = status.HTTP_201_CREATED
    return PutGeneratedFileResponse(
        file_path=query_params.file_path,
        # message=f"New {query_params.file_type.value} file generated and uploaded at path: {query_params.file_path}",
        message=f"New {GeneratedFileType.IMAGE.value} file generated and uploaded at path: {query_params.file_path}",
    )

