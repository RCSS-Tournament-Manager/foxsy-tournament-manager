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

async def make_team(session, user_code="123456", team_name="T1"):
    tm = TeamManager(db_session=session)
    response = await tm.create_team(AddTeamRequestMessage(user_code=user_code, team_name=team_name))
    assert response is not None
    return response

