from urllib import response
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from models.user_model import UserModel
from models.team_model import TeamModel
from utils.messages import AddTeamRequestMessage, AddUserRequestMessage, GetTeamRequestMessage, GetTeamResponseMessage, GetUserRequestMessage, RemoveTeamRequestMessage, ResponseMessage, UpdateTeamRequestMessage
from tests.db_utils import add_team_to_db, add_user_to_db, get_db_manager_and_session, get_db_session

async def make_user(session, user_name="U1", user_code="123456"):
    await add_user_to_db(session, user_name, user_code)

'''
    Test
    Create a team with the same name to see if the teamname is changed or not
'''
@pytest.mark.asyncio
async def test_create_team_with_same_name():
    dbm, session = await get_db_manager_and_session()
    
    await make_user(session)
    await make_user(session, user_name="U2", user_code="654321")
    tm = TeamManager(db_session=session)
    response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
    assert response is not None
    assert response.team_name == "T1"
    
    response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
    assert response is not None
    assert response.team_name == "T1_1"
    
    # to make sure the statement only gets first user teams
    response = await tm.create_team(AddTeamRequestMessage(user_code="654321", team_name="T2"))
    await session.close()
    
    session = await dbm.get_session()
    stmt = select(TeamModel).select_from(UserModel).where(UserModel.code == '123456').join(UserModel.teams)
    result = await session.execute(stmt)
    team_ids = result.scalars().all()
    assert len(team_ids) == 2
    assert team_ids[0].id == 1
    assert team_ids[1].id == 2
    assert team_ids[0].name == 'T1'
    assert team_ids[1].name == 'T1_1'
    
    stmt = select(TeamModel).select_from(UserModel).where(UserModel.code == '654321').join(UserModel.teams)
    result = await session.execute(stmt)
    team_ids = result.scalars().all()
    assert len(team_ids) == 1
    assert team_ids[0].id == 3
    assert team_ids[0].name == 'T2'

'''
    Test
    get a team that exists with teamname
'''
@pytest.mark.asyncio
async def test_get_team_with_name():
    dbm, session = await get_db_manager_and_session()
    await make_user(session)
    await add_team_to_db(session, 1, "T1")
    session.close()
    
    session = await dbm.get_session()
    tm = TeamManager(db_session=session)
    response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_name='T1'))
    assert response is not None
    assert response.team_name == "T1"
   

'''
    Test
    get a team that exists with teamid
'''
@pytest.mark.asyncio
async def test_get_team_with_teamid():
    dbm, session = await get_db_manager_and_session()
    await make_user(session)
    await add_team_to_db(session, 1, "T1")
    session.close()
    
    session = await dbm.get_session()
    tm = TeamManager(db_session=session)
    response = await tm.get_team(GetTeamRequestMessage(user_code="123456", teamid=1))
    assert response is not None
    assert response.team_name == "T1"   
 
'''
    Test
    get a team that does not exist
'''
@pytest.mark.asyncio
async def test_get_team_does_not_exist():
    dbm, session = await get_db_manager_and_session()
    tm = TeamManager(db_session=session)
    response = await tm.get_team(GetTeamRequestMessage(team_name='T1'))
    assert type(response) == ResponseMessage
    assert response.success == False
    assert response.error == "Team not found"


'''
    Test
    check the teams that the user has (multiple teams)
'''
@pytest.mark.asyncio
async def test_get_user_teams_using_get_user_info():
    dbm, session = await get_db_manager_and_session()
    
    await make_user(session)
    await add_team_to_db(session, 1, "T1")
    await add_team_to_db(session, 1, "T2")
    session.close()

    session = await dbm.get_session()
    um = UserManager(db_session=session)
    response = await um.get_user_info(GetUserRequestMessage(user_code="123456"))
    assert response is not None
    assert len(response.team_ids) == 2
    assert response.team_ids[0] == 1
    assert response.team_ids[1] == 2
    
    response = await um.get_user_info(GetUserRequestMessage(user_code="238473"))
    assert response.success == False

