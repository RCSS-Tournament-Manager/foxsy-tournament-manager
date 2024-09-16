import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.user_manager import UserManager
from models import TournamentModel, UserModel
from utils.messages import AddUserRequestMessage, ResponseMessage
from pytest import raises
from sqlalchemy import select, exists, and_

async def get_db_session():
    # Create in-memory SQLite engine
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False)
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables in the in-memory database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return async_session

@pytest.mark.asyncio
async def test_add_tournament():
    async_session = await get_db_session()

    # Create a session and tournament manager
    async with async_session() as session:
        # Add a dummy user to the database
        
        # Instantiate TournamentManager
        user_manager = UserManager(db_session=session)

        # Create an AddUserRequestMessage
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User")
        
        response = await user_manager.add_user(add_user_message)
            
        # Assert the response is successful
        assert isinstance(response, ResponseMessage)
        assert response.success is True

        # Check if the tournament was added to the database
        stmt = select(UserModel).filter_by(name="Test User")
        result = await session.execute(stmt)
        new_user = result.scalars().first()

        assert new_user is not None
        assert new_user.name == "Test User"
        
        response = await user_manager.add_user(add_user_message)
        
        assert response.success is False
