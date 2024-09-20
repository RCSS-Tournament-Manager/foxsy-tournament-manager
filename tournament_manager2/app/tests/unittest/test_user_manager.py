import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.user_manager import UserManager
from models import TournamentModel, UserModel
from utils.messages import AddUserRequestMessage, GetUserRequestMessage, ResponseMessage
from pytest import raises
from sqlalchemy import select, exists, and_
from tests.db_utils import get_db_session


'''
    Test
    1. Add a user
    2. Add a user with same username
'''
@pytest.mark.asyncio
async def test_add_two_same_users():
    session = await get_db_session()
    
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


'''
    Test
    1. Add a user
    2. Add a user with the same code
'''
@pytest.mark.asyncio
async def test_add_two_users_with_same_code():
    session = await get_db_session()
    
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
       
'''
    Test
    1. Add a user=A
    2. get the user using get_user_or_create with usercode with the A user
    3. get the user using get_user_or_create with new usercode it should be created
''' 
@pytest.mark.asyncio
async def test_get_user_or_create():
    session = await get_db_session()
    
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

'''
    Test
    1. Get a user that does not exist with usercode and username
'''        
@pytest.mark.asyncio
async def test_get_user():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    
    user_req = GetUserRequestMessage(user_code="123456")
    user = await user_manager.get_user(user_req)
    assert user is None
    
    user_req = GetUserRequestMessage(user_name="123456")
    user = await user_manager.get_user(user_req)
    assert user is None

'''
    Test
    1. Get users using username
    2. Get users using usercode
    3. Get users using both username and usercode
'''
@pytest.mark.asyncio
async def test_get_user2():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    
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


'''
    Test
    1. Get a user info that does not exist with usercode
'''
@pytest.mark.asyncio
async def test_get_user_info():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    
    user_req = GetUserRequestMessage(user_code="123456")
    user = await user_manager.get_user_info(user_req)
    assert type(user) is ResponseMessage
    assert user.success is False


'''
    Test
    1. Get a user info that does exist with usercode
'''
@pytest.mark.asyncio
async def test_get_user_info2():
    session = await get_db_session()
    
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

'''
    Test
    1. get all users that do not exist
'''
@pytest.mark.asyncio
async def test_get_users():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    
    users = await user_manager.get_users()
    assert users is not None
    assert users.users == []
 
 
'''
    Test
    1. get all users
'''       
@pytest.mark.asyncio
async def test_get_users2():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    await user_manager.add_user(AddUserRequestMessage(user_code="123456", user_name="Test User"))
    await user_manager.add_user(AddUserRequestMessage(user_code="654321", user_name="Test User2"))
    
    users = await user_manager.get_users()
    assert users is not None
    assert len(users.users) == 2
    assert users.users[0].user_name == "Test User"
    assert users.users[1].user_name == "Test User2"
        