from dotenv import load_dotenv
from fastapi import FastAPI
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

load_dotenv()
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await init_models()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scanner_controller.router)
app.include_router(exploiter_controller.router)
app.include_router(report_controller.router)
app.include_router(user_controller.router, prefix="/api")
app.include_router(auth_controller.router, prefix="/api")
app.include_router(swagger_controller.router, prefix="/api")