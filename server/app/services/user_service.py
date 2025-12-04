from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import get_db, async_session
from models.scan_model import Scan
from models.users_model import User
from models.vulnerability_model import Vulnerability
from schemas.user_schema import UserCreate, UserUpdate, UserOut
from services.database_service import AsyncDatabaseService
from utils.auth_util import hash_password
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

database_service = AsyncDatabaseService(async_session)

async def get_users():
    result = await database_service.get_all(User)
    return result

async def get_user(user_id: str):
    user = await database_service.get(User, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def create_user(user_data: UserCreate) -> UserOut:
    existing_user = await database_service.get(User, email=user_data.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    print(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        enabled_domains=user_data.enabled_domains
    )

    created_user = await database_service.create(new_user)
    return created_user

async def delete_user(user_id:str):
    existing_user = await database_service.get(User, user_id=user_id)

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    await database_service.delete(User, user_id=user_id)

    return {"message": "User deleted!"}

async def update_user(user_id: str, user_data: UserUpdate) -> UserOut:
    existing_user = await database_service.get(User, user_id=user_id)

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}

    if "password" in update_data:
        hashed_password = pwd_context.hash(update_data.pop("password"))
        existing_user.password_hash = hashed_password

    result = await database_service.update(User, {"user_id" : user_id}, update_data)

    return result

async def get_my_scan_history(user_id):
    instance = await database_service.get_all(Scan, user_id=user_id)
    if not instance:
        return []
    return instance

async def get_my_scan_results(user_id:str, scan_id: str):
    scan = await database_service.get(Scan, user_id=user_id, scan_id=scan_id)
    if not scan:
        return []

    scan_results = await database_service.get_all(Vulnerability, scan_id=scan_id)

    if not scan_results:
        return []

    return scan_results