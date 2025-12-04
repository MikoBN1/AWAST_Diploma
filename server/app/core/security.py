import ipaddress

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db, async_session
from models.scan_model import Scan
from models.users_model import User
import os
from dotenv import load_dotenv

from services.database_service import AsyncDatabaseService

load_dotenv()

database_service = AsyncDatabaseService(async_session)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = 'HS256'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await database_service.get(User, email=email)

    if user is None:
        raise credentials_exception

    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

async def check_domain_permission(
    domain: str,
    current_user: User = Depends(get_current_user)
) -> User:
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")
    if current_user.role == "ADMIN":
        return current_user
    if not current_user.enabled_domains:
        raise HTTPException(status_code=403, detail="No domains enabled for this user")
    allowed_domains = [d.lower() for d in current_user.enabled_domains]
    if domain.lower() not in allowed_domains:
        raise HTTPException(status_code=403, detail=f"Access to domain '{domain}' is denied")
    return current_user

async def check_domain_permission_from_body(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    body = await request.json()
    target_url = body.get("target")
    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'target_url' in body")

    from urllib.parse import urlparse
    domain = urlparse(target_url).hostname or target_url
    return await check_domain_permission(domain, current_user)

async def check_scan_permission_from_query(
    scan_id: str,
    current_user: User = Depends(get_current_user)
) -> User:
    result = await database_service.get(User, scan_id=scan_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Scan not found for this user")
    return current_user

async def check_scan_permission_from_body(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    body = await request.json()
    scan_id = body.get("scan_id")

    if not scan_id:
        raise HTTPException(status_code=400, detail="Missing 'scan_id' in request body")

    scan_exists = await database_service.get(User, scan_id=scan_id, user_id=current_user.id)

    if not scan_exists:
        raise HTTPException(status_code=404, detail=f"Scan ID '{scan_id}' not found for this user")

    return current_user

async def check_report_permission_from_query(
    report_id: str,
    current_user: User = Depends(get_current_user)
) -> User:
    scan_exists = await database_service.get(User, report_id=report_id, user_id=current_user.id)

    if not scan_exists:
        raise HTTPException(status_code=404, detail=f"Scan not found for this user")

    return current_user