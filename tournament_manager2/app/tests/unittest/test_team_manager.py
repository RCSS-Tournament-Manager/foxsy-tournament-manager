from urllib import response
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from utils.messages import AddTeamRequestMessage, AddUserRequestMessage, GetTeamRequestMessage, RemoveTeamRequestMessage, UpdateTeamRequestMessage

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

async def make_user(session, user_name="U1", user_code="123456"):
    um = UserManager(db_session=session)
    response = await um.add_user(AddUserRequestMessage(user_code=user_code, user_name=user_name))
    
    assert response.success is True
    return response

@pytest.mark.asyncio
async def test_create_team():
    async_session = await get_db_session()
    
    async with async_session() as session:
        await make_user(session)
        tm = TeamManager(db_session=session)
        response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1"
        
        response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1_1"
        
@pytest.mark.asyncio
async def test_get_team():
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TeamManager(db_session=session)
        response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1"
        
        response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=response.team_id))
        assert response is not None
        assert response.team_name == "T1"
        
        with pytest.raises(Exception):
            await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=999))

@pytest.mark.asyncio
async def test_get_team_by_name():
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TeamManager(db_session=session)
        response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1"
        
        response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1"
        
        with pytest.raises(Exception):
            await tm.get_team(GetTeamRequestMessage(user_code="123456", team_name="999"))

@pytest.mark.asyncio
async def test_get_user_teams():
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TeamManager(db_session=session)
        response = tm.get_user_teams("123456")
        assert response is not None
        assert len(response) == 0
        
        response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1"
        response = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert response is not None
        assert response.team_name == "T1_1"
        
        response = await tm.get_user_teams("123456")
        assert response is not None
        assert len(response) == 2
        assert response[0].team_name == "T1"
        assert response[1].team_name == "T1_1"
        
        with pytest.raises(Exception):
            await tm.get_user_teams("999")

@pytest.mark.asyncio
async def test_remove_team():
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TeamManager(db_session=session)
        team = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        assert team is not None
        assert team.team_name == "T1"
        
        response = await tm.remove_team(RemoveTeamRequestMessage(user_code="123456", team_id=team.team_id))
        assert response is not None
        assert response is True
        
        with pytest.raises(Exception):
            await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=team.team_id))
        
        with pytest.raises(Exception):
            response = await tm.remove_team(RemoveTeamRequestMessage(user_code="123456", team_id=999))
        
@pytest.mark.asyncio
async def test_update_team():
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TeamManager(db_session=session)
        team = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T1"))
        team2 = await tm.create_team(AddTeamRequestMessage(user_code="123456", team_name="T10"))
        assert team is not None
        assert team.team_name == "T1"
        print(team.team_id)
        
        with pytest.raises(Exception):
            response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id='999', team_name="T3"))
        
        response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id=team.team_id, team_name="T2"))
        assert response is not None
        assert response.team_name == "T2"
        
        response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=team.team_id))
        assert response is not None
        assert response.team_name == "T2"
        
        with pytest.raises(Exception):
            response = await tm.get_team(GetTeamRequestMessage(user_code="123456", team_id=team.team_id))
            
        response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id=team2.team_id, team_name="T2"))
        assert response is not None
        assert response.team_name == "T2_1"
        
@pytest.mark.asyncio
async def test_get_teams():
    async_session = await get_db_session()
    async with async_session() as session:
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
        
        
        
       
       