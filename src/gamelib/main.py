from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from gamelib.exceptions.common import ObjAlreadyExistsError, ObjNotFoundError
from gamelib.lifespan import lifespan
from gamelib.routers.auth import router as auth_router
from gamelib.routers.games import router as games_router
from gamelib.routers.users import router as users_router

app = FastAPI(lifespan=lifespan)

app.include_router(games_router)
app.include_router(auth_router)
app.include_router(users_router)

@app.exception_handler(ObjAlreadyExistsError)
async def already_exists_error_handler(
    request: Request,
    exc: ObjAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': str(exc)}
    )


@app.exception_handler(ObjNotFoundError)
async def obj_not_found_error_handler(
    request: Request,
    exc: ObjNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'detail': str(exc)}
    )
