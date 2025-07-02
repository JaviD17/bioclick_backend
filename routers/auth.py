from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from slowapi import Limiter
from slowapi.util import get_remote_address

try:

    from ..models.auth import (
        Token,
        UserLogin,
        UserRegister,
        PasswordResetRequest,
        PasswordResetConfirm,
    )
    from ..models.user import UserPublic
    from ..dependencies import AuthServiceDep
except ImportError:
    from models.auth import (
        Token,
        UserLogin,
        UserRegister,
        PasswordResetRequest,
        PasswordResetConfirm,
    )
    from models.user import UserPublic
    from dependencies import AuthServiceDep


router = APIRouter(prefix="/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")  # Limit registration to 5 requests per minute
async def register(
    request: Request, user_register: UserRegister, auth_service: AuthServiceDep
):
    """Register a new user"""
    new_user = auth_service.create_user(user_register)
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Limit login to 10 requests per minute
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
):
    """Login with username and password (OAuth2 compatible)"""
    user_login = UserLogin(username=form_data.username, password=form_data.password)
    return auth_service.login_user(user_login)


@router.post("/login-json", response_model=Token)
@limiter.limit("10/minute")  # Limit login to 10 requests per minute
async def login_json(
    request: Request, user_login: UserLogin, auth_service: AuthServiceDep
):
    """Login with JSON body (alternative to form data)"""
    return auth_service.login_user(user_login)


@router.post("/password-reset/request")
@limiter.limit("3/minute")  # Limit password reset request to 3 requests per minute
async def request_password_reset(
    request: Request, reset_request: PasswordResetRequest, auth_service: AuthServiceDep
):
    """Request password reset email"""
    return auth_service.request_password_reset(reset_request)


@router.post("/password-reset/confirm")
@limiter.limit("5/minute")  # Limit password reset confirm to 5 requests per minute
async def confirm_password_reset(
    request: Request, reset_confirm: PasswordResetConfirm, auth_service: AuthServiceDep
):
    """Reset password with token"""
    return auth_service.reset_password(reset_confirm)
