from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from core.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    target = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default='pending')
    report_id = Column(UUID(as_uuid=True), nullable=True, unique=True,)
    report_status = Column(String, nullable=False, default='none')
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    zap_index = Column(Integer, nullable=False)