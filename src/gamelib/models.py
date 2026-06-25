from datetime import date, datetime

from sqlalchemy import Enum, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from gamelib.schemas import GameStatus, UserRole
from gamelib.utils.common import enum_values


class Base(DeclarativeBase):
    pass


class GameModel(Base):
    __tablename__ = 'games'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str] = mapped_column(String(200))
    hours_played: Mapped[float] = mapped_column(default=0.0)
    rating: Mapped[float | None] = mapped_column()
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, values_callable=enum_values),
        default=GameStatus.BACKLOG
    )
    release_date: Mapped[date | None] = mapped_column()
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserModel(Base):
    __tablename__ = 'users'

    _STAFF_ROLES = frozenset([UserRole.ADMIN])

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column()
    about: Mapped[str | None] = mapped_column()
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=enum_values)
    )

    @property
    def is_staff(self) -> bool:
        return self.role in self._STAFF_ROLES
