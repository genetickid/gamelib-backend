from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from gamelib.lifespan import lifespan
from gamelib.routers.games import router as games_router
from gamelib.routers.auth import router as auth_router
from gamelib.routers.users import router as users_router
from gamelib.exceptions import UserAlreadyExistsError

app = FastAPI(lifespan=lifespan)

app.include_router(games_router)
app.include_router(auth_router)
app.include_router(users_router)

@app.exception_handler(UserAlreadyExistsError)
async def user_exists_error_handler(
    request: Request,
    exc: UserAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': 'This username is already taken.'}
    )
