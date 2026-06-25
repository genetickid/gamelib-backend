from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from gamelib.models import Base


def get_obj_or_404[ModelType: Base](
    db_model: type[ModelType],
    pk: int,
    db: Session,
    error_msg: str = 'Object not found'
) -> ModelType:
    obj = db.get(db_model, pk)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )
    return obj
