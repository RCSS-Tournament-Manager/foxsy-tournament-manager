import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.user_manager import UserManager
from models import TournamentModel, UserModel
from utils.messages import AddUserRequestMessage, GetUserRequestMessage, ResponseMessage
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
async def test_add_two_same_users():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User")
        
        response = await user_manager.add_user(add_user_message)
            
        assert isinstance(response, ResponseMessage)
        assert response.success is True
        
        stmt = select(UserModel).filter_by(name="Test User")
        result = await session.execute(stmt)
        new_user = result.scalars().first()

        assert new_user is not None
        assert new_user.name == "Test User"
        
        response = await user_manager.add_user(add_user_message)
        
        assert response.success is False

@pytest.mark.asyncio
async def test_add_two_users_with_same_code():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User")
        
        response = await user_manager.add_user(add_user_message)
            
        assert isinstance(response, ResponseMessage)
        assert response.success is True
        
        stmt = select(UserModel).filter_by(name="Test User")
        result = await session.execute(stmt)
        new_user = result.scalars().first()

        assert new_user is not None
        assert new_user.name == "Test User"
        
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User2")
        
        response = await user_manager.add_user(add_user_message)
        
        assert response.success is False
        
@pytest.mark.asyncio
async def test_get_user_or_create():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User")
        
        response = await user_manager.add_user(add_user_message)
            
        assert isinstance(response, ResponseMessage)
        assert response.success is True
        
        stmt = select(UserModel).filter_by(name="Test User")
        result = await session.execute(stmt)
        new_user = result.scalars().first()

        assert new_user is not None
        assert new_user.name == "Test User"
        
        user = await user_manager.get_user_or_create("123456")
        
        assert user is not None
        assert user.name == "Test User"
        
        user = await user_manager.get_user_or_create("654321")
        
        assert user is not None
        assert user.name == "user_654321"
        
        stmt = select(UserModel).filter_by(name="user_654321")
        result = await session.execute(stmt)
        new_user = result.scalars().first()

        assert new_user is not None
        assert new_user.name == "user_654321"
        
@pytest.mark.asyncio
async def test_get_user():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        
        user_req = GetUserRequestMessage(user_code="123456")
        user = await user_manager.get_user(user_req)
        assert user is None
        
        user_req = GetUserRequestMessage(user_name="123456")
        user = await user_manager.get_user(user_req)
        assert user is None

@pytest.mark.asyncio
async def test_get_user2():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User")
        
        await user_manager.add_user(AddUserRequestMessage(user_code="123456", user_name="Test User"))
        await user_manager.add_user(AddUserRequestMessage(user_code="654321", user_name="Test User2"))
        
        user_req = GetUserRequestMessage(user_code="123456")
        user = await user_manager.get_user(user_req)
        assert user is not None
        assert user.name == "Test User"
        
        user_req = GetUserRequestMessage(user_name="Test User2")
        user = await user_manager.get_user(user_req)
        assert user is not None
        assert user.name == "Test User2"
        assert user.code == "654321"
        
        user_req = GetUserRequestMessage(user_code="654321", user_name="Test User")
        user = await user_manager.get_user(user_req)
        assert user is None
        
        user_req = GetUserRequestMessage(user_code="654321", user_name="Test User2")
        user = await user_manager.get_user(user_req)
        assert user is not None
        assert user.name == "Test User2"

@pytest.mark.asyncio
async def test_get_user_info():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        
        user_req = GetUserRequestMessage(user_code="123456")
        user = await user_manager.get_user_info(user_req)
        assert user is None

@pytest.mark.asyncio
async def test_get_user_info2():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        add_user_message = AddUserRequestMessage(
            user_code="123456",
            user_name="Test User")
        
        await user_manager.add_user(AddUserRequestMessage(user_code="123456", user_name="Test User"))
        await user_manager.add_user(AddUserRequestMessage(user_code="654321", user_name="Test User2"))
        
        user_req = GetUserRequestMessage(user_code="123456")
        user = await user_manager.get_user_info(user_req)
        assert user is not None
        assert user.user_name == "Test User"
        assert user.owned_tournament_ids== []
        assert user.in_tournament_ids == []

@pytest.mark.asyncio
async def test_get_users():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        
        users = await user_manager.get_users()
        assert users is not None
        assert users.users == []
        
@pytest.mark.asyncio
async def test_get_users2():
    async_session = await get_db_session()

    async with async_session() as session:
        user_manager = UserManager(db_session=session)
        await user_manager.add_user(AddUserRequestMessage(user_code="123456", user_name="Test User"))
        await user_manager.add_user(AddUserRequestMessage(user_code="654321", user_name="Test User2"))
        
        users = await user_manager.get_users()
        assert users is not None
        assert len(users.users) == 2
        assert users.users[0].user_name == "Test User"
        assert users.users[1].user_name == "Test User2"
        