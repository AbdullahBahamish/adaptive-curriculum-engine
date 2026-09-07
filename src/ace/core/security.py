"""Service-to-service authentication middleware.

The C# backend must pass `X-Service-API-Key: <value>` on every request.
This module provides:
  - `verify_api_key`  : FastAPI dependency for route-level enforcement.
  - `APIKeyMiddleware`: Starlette middleware for global enforcement.
"""
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from ace.core.config import settings

_API_KEY_HEADER = APIKeyHeader(name="X-Service-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> str:
    """FastAPI dependency: validates the service API key.

    Raises 401 if missing, 403 if invalid.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Service-API-Key header is required.",
        )
    if api_key != settings.service_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service API key.",
        )
    return api_key