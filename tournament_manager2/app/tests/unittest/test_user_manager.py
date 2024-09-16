import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.user_manager import UserManager
from models import TournamentModel, UserModel
from utils.messages import AddUserRequestMessage, GetUserRequestMessage, ResponseMessage
from sqlalchemy import select

# Database and session fixture
@pytest.fixture(name='db_session', scope='session')
async def async_session():
    # Create in-memory SQLite engine
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False)
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables in the in-memory database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide a session object for tests
    while True:
        async with async_session() as session:
            yield session

    # Drop all tables after tests complete (if needed)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Test function using the session fixture
@pytest.mark.asyncio
async def test_add_user(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)

    add_user_message = AddUserRequestMessage(
        user_code="123456",
        user_name="Test User"
    )
    
    response = await user_manager.add_user(add_user_message)
    
    # Assert the response is successful
    assert isinstance(response, ResponseMessage)
    assert response.success is True

    # Check if the user was added to the database
    # stmt = select(UserModel).filter_by(name="Test User")
    # result = await session.execute(stmt)
    # new_user = result.scalars().first()

    # assert new_user is not None
    # assert new_user.name == "Test User"

    # # Attempt to add the same user again
    # response = await user_manager.add_user(add_user_message)
    
    # # Assert that adding a duplicate user fails
    # assert response.success is False

@pytest.mark.asyncio
async def test_get_user(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    user_info = GetUserRequestMessage(user_code="123456")
    response = await user_manager.get_user(user_info)
    
    assert isinstance(response, UserModel)
    assert response.name == "Test User"
    
