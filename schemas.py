from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Literal


# class UserStatus(str, Enum):
#     admin = 'admin'
#     user = 'user'
#     superuser = 'superuser'
#     blocked = 'blocked'


class MyBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AddOption(MyBaseModel):
    text: str = Field(min_length=1, max_length=150)


class Option(AddOption):
    option_id: int = Field(gt=0)


class OptionsList(MyBaseModel):
    options: list[int]


class JWTToken(MyBaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    user_id: int | None = None


class Rank(MyBaseModel):
    id: int = Field(gt=0)
    text: str
    rating: float


class RankingRequest(MyBaseModel):
    ids: list[int]


class RankingOptions(MyBaseModel):
    id: int | None
    text: str


class _BaseUser(MyBaseModel):
    username: str
    email: EmailStr | None = None


class CreateUser(_BaseUser):
    password: str | bytes


class BaseUserData(MyBaseModel):
    user_id: int
    status: Literal['admin', 'user', 'superuser', 'blocked']


class UserData(_BaseUser, BaseUserData):
    pass


class User(CreateUser, BaseUserData):
    pass


class UserCreds(MyBaseModel):
    username: str
    password: bytes


class HandleAnswer(MyBaseModel):
    result: str
    message: str

