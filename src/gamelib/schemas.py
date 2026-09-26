import enum
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GameStatus(str, enum.Enum):
    BACKLOG = 'backlog'
    PLAYING = 'playing'
    COMPLETED = 'completed'
    DROPPED = 'dropped'


GameRating = Annotated[float, Field(ge=0, le=10.0)]
GameMinutes = Annotated[int, Field(ge=0)]
GameTitle = Annotated[str, Field(min_length=1, max_length=200)]
GameGenre = Annotated[str, Field(min_length=2, max_length=200)]


class BaseGame(BaseModel):
    title: GameTitle
    genre: GameGenre | None
    release_date: date | None


class GameRead(BaseGame):
    model_config = ConfigDict(from_attributes=True)

    id: int
    steam_appid: int | None


class GameWrite(BaseGame):
    genre: GameGenre
    release_date: date | None = None


class GameUpdate(BaseModel):
    title: GameTitle | None = None
    genre: GameGenre | None = None
    release_date: date | None = None

    @field_validator('title', 'genre')
    @classmethod
    def validate_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError('Field is not nullable.')
        return value


class UserGameWrite(BaseModel):
    game_id: int
    playtime_minutes: GameMinutes = 0
    rating: GameRating | None = None
    status: GameStatus = GameStatus.BACKLOG


class UserGameUpdate(BaseModel):
    playtime_minutes: GameMinutes | None = None
    rating: GameRating | None = None
    status: GameStatus | None = None


class UserLibraryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    playtime_minutes: GameMinutes
    rating: GameRating | None
    status: GameStatus
    game: GameRead
    added_at: datetime


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


class UserUpdate(BaseModel):
    name: str | None = None
    about: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str
