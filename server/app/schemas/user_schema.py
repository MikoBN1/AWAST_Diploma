from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

PricingPlan = Literal["Pro", "Advanced", "Trial", "Lite"]

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    enabled_domains: Optional[List[str]] = None
    role: Optional[str] = 'USER'

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    enabled_domains: List[str]

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None
    enabled_domains: Optional[List[str]] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr
    enabled_domains: List[str]
    role: str

class User(UserBase):
    user_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True