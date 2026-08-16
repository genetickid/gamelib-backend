from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.database import get_db
from gamelib.models import Game
from gamelib.schemas import GameRead, GameUpdate, GameWrite
from gamelib.utils.web import get_obj_or_404

router = APIRouter(prefix='/games', tags=['games'])

@router.get('')
async def games_list(db: AsyncSession = Depends(get_db)) -> list[GameRead]:
    stmt = select(Game)
    result = await db.scalars(stmt)
    games = result.all()
    return games


@router.get('/{game_id}')
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)) -> GameRead:
    return await get_obj_or_404(Game, game_id, db, 'Game not found')

@router.post('/')
async def add_game(game_data: GameWrite, db: AsyncSession = Depends(get_db)) -> GameRead:
    game_obj = Game(**game_data.model_dump())
    db.add(game_obj)
    await db.commit()
    await db.refresh(game_obj)
    return game_obj


@router.delete('/{game_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)) -> None:
    game = await get_obj_or_404(Game, game_id, db, 'Game not found')
    await db.delete(game)
    await db.commit()


@router.patch('/{game_id}')
async def update_game(
    game_id: int,
    update_fields: GameUpdate,
    db: AsyncSession = Depends(get_db)
) -> GameRead:
    game = await get_obj_or_404(Game, game_id, db, 'Game not found')
    update_data = update_fields.model_dump(exclude_unset=True)
    if not update_data:
        return game

    for field_name, new_value in update_data.items():
        setattr(game, field_name, new_value)
    await db.commit()

    return game
