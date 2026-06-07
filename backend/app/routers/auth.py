
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import RefreshTokenRequest, SignInRequest, SignUpRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE = "refresh_token"
COOKIE_MAX_AGE = int(timedelta(days=30).total_seconds())


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    data: SignUpRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user and create an organization."""
    try:
        svc = AuthService(db)
        token_response, refresh_token = await svc.sign_up(data)
        _set_refresh_cookie(response, refresh_token)
        return token_response
    except AppError as e:
        raise to_http_exception(e)


@router.post("/signin", response_model=TokenResponse)
async def sign_in(
    data: SignInRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Sign in with email and password."""
    try:
        svc = AuthService(db)
        token_response, refresh_token = await svc.sign_in(data)
        _set_refresh_cookie(response, refresh_token)
        return token_response
    except AppError as e:
        raise to_http_exception(e)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
    body: RefreshTokenRequest | None = None,
):
    """Get a new access token using the refresh token."""
    raw_token = refresh_token or (body.refresh_token if body else None)
    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )
    try:
        svc = AuthService(db)
        token_response, new_refresh = await svc.refresh(raw_token)
        _set_refresh_cookie(response, new_refresh)
        return token_response
    except AppError as e:
        raise to_http_exception(e)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    """Revoke the current refresh token."""
    if refresh_token:
        svc = AuthService(db)
        await svc.logout(refresh_token)
    response.delete_cookie(REFRESH_COOKIE)


@router.get("/me", response_model=dict)
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    """Get currently authenticated user info."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
    }


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/api/auth",
    )
