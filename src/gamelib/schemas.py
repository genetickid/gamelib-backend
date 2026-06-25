import enum
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GameStatus(str, enum.Enum):
    BACKLOG = 'backlog'
    PLAYING = 'playing'
    COMPLETED = 'completed'
    DROPPED = 'dropped'


GameRating = Annotated[float, Field(ge=0, le=10.0)]
GameHours = Annotated[float, Field(ge=0)]
GameTitle = Annotated[str, Field(max_length=200)]
GameGenre = Annotated[str, Field(max_length=200)]


class BaseGame(BaseModel):
    title: GameTitle
    genre: GameGenre
    hours_played: GameHours = 0.0
    rating: GameRating | None = None
    release_date: date | None = None
    status: GameStatus = GameStatus.BACKLOG


class GameRead(BaseGame):
    model_config = ConfigDict(from_attributes=True)

    id: int
    added_at: datetime


class GameWrite(BaseGame):
    pass


class GameUpdate(BaseModel):
    title: GameTitle | None = None
    genre: GameGenre | None = None
    hours_played: GameHours | None = None
    rating: GameRating | None = None
    release_date: date | None = None
    status: GameStatus | None = None


Username = Annotated[str, Field(min_length=2, max_length=32)]
Password = Annotated[str, Field(min_length=8, max_length=64)]


class UserRole(str, enum.Enum):
    USER = 'user'
    ADMIN = 'admin'
    EDITOR = 'editor'


class BaseUser(BaseModel):
    username: Username
    name: str | None = None
    about: str | None = None


class UserAuth(BaseUser):
    password: Password


class UserCreate(UserAuth):
    role: UserRole


class UserRead(BaseUser):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str
