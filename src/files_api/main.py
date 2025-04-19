from datetime import datetime
from typing import (
    List,
    Optional,
)
from venv import create

from fastapi import (
    APIRouter,
    Depends,
    Request,
    FastAPI,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3
)
from files_api.s3.write_objects import upload_s3_object
import os
from pydantic import BaseModel
from regex import R
from files_api.routes import ROUTER
from files_api.schemas import (
    PutFileResponse
)
from files_api.settings import Settings

def create_app(settings: Settings = None) -> FastAPI:
    settings = settings = settings or Settings()
    app = FastAPI()

    app.state.settings = settings
    app.include_router(ROUTER)

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
