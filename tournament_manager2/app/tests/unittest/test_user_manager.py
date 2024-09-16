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

@pytest.mark.asyncio
async def test_get_user_by_code(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    user_info = GetUserRequestMessage(user_code="123456")
    response = await user_manager.get_user(user_info)
    
    assert isinstance(response, UserModel)
    assert response.name == "Test User"
    
@pytest.mark.asyncio
async def test_same_user(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    add_user_message = AddUserRequestMessage(
        user_code="123456",
        user_name="Test User"
    )
    
    response = await user_manager.add_user(add_user_message)
    
    assert response.success is False
    
@pytest.mark.asyncio
async def test_add_new_user(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    add_user_message = AddUserRequestMessage(
        user_code="654321",
        user_name="New User"
    )
    
    response = await user_manager.add_user(add_user_message)
    
    assert response.success is True

async def test_get_users(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    response = await user_manager.get_users()
    
    assert isinstance(response, list)
    assert len(response) == 2
    assert response[0].name == "Test User"
    assert response[1].name == "New User"
    
@pytest.mark.asyncio
async def test_user_not_found(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    user_info = GetUserRequestMessage(user_code="000000")
    response = await user_manager.get_user(user_info)
    
    assert response is None

@pytest.mark.asyncio
async def test_get_user_by_id(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    user_info = GetUserRequestMessage(user_id=1)
    response = await user_manager.get_user(user_info)
    
    assert isinstance(response, UserModel)
    assert response.name == "Test User"

@pytest.mark.asyncio
async def test_get_user_by_name(db_session):
    session = await db_session.asend(None)
    user_manager = UserManager(db_session=session)
    
    user_info = GetUserRequestMessage(user_name="New User")
    response = await user_manager.get_user(user_info)
    
    assert isinstance(response, UserModel)
    assert response.name == "New User"