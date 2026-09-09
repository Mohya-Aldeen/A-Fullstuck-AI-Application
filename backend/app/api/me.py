from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import CurrentUser, get_current_user

router = APIRouter()


class MeResponse(BaseModel):
    id: UUID
    email: str | None


@router.get("/me")
async def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> MeResponse:
    """Authenticated identity check — used to verify the browser JWT reaches FastAPI."""
    return MeResponse(id=user.id, email=user.email)
