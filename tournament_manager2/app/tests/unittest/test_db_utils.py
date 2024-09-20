import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from models.base import Base
from models.user_model import UserModel
from models.team_model import TeamModel
from models.tournament_model import TournamentModel, TournamentStatus
from tests.db_utils import *
from utils.messages import *
import datetime


@pytest.mark.asyncio
async def test_add_user_success():
    session = await get_db_session()
    response = await add_user_to_db(session, "U1", "123456")
    assert response is not None
    assert response.name == "U1"
    assert response.code == "123456"

    session.expunge_all()
    stmt = select(UserModel).filter_by(name="U1")
    result = await session.execute(stmt)
    new_user = result.scalars().first()
    assert new_user is not None
    assert new_user.name == "U1"
    assert new_user.code == "123456"



@pytest.mark.asyncio
async def test_add_team_success():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    response = await add_team_to_db(session, user_model.id, "T1")
    assert response is not None
    assert response.name == "T1"
    assert response.user_id == user_model.id

    session.expunge_all()
    stmt = select(TeamModel).filter_by(name="T1")
    result = await session.execute(stmt)
    new_team = result.scalars().first()
    assert new_team is not None
    assert new_team.name == "T1"
    assert new_team.user_id == user_model.id



@pytest.mark.asyncio
async def test_add_tournament_success():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    response = await add_tournament_to_db(session, user_model.id, "T1", 
                                          datetime.datetime.now() + timedelta(hours=2), 
                                          datetime.datetime.now(), 
                                          datetime.datetime.now() + timedelta(hours=1) + timedelta(minutes=45), 
                                          TournamentStatus.WAIT_FOR_REGISTRATION)
    assert response is not None
    assert response.name == "T1"
    assert response.owner_id == user_model.id

    session.expunge_all()
    stmt = select(TournamentModel).filter_by(name="T1")
    result = await session.execute(stmt)
    new_tournament = result.scalars().first()
    assert new_tournament is not None
    assert new_tournament.name == "T1"
    assert new_tournament.owner_id == user_model.id
