import asyncio
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth.models import User
from auth.schemas import UserRead, Token, UserCreate
from core.config import settings
from db.database import get_async_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login/')


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    return AuthService.verify_token(token)


async def get_user_by_username(username: str, session: AsyncSession) -> UserRead | None:
    users = await session.execute(select(User).where(User.username == username))
    user: UserRead = users.scalars().first()
    return user


class AuthService:
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def verify_token(cls, token: str) -> UserRead:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Не смогли валидировать входящие данные.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError:
            raise exception

        user_data = payload.get('user')

        try:
            user = UserRead.model_validate(user_data)
        except ValidationError:
            raise exception

        return user

    @classmethod
    def create_token(cls, user: User) -> Token:
        user_data = UserRead.model_validate(user)
        now = datetime.utcnow()
        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=settings.JWT_EXPIRES_AT),
            'sub': str(user_data.id),
            'user': user_data.model_dump(exclude_unset=True),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        return Token(access_token=token)

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    def register_new_user(
            self,
            user_data: UserCreate,
    ) -> Token:
        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=self.hash_password(user_data.password),
        )
        self.session.add(user)
        self.session.commit()
        return self.create_token(user)

    def authenticate_user(
            self,
            username: str,
            password: str,
    ) -> Token:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Пожалуйста, проверьте имя пользователя или пароль',
            headers={'WWW-Authenticate': 'Bearer'},
        )

        user = asyncio.create_task(get_user_by_username(username, self.session))

        if not user:
            raise exception

        if not self.verify_password(password, user.password_hash):
            raise exception

        return self.create_token(user)
