import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from managers.tournament_manager import TournamentManager
from models.base import Base
from models.user_model import UserModel
from models.team_model import TeamModel
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from managers.run_game_sender import *
from models.tournament_model import TournamentModel, TournamentStatus
from tests.db_utils import *
from utils.messages import *
from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_update_tournament_status_to_registration():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    team_model1 = await add_team_to_db(session, "T1", user_model1.id)
    team_model2 = await add_team_to_db(session, "T2", user_model1.id)
    now = datetime.utcnow()
    tournament_model1 = await add_tournament_to_db(session, "Tournament1", 
                                                   user_model1.id, 
                                                   start_registration_at=now,
                                                   end_registration_at=now + timedelta(days=1), 
                                                   start_at=now + timedelta(days=1), 
                                                   status=TournamentStatus.WAIT_FOR_REGISTRATION, 
                                                   teams=[team_model1, team_model2])
    
    session.expunge_all()

    await update_tournament_status_to_registration(session)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)
    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.REGISTRATION
    assert len(tournament.teams) == 2
    assert len(tournament.games) == 0

@pytest.mark.asyncio
async def test_update_tournament_status_to_registration__no_tournament_ready():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    team_model1 = await add_team_to_db(session, "T1", user_model1.id)
    team_model2 = await add_team_to_db(session, "T2", user_model1.id)
    now = datetime.utcnow()
    tournament_model1 = await add_tournament_to_db(session, "Tournament1", 
                                                   user_model1.id, 
                                                   start_registration_at=now + timedelta(days=1),
                                                   end_registration_at=now + timedelta(days=1), 
                                                   start_at=now + timedelta(days=1), 
                                                   status=TournamentStatus.WAIT_FOR_REGISTRATION, 
                                                   teams=[team_model1, team_model2])
    
    session.expunge_all()

    await update_tournament_status_to_registration(session)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)
    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.WAIT_FOR_REGISTRATION
    assert len(tournament.teams) == 2
    assert len(tournament.games) == 0


@pytest.mark.asyncio
async def test_update_tournament_status_to_registration__no_tournament_ready2():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    team_model1 = await add_team_to_db(session, "T1", user_model1.id)
    team_model2 = await add_team_to_db(session, "T2", user_model1.id)
    now = datetime.utcnow()
    tournament_model1 = await add_tournament_to_db(session, "Tournament1", 
                                                   user_model1.id, 
                                                   start_registration_at=now,
                                                   end_registration_at=now + timedelta(days=1), # times are not correct
                                                   start_at=now + timedelta(days=1), 
                                                   status=TournamentStatus.FINISHED, 
                                                   teams=[team_model1, team_model2])
    
    session.expunge_all()

    await update_tournament_status_to_registration(session)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)
    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.FINISHED
    assert len(tournament.teams) == 2
    assert len(tournament.games) == 0


@pytest.mark.asyncio
async def test_update_tournament_status_to_wait_for_start():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    team_model1 = await add_team_to_db(session, "T1", user_model1.id)
    team_model2 = await add_team_to_db(session, "T2", user_model1.id)
    team_model3 = await add_team_to_db(session, "T3", user_model1.id)
    now = datetime.utcnow()
    tournament_model1 = await add_tournament_to_db(session, "Tournament1", 
                                                   user_model1.id, 
                                                   start_registration_at=now,
                                                   end_registration_at=now, 
                                                   start_at=now + timedelta(days=1), 
                                                   status=TournamentStatus.REGISTRATION, 
                                                   teams=[team_model1, team_model2, team_model3])
    
    session.expunge_all()

    await update_tournament_status_to_wait_for_start(session)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)

    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.WAIT_FOR_START
    assert len(tournament.teams) == 3
    assert len(tournament.games) == 3

@pytest.mark.asyncio
async def test_update_tournament_status_to_wait_for_start__no_tournament_ready():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    team_model1 = await add_team_to_db(session, "T1", user_model1.id)
    team_model2 = await add_team_to_db(session, "T2", user_model1.id)
    team_model3 = await add_team_to_db(session, "T3", user_model1.id)
    now = datetime.utcnow()
    tournament_model1 = await add_tournament_to_db(session, "Tournament1", 
                                                   user_model1.id, 
                                                   start_registration_at=now,
                                                   end_registration_at=now + timedelta(days=1), 
                                                   start_at=now + timedelta(days=1), 
                                                   status=TournamentStatus.REGISTRATION, 
                                                   teams=[team_model1, team_model2, team_model3])
    
    session.expunge_all()

    await update_tournament_status_to_wait_for_start(session)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)

    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.REGISTRATION
    assert len(tournament.teams) == 3
    assert len(tournament.games) == 0

@pytest.mark.asyncio
async def test_update_tournament_status_to_in_progress():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    team_model1 = await add_team_to_db(session, "T1", user_model1.id)
    team_model2 = await add_team_to_db(session, "T2", user_model1.id)
    team_model3 = await add_team_to_db(session, "T3", user_model1.id)
    now = datetime.utcnow()
    tournament_model1 = await add_tournament_to_db(session, "Tournament1", 
                                                   user_model1.id, 
                                                   start_registration_at=now,
                                                   end_registration_at=now, 
                                                   start_at=now, 
                                                   status=TournamentStatus.REGISTRATION, 
                                                   teams=[team_model1, team_model2, team_model3])
    
    session.expunge_all()

    await update_tournament_status_to_wait_for_start(session)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)

    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.WAIT_FOR_START
    assert len(tournament.teams) == 3
    assert len(tournament.games) == 3

    session.expunge_all()

    game_list = []
    await update_tournament_status_to_in_progress(session, game_list=game_list)

    session.expunge_all()

    smtp = select(TournamentModel).options(
        selectinload(TournamentModel.teams),selectinload(TournamentModel.games)
    ).where(TournamentModel.id == tournament_model1.id)

    result = await session.execute(smtp)
    tournament = result.scalars().first()
    assert tournament.status == TournamentStatus.IN_PROGRESS
    assert len(tournament.teams) == 3
    assert len(tournament.games) == 3

    assert len(game_list) == 3
