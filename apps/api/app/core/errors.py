"""Global RFC 7807 problem-detail error handling for the FastAPI surface."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _problem(
    status_code: int,
    title: str,
    detail: str,
    instance: str | None = None,
    errors: list[dict] | None = None,
) -> JSONResponse:
    body: dict = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    if errors:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code, content=body, media_type="application/problem+json"
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_problem_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation Failed",
            "The submitted payload failed schema validation.",
            instance=str(request.url.path),
            errors=[
                {
                    "loc": list(err.get("loc", [])),
                    "msg": err.get("msg", ""),
                    "type": err.get("type", ""),
                }
                for err in exc.errors()
            ],
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_problem_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(
            exc.status_code,
            "Request Failed",
            str(exc.detail),
            instance=str(request.url.path),
        )

    @app.exception_handler(Exception)
    async def unhandled_problem_handler(request: Request, exc: Exception) -> JSONResponse:
        return _problem(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "An unexpected error occurred while processing the request.",
            instance=str(request.url.path),
        )
