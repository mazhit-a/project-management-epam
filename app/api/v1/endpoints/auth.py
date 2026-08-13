from fastapi import APIRouter, status

from app.api.deps import UserServiceDep
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.common import ErrorResponse
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(tags=["auth"])


@router.post(
    "/auth",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    responses={409: {"model": ErrorResponse}},
)
async def create_user(payload: UserCreate, service: UserServiceDep) -> UserRead:
    return UserRead.model_validate(await service.register(payload))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and obtain a JWT access token",
    responses={401: {"model": ErrorResponse}},
)
async def login(payload: LoginRequest, service: UserServiceDep) -> TokenResponse:
    user = await service.authenticate(payload.login, payload.password)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