'''
    Test
    remove or update teams with a user that is not the owner
'''  
@pytest.mark.asyncio
async def test_user_access():
    dbm, session = await get_db_manager_and_session()
    
    await make_user(session)
    await make_user(session, user_name="U2", user_code="654321")
    await add_team_to_db(session, 1, "T1")
    session.close()
    
    session = await dbm.get_session()
    tm = TeamManager(db_session=session)
    response = await tm.update_team(UpdateTeamRequestMessage(user_code="654321", team_id=1, team_name="T2"))
    assert response is not None
    assert type(response) == ResponseMessage
    assert response.success == False
    assert response.error == "Team not found or user does not own the team"

    response = await tm.remove_team(RemoveTeamRequestMessage(user_code="654321", team_id=1))
    assert response is not None
    assert type(response) == ResponseMessage
    assert response.success == False
    assert response.error == "Team not found or user does not own the team"

'''
================================UPDATED UNTIL HERE================================================== 
'''        
'''
    Test
    1. remove a team
    2. remove a team that does not exist
    3. check if the team is removed
'''
@pytest.mark.asyncio
async def test_remove_team():
    session = await get_db_session()
    
    await make_user(session)
    tm = TeamManager(db_session=session)
    team = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
    assert team is not None
    assert team.team_name == "T1"
    
    response = await tm.remove_team(RemoveTeamRequestMessage(user_code="123456", team_id=team.team_id))
    assert response is not None
    assert response.success is True
    
    response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=team.team_id))
    assert type(response) == ResponseMessage
    assert response.success == False
    assert response.error == "Team not found"
    
    response = await tm.remove_team(RemoveTeamRequestMessage(user_code="123456", team_id=999))
    assert type(response) == ResponseMessage
    assert response.success == False
    assert response.error == "Team not found or user does not own the team"


'''
    Test
    1. update a team
    2. update a team that does not exist
    3. update a team that the user does not own # TODO NOT tested
    4. check if the team is updated
''' 
@pytest.mark.asyncio
async def test_update_team():
    session = await get_db_session()
    
    await make_user(session)
    await make_user(session, user_name="U2", user_code="654321")
    tm = TeamManager(db_session=session)
    team = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
    team2 = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T10"))
    assert team is not None
    assert team.team_name == "T1"
    print(team.team_id)
    session.expunge_all()
    response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id='999', base_team_name="T3"))
    assert response is not None
    assert type(response) == ResponseMessage
    assert response.success == False
    assert response.error == "Team not found or user does not own the team"
    
    response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id=team.team_id, base_team_name="T2"))
    assert response is not None
    assert type(response) == GetTeamResponseMessage
    assert response.base_team_name == "T2"
    assert response.team_name == "T1"
    
    response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=team.team_id))
    assert response is not None
    assert response.team_name == "T1"
    
    response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id=team2.team_id, base_team_name="T2"))
    assert response is not None
    assert response.team_name == "T10"
    assert response.base_team_name == "T2"
    
    response = await tm.update_team(UpdateTeamRequestMessage(user_code="654321", team_id=team2.team_id, base_team_name="T3"))
    assert response is not None
    assert response.success == False
    assert response.error == "Team not found or user does not own the team"

'''
    Test
    1. get all teams
'''      
@pytest.mark.asyncio
async def test_get_teams(): 
    session = await get_db_session()
    
    await make_user(session)
    await make_user(session, user_name="U2", user_code="654321")
    tm = TeamManager(db_session=session)
    response = await tm.get_teams()
    assert response is not None
    assert len(response.teams) == 0
    
    team = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
    assert team is not None
    assert team.team_name == "T1"
    
    response = await tm.get_teams()
    assert response is not None
    assert len(response.teams) == 1
    assert response.teams[0].team_name == "T1"
    
    team2 = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T10"))
    assert team2 is not None
    assert team2.team_name == "T10"
    
    response = await tm.get_teams()
    assert response is not None
    assert len(response.teams) == 2
    assert response.teams[0].team_name == "T1"
    assert response.teams[1].team_name == "T10"
    
    team3 = await tm.create_team(AddTeamRequestMessage(user_code="654321", team_name="T2"))
    team4 = await tm.create_team(AddTeamRequestMessage(user_code="654321", team_name="T20"))
    
    response = await tm.get_teams()
    assert response is not None
    assert len(response.teams) == 4
    assert response.teams[0].team_name == "T1"
    assert response.teams[1].team_name == "T10"
    assert response.teams[2].team_name == "T2"
    assert response.teams[3].team_name == "T20"
    assert response.teams[0].user_id == 1
    assert response.teams[1].user_id == 1
    assert response.teams[2].user_id == 2
    assert response.teams[3].user_id == 2
        
        
        
       
       