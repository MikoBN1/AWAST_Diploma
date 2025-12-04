from fastapi import APIRouter, HTTPException, status, Body
from jose import JWTError

from core.database import async_session
from models.users_model import User
from schemas.user_schema import UserLogin
from services.database_service import AsyncDatabaseService
from utils.auth_util import verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])

database_service = AsyncDatabaseService(async_session)

@router.post("/login")
async def login(user_data: UserLogin):
    user = await database_service.get(User, email=user_data.email)

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_token_route(refresh_token: str = Body(...)):
    try:
        payload = decode_token(refresh_token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Expired or invalid refresh token")

    new_access_token = create_access_token({"sub": email})
    return {"access_token": new_access_token}