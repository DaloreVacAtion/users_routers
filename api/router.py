from fastapi import APIRouter
from starlette import status
from starlette.responses import JSONResponse

from api.v1 import v1_router

root_router = APIRouter(prefix="/api")


root_router.include_router(v1_router)


@root_router.get("/ping")
async def ping() -> JSONResponse:
    return JSONResponse({'status': status.HTTP_200_OK, 'result': 'pong'})
