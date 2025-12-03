from typing import Type, TypeVar, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import declarative_base

Base = declarative_base()
T = TypeVar("T", bound=Base)

class AsyncDatabaseService:
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def create(self, obj: T) -> T:
        async with self.session_maker() as session:
            async with session.begin():
                session.add(obj)
                await session.flush()
                await session.refresh(obj)
                return obj

    async def get(self, model: Type[T], **filters) -> Optional[T]:
        async with self.session_maker() as session:
            stmt = select(model).filter_by(**filters)
            result = await session.scalar(stmt)
            return result

    async def get_all(self, model: Type[T], **filters) -> List[T]:
        async with self.session_maker() as session:
            stmt = select(model).filter_by(**filters)
            result = await session.scalars(stmt)
            return result.all()

    async def update(self, model: Type[T], filters: dict, updates: dict) -> Optional[T]:
        async with self.session_maker() as session:
            stmt = select(model).filter_by(**filters)
            obj = await session.scalar(stmt)
            if obj:
                for key, value in updates.items():
                    setattr(obj, key, value)
                await session.commit()
                await session.refresh(obj)
            return obj

    async def delete(self, model: Type[T], **filters) -> Optional[T]:
        async with self.session_maker() as session:
            stmt = select(model).filter_by(**filters)
            obj = await session.scalar(stmt)
            if obj:
                await session.delete(obj)
                await session.commit()
            return obj
