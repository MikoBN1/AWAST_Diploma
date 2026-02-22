from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user, require_admin
from models.users_model import User
from schemas.user_schema import UserOut, UserCreate, UserUpdate
import services.user_service as users_service

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/all", response_model=List[UserOut])
async def get_users(user: User = Depends(require_admin)):
    users = await users_service.get_users()
    return users

@router.get("/me", response_model=UserOut)
async def read_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, current_user: User = Depends(require_admin)):
    user = await users_service.get_user(user_id)
    return user

@router.post("/new", response_model=UserOut)
async def create_user(user_data: UserCreate, current_user: User = Depends(require_admin)):
    return await users_service.create_user(user_data)

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id:str, user_data: UserUpdate, current_user: User = Depends(require_admin)):
    return await users_service.update_user(user_id,user_data)

@router.delete("/{user_id}", response_model=dict[str, str])
async def delete_user(user_id: str, current_user: User = Depends(require_admin)):
    return await users_service.delete_user(user_id)

@router.get("/my/scan/history")
async def get_my_scan_history(current_user = Depends(get_current_user)):
    return await users_service.get_my_scan_history(current_user.user_id)

@router.get("/my/scan/{scan_id}/results")
async def get_my_scan_history(scan_id: str, current_user = Depends(get_current_user)):
    return await users_service.get_my_scan_results(current_user.user_id, scan_id)