from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from controllers import (
    user_controller,
    auth_controller,
    swagger_controller,
    scanner_controller,
    exploiter_controller,
    report_controller,
)
from core.database import init_models
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(scanner_controller.router)
api_router.include_router(exploiter_controller.router)
api_router.include_router(report_controller.router)
api_router.include_router(user_controller.router)
api_router.include_router(auth_controller.router)
api_router.include_router(swagger_controller.router)

app.include_router(api_router)