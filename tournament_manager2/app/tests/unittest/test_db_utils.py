import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from models.base import Base
from models.user_model import UserModel
from models.team_model import TeamModel
from models.tournament_model import TournamentModel, TournamentStatus
from models.runner_model import RunnerModel, RunnerStatusMessageEnum
from models.game_model import GameModel, GameStatusEnum
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


@pytest.mark.asyncio
async def test_add_runner_success():
    session = await get_db_session()
    response = await add_runner_to_db(session, RunnerStatusMessageEnum.RUNNING, "127.0.0.1:8000", 10, datetime.datetime.now() - timedelta(days=2), None)
    assert response is not None
    assert response.status == RunnerStatusMessageEnum.RUNNING

    session.expunge_all()
    stmt = select(RunnerModel).filter_by(id=response.id)
    result = await session.execute(stmt)
    new_runner = result.scalars().first()
    assert new_runner is not None
    assert new_runner.address == "127.0.0.1:8000"
    assert new_runner.available_games_count == 10
    assert new_runner.start_time is not None
    assert new_runner.end_time is None
    assert new_runner.status == RunnerStatusMessageEnum.RUNNING


@pytest.mark.asyncio
async def test_add_game_success():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    tournament_model = await add_tournament_to_db(session, user_model.id, "T1", 
                                                  datetime.datetime.now() + timedelta(hours=2), 
                                                  datetime.datetime.now(), 
                                                  datetime.datetime.now() + timedelta(hours=1) + timedelta(minutes=45), 
                                                  TournamentStatus.WAIT_FOR_REGISTRATION)
    team1_model = await add_team_to_db(session, user_model.id, "T1", tournament_model)
    team2_model = await add_team_to_db(session, user_model.id, "T2", tournament_model)
    response = await add_game_to_db(session, tournament_model.id, team1_model.id, team2_model.id, GameStatusEnum.PENDING)
    assert response is not None
    assert response.status == GameStatusEnum.PENDING

    session.expunge_all()
    stmt = select(GameModel).filter_by(id=response.id)
    result = await session.execute(stmt)
    new_game = result.scalars().first()
    assert new_game is not None
    assert new_game.status == GameStatusEnum.PENDING
    assert new_game.tournament_id == tournament_model.id
    assert new_game.left_team_id == team1_model.id
    assert new_game.right_team_id == team2_model.id