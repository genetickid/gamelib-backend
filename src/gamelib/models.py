from datetime import date, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from gamelib.schemas import GameStatus, UserRole
from gamelib.utils.common import enum_values


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = 'games'

    id: Mapped[int] = mapped_column(primary_key=True)
    steam_appid: Mapped[int | None] = mapped_column(unique=True)
    steam_icon_hash: Mapped[str | None] = mapped_column()
    title: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str | None] = mapped_column(String(200))
    release_date: Mapped[date | None] = mapped_column()
    library_entries: Mapped[list['UserGame']] = relationship(
        back_populates='game'
    )

    @property
    def steam_icon_url(self) -> str | None:
        if not self.steam_icon_hash:
            return None

        return (
            'https://media.steampowered.com/steamcommunity/public/images/apps/'
            f'{self.steam_appid}/{self.steam_icon_hash}.jpg'
        )


class User(Base):
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
    library_entries: Mapped[list['UserGame']] = relationship(
        back_populates='user'
    )

    @property
    def is_staff(self) -> bool:
        return self.role in self._STAFF_ROLES


class UserGame(Base):
    __tablename__ = 'usergame'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey('games.id'), primary_key=True)

    user: Mapped['User'] = relationship(back_populates='library_entries')
    game: Mapped['Game'] = relationship(back_populates='library_entries')

    playtime_minutes: Mapped[int] = mapped_column(default=0)
    last_played_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    rating: Mapped[float | None] = mapped_column()
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, values_callable=enum_values),
        default=GameStatus.BACKLOG
    )
