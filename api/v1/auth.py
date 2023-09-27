from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from auth.schemas import Token, UserCreate
from auth.services import AuthService

auth_router = APIRouter(prefix='/auth')


@auth_router.post(
    '/register',
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(),
):
    return auth_service.register_new_user(user_data)


@auth_router.post(
    '/login',
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
def login_user(
    auth_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(),
):
    return auth_service.authenticate_user(
        auth_data.username,
        auth_data.password,
    )
