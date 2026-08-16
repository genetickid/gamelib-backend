from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.exceptions.common import ObjNotFoundError
from gamelib.models import Base


async def get_obj_or_404[ModelType: Base](
    db_model: type[ModelType],
    pk: int,
    db: AsyncSession,
    error_msg: str = 'Object not found'
) -> ModelType:
    obj = await db.get(db_model, pk)
    if obj is None:
        raise ObjNotFoundError(error_msg)
    return obj
