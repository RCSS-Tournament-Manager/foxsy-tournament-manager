import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.user_manager import UserManager
from models import TournamentModel, UserModel
from utils.messages import AddUserRequestMessage, GetUserRequestMessage, ResponseMessage
from pytest import raises
from sqlalchemy import select, exists, and_
from tests.db_utils import add_user_to_db, get_db_session


'''
    Test
    Add a user with same username
'''
@pytest.mark.asyncio
async def test_adding_user_with_non_unique_username():
    session = await get_db_session()
    
    await add_user_to_db(session, "Test User", "123456")
    session.expire_all()
    
    um = UserManager(db_session=session)
    add_user_message = AddUserRequestMessage(
        user_code="654321",
        user_name="Test User")

    response = await um.add_user(add_user_message)
    assert response.success is False


'''
    Test
    Add a user with the same code
'''
@pytest.mark.asyncio
async def test_adding_user_with_non_unique_code():
    session = await get_db_session()
    
    await add_user_to_db(session, "Test User", "123456")
    session.expire_all()
    
    um = UserManager(db_session=session)
    add_user_message = AddUserRequestMessage(
        user_code="123456",
        user_name="Test User3")

    response = await um.add_user(add_user_message)
    assert response.success is False
       
'''
    Test
    get user or create while the user exist
''' 
@pytest.mark.asyncio
async def test_get_user_or_create_user_exist():
    session = await get_db_session()
    await add_user_to_db(session, "Test User", "123456")
    session.expire_all()
    
    um = UserManager(db_session=session)
    user = await um.get_user_or_create("123456")
    
    assert user is not None
    assert user.name == "Test User"
    
'''
    Test
    get user or create while the user does not exist
'''
@pytest.mark.asyncio
async def test_get_user_or_create_user_does_not_exist():
    session = await get_db_session()
    um = UserManager(db_session=session)
    user = await um.get_user_or_create("123456")
    
    assert user is not None
    assert user.name == "user_123456"

'''
    Test
    Get a user that does not exist with usercode and username
'''        
@pytest.mark.asyncio
async def test_get_user_does_not_exist():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    
    user_req = GetUserRequestMessage(user_code="123456")
    user = await user_manager.get_user(user_req)
    assert user.success is False
    assert user.error == "User not found"
    
    user_req = GetUserRequestMessage(user_name="123456")
    user = await user_manager.get_user(user_req)
    assert user.success is False
    assert user.error == "User not found"

'''
    Test
    Get a user that exist with usercode
'''
@pytest.mark.asyncio
async def test_get_user_with_code():
    session = await get_db_session()
    await add_user_to_db(session, "Test User", "123456")
    session.expire_all()
    
    user_manager = UserManager(db_session=session)
    
    user_req = GetUserRequestMessage(user_code="123456")
    user = await user_manager.get_user(user_req)
    assert user is not None
    assert user.name == "Test User"
    
'''
    Test
    Get a user that exist with username
'''
@pytest.mark.asyncio
async def test_get_user_with_name():
    session = await get_db_session()
    await add_user_to_db(session, "Test User", "123456")
    session.expire_all()
    
    user_manager = UserManager(db_session=session)
    user = await user_manager.get_user(GetUserRequestMessage(user_name="Test User"))
    assert user is not None
    assert user.code == "123456"

'''
    Test
    Get a user that exist with usercode and username
'''
@pytest.mark.asyncio
async def test_get_user_with_code_and_name():
    session = await get_db_session()
    await add_user_to_db(session, "Test User", "123456")
    
    user_manager = UserManager(db_session=session)
    user = await user_manager.get_user(GetUserRequestMessage(user_code="123456", user_name="Test User"))
    assert user is not None
    assert user.code == "123456"

'''
    Test
    Get a user info that does not exist with usercode
'''
@pytest.mark.asyncio
async def test_get_user_info_does_not_exist():
    session = await get_db_session()
    
    user_manager = UserManager(db_session=session)
    
    user_req = GetUserRequestMessage(user_code="123456")
    user = await user_manager.get_user_info(user_req)
    assert type(user) is ResponseMessage
    assert user.success is False


'''
    Test
    Get a user info that does exist with usercode
'''
@pytest.mark.asyncio
async def test_get_user_info():
    session = await get_db_session()
    await add_user_to_db(session, "Test User", "123456")
    session.expire_all()
    
    user_manager = UserManager(db_session=session)
    await user_manager.add_user(AddUserRequestMessage(user_code="123456", user_name="Test User"))
    
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
    await add_user_to_db(session, "Test User", "123456")
    await add_user_to_db(session, "Test User2", "654321")
    session.expire_all()
    
    user_manager = UserManager(db_session=session)
    
    users = await user_manager.get_users()
    assert users is not None
    assert len(users.users) == 2
    assert users.users[0].user_name == "Test User"
    assert users.users[1].user_name == "Test User2"
        