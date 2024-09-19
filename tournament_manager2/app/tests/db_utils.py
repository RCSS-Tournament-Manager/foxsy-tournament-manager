from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.database_manager import DatabaseManager

async def get_db_session(): 
    db = DatabaseManager('sqlite+aiosqlite:///:memory:')
    await db.init_db()
    return db.get_session