# managers/database_manager.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from typing import AsyncGenerator, Optional

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None
        self.async_session: Optional[sessionmaker] = None

    async def init_db(self):
        # Create the async engine
        self.engine = create_async_engine(
            self.database_url, echo=False, future=True
        )

        # Create the sessionmaker
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.async_session is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
