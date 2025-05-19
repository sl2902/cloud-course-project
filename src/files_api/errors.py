"""Defines global errors"""
import traceback

import pydantic
from fastapi import (
    Request,
    status,
)
from fastapi.responses import JSONResponse
from loguru import logger

from files_api.monitoring.logger import log_response_info


async def handle_broad_exceptions(request: Request, call_next):
    """Handle any exception that goes unhandled by a more specific exception handler."""
    try:
        return await call_next(request)
    except Exception as err:  # pylint: disable=broad-except
        logger.exception(err)
        traceback.print_exc()
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
        log_response_info(response)
        return response


async def handle_pydantic_validation_errors(_: Request, exc: pydantic.ValidationError) -> JSONResponse:
    errors = exc.errors()
    logger.exception(exc)
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": [{"msg": error["msg"], "input": error["input"]} for error in errors]},
    )
    log_response_info(response)
    return response
