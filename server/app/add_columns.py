import asyncio
from sqlalchemy import text
from core.database import engine

async def amend_db():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE vulnerability ADD COLUMN confidence_score INTEGER;"))
            print("Added confidence_score")
        except Exception as e: print(e)

if __name__ == "__main__":
    asyncio.run(amend_db())
