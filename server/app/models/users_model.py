from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY
from datetime import datetime
from core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(Text)
    enabled_domains = Column(ARRAY(String))
    role = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)