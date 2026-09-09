"""FastAPI dependencies for Supabase JWT verification.

Identity comes from GoTrue's user endpoint, not local JWT parsing.
Missing or invalid tokens are 401; upstream Auth outages are 502.
"""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import (
    AsyncClient,
    AuthError,
    AuthRetryableError,
    AuthUnknownError,
)

from app.database.supabase import create_user_client

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    email: str | None


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing, expired, or invalid Supabase token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _auth_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Supabase Auth is unavailable",
    )


async def get_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    token = credentials.credentials.strip()
    if not token:
        raise _unauthorized()
    return token


async def _user_client(
    access_token: Annotated[str, Depends(get_access_token)],
) -> AsyncClient:
    return await create_user_client(access_token)


async def get_current_user(
    access_token: Annotated[str, Depends(get_access_token)],
    client: Annotated[AsyncClient, Depends(_user_client)],
) -> CurrentUser:
    try:
        response = await client.auth.get_user(access_token)
    except (AuthRetryableError, AuthUnknownError, httpx.RequestError) as exc:
        raise _auth_unavailable() from exc
    except AuthError as exc:
        raise _unauthorized() from exc

    user = response.user if response is not None else None
    if user is None or not user.id:
        raise _unauthorized()

    return CurrentUser(id=UUID(user.id), email=user.email)


async def get_user_client(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[AsyncClient, Depends(_user_client)],
) -> AsyncClient:
    return client


def require_thread_owner(user: CurrentUser, owner_id: UUID) -> None:
    if user.id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's thread",
        )
