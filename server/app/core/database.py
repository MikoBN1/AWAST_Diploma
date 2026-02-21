import asyncio
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from models.users_model import User

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)