from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login_api(payload: LoginRequest) -> LoginResponse:
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    return LoginResponse(
        access_token=create_access_token(settings.admin_username),
        expires_in=settings.auth_token_expire_minutes * 60,
        username=settings.admin_username,
    )


@router.get("/me", response_model=MeResponse)
async def me_api() -> MeResponse:
    return MeResponse(username=settings.admin_username)
