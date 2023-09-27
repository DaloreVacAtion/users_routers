from pydantic import BaseModel, ConfigDict


class BaseUser(BaseModel):
    email: str
    username: str


class UserCreate(BaseUser):
    password: str


class UserRead(BaseUser):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
