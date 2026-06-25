from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gamelib.database import get_db
from gamelib.models import GameModel
from gamelib.schemas import GameRead, GameUpdate, GameWrite
from gamelib.utils.web import get_obj_or_404

router = APIRouter(prefix='/games', tags=['games'])

@router.get('')
def games_list(db: Session = Depends(get_db)) -> list[GameRead]:
    stmt = select(GameModel)
    games = db.scalars(stmt).all()
    return games


@router.get('/{game_id}')
def get_game(game_id: int, db: Session = Depends(get_db)) -> GameRead:
    return get_obj_or_404(GameModel, game_id, db, 'Game not found')

@router.post('/')
def add_game(game_data: GameWrite, db: Session = Depends(get_db)) -> GameRead:
    game_obj = GameModel(**game_data.model_dump())
    db.add(game_obj)
    db.commit()
    db.refresh(game_obj)
    return game_obj


@router.delete('/{game_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_game(game_id: int, db: Session = Depends(get_db)) -> None:
    game = get_obj_or_404(GameModel, game_id, db, 'Game not found')
    db.delete(game)
    db.commit()


@router.patch('/{game_id}')
def update_game(
    game_id: int,
    update_fields: GameUpdate,
    db: Session = Depends(get_db)
) -> GameRead:
    game = get_obj_or_404(GameModel, game_id, db, 'Game not found')
    update_data = update_fields.model_dump(exclude_unset=True)
    if not update_data:
        return game

    for field_name, new_value in update_data.items():
        setattr(game, field_name, new_value)
    db.commit()

    return game
