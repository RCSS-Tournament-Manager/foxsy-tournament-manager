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
from models.tournament_model import TournamentModel, TournamentStatus
from tests.db_utils import *
from utils.messages import *
from sqlalchemy.orm import selectinload


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
    response = await add_tournament_to_db(session, user_model.id, "T1", now() + timedelta(hours=2), now(), now() + timedelta(hours=1) + timedelta(minutes=45), TournamentStatus.WAIT_FOR_REGISTRATION)
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

async def make_user(session, user_name, user_code):
    um = UserManager(db_session=session)
    response = await um.add_user(AddUserRequestMessage(user_code=user_code, user_name=user_name))
    
    assert response.success is True
    return response

async def make_team(session, user_code, team_name):
    tm = TeamManager(db_session=session)
    response = await tm.create_team(AddTeamRequestMessage(user_code=user_code, team_name=team_name))
    assert response is not None
    return response

def now():
    return datetime.now()

async def update_tournament_status_to_registration(
    session
):
    current_time = datetime.utcnow()
    result = await session.execute(
        select(TournamentModel)
        .where(
            TournamentModel.status == TournamentStatus.WAIT_FOR_REGISTRATION,
            TournamentModel.start_registration_at <= current_time,
            TournamentModel.status != TournamentStatus.REGISTRATION
        )
    )
    tournaments = result.scalars().all()
    print(f'{len(tournaments)=}')
    for tournament in tournaments:
        tournament.status = TournamentStatus.REGISTRATION
    await session.commit()
    
async def create_all_games(
    session,
    tournament_ids: list[int]
):
    tournament_manager = TournamentManager(session, None)
    
    for tournament_id in tournament_ids:
        await tournament_manager.create_all_games(tournament_id)
    
    
async def update_tournament_status_to_wait_for_start(
    session
):
    tournament_ids = []
    current_time = datetime.utcnow()
    result = await session.execute(
        select(TournamentModel)
        .where(
            TournamentModel.status == TournamentStatus.REGISTRATION,
            TournamentModel.end_registration_at <= current_time,
            TournamentModel.status != TournamentStatus.WAIT_FOR_START
        )
    )
    tournaments = result.scalars().all()
    for tournament in tournaments:
        tournament.status = TournamentStatus.WAIT_FOR_START
        tournament_ids.append(tournament.id)
    await session.commit()
        
    if len(tournament_ids) > 0:
        await create_all_games(session, tournament_ids)

@pytest.mark.asyncio
async def test_add_tournament_success():
    session = await get_db_session()
    
    user_model = await add_user_to_db(session, "U1", "123456")

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.add_tournament(AddTournamentRequestMessage(user_code=user_model.code,
                                                                    tournament_name="T1",
                                                                    start_at=now() + timedelta(hours=2),
                                                                    start_registration_at=now(),
                                                                    end_registration_at=now() + timedelta(hours=1) + timedelta(minutes=45)))
    assert response is not None
    assert response.success is True

    # Check db to be sure that the tournament is added
    session.expunge_all()
    stmt = select(TournamentModel).filter_by(name="T1")
    result = await session.execute(stmt)
    new_tournament = result.scalars().first()
    assert new_tournament is not None
    assert new_tournament.name == "T1"


@pytest.mark.asyncio
async def test_add_tournament_failed_same_name():
    session = await get_db_session()
    user = await add_user_to_db(session, "U1", "123456")
    tournament_model = await add_tournament_to_db(session, user.id, "T1", now() + timedelta(hours=2), now(), now() + timedelta(hours=1) + timedelta(minutes=45), TournamentStatus.WAIT_FOR_REGISTRATION)

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                    tournament_name=tournament_model.name,
                                                                    start_at=now() + timedelta(hours=2),
                                                                    start_registration_at=now(),
                                                                    end_registration_at=now() + timedelta(hours=1) + timedelta(minutes=45)))
    assert response is not None
    assert response.success is False
    assert response.error == 'Tournament name is not unique'

    session.expunge_all()
    # Check db to be sure that the tournament is not added
    stmt = select(TournamentModel).filter_by(name="T1")
    result = await session.execute(stmt)
    tournaments = result.scalars().all()
    assert len(tournaments) == 1


@pytest.mark.asyncio
async def test_add_tournament_failed_invalid_time_range():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.add_tournament(AddTournamentRequestMessage(user_code=user_model.code,
                                                                    tournament_name="T4",
                                                                    start_at=now() + timedelta(hours=2),
                                                                    start_registration_at=now() + timedelta(hours=4),
                                                                    end_registration_at=now() + timedelta(hours=3) + timedelta(minutes=45)))
    assert response is not None
    assert response.success is False
    assert response.error == 'Invalid time range'
    
    response = await tm.add_tournament(AddTournamentRequestMessage(user_code=user_model.code,
                                                                    tournament_name="T5",
                                                                    start_at=now() + timedelta(hours=2),
                                                                    start_registration_at=now() + timedelta(hours=3) + timedelta(minutes=50),
                                                                    end_registration_at=now() + timedelta(hours=3) + timedelta(minutes=45)))
    assert response is not None
    assert response.success is False
    assert response.error == 'Invalid time range'

    # Check db to be sure that the tournament is not added
    session.expunge_all()
    stmt = select(TournamentModel).filter_by(name="T4")
    result = await session.execute(stmt)
    tournaments = result.scalars().all()
    assert len(tournaments) == 0
        

@pytest.mark.asyncio
async def test_register_team_success():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    team_model = await add_team_to_db(session, user_model.id, "T1")
    tournament_model = await add_tournament_to_db(session, user_model.id, "T1", 
                                                  now() + timedelta(hours=2), 
                                                  now(), now() + timedelta(hours=1) + timedelta(minutes=45), 
                                                  TournamentStatus.REGISTRATION)
    
    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_model.id,
                                                                                           team_id=team_model.id))
    assert response is not None
    assert response.success is True

    # Check db to be sure that the team is registered
    session.expunge_all()
    stmt = select(TeamModel).options(selectinload(TeamModel.tournaments)).filter_by(name="T1")
    result = await session.execute(stmt)
    new_team = result.scalars().first()
    assert new_team is not None
    assert new_team.name == "T1"
    assert new_team.tournaments[0].id == tournament_model.id
    

@pytest.mark.asyncio
async def test_register_team_faild_team_already_registered():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    team_model = await add_team_to_db(session, user_model.id, "T1")
    tournament_model = await add_tournament_to_db(session, user_model.id, "T1", now() + timedelta(hours=2), now(), now() + timedelta(hours=1) + timedelta(minutes=45), TournamentStatus.REGISTRATION)

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_model.id,
                                                                                           team_id=team_model.id))
    assert response is not None
    assert response.success is True
    
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_model.id,
                                                                                           team_id=team_model.id))
    assert response is not None
    assert response.success is False
    assert response.error == 'Team is already registered'


@pytest.mark.asyncio
async def test_register_team_faild_team_not_found():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    tournament_model = await add_tournament_to_db(session, user_model.id, "T1", now() + timedelta(hours=2), now(), now() + timedelta(hours=1) + timedelta(minutes=45), TournamentStatus.REGISTRATION)

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_model.id,
                                                                                           team_id=15))
    assert response is not None
    assert response.success is False
    assert response.error == 'Team or tournament not found'


@pytest.mark.asyncio
async def test_register_team_faild_tournament_not_found():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    team_model = await add_team_to_db(session, user_model.id, "T1")

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=12,
                                                                                           team_id=team_model.id))
    assert response is not None
    assert response.success is False
    assert response.error == 'Team or tournament not found'



@pytest.mark.asyncio
async def test_register_team_failed_registration_time_is_over():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    team_model = await add_team_to_db(session, user_model.id, "T1")
    tournament_model = await add_tournament_to_db(session, user_model.id, "T1", 
                                                  now() + timedelta(hours=1), 
                                                  now() - timedelta(hours=2), 
                                                  now() + timedelta(seconds=5), 
                                                  TournamentStatus.WAIT_FOR_START)

    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_model.id,
                                                                                           team_id=team_model.id))
    assert response is not None
    assert response.success is False
    assert response.error == 'Tournament is not in registration phase'    

    # Check db to be sure that the team is not registered
    session.expunge_all()
    stmt = select(TeamModel).options(selectinload(TeamModel.tournaments)).filter_by(name="T1")
    result = await session.execute(stmt)
    new_team = result.scalars().first()
    assert new_team is not None
    assert new_team.name == "T1"
    assert len(new_team.tournaments) == 0

    stmt = select(TournamentModel).options(selectinload(TournamentModel.teams)).filter_by(name="T1")
    result = await session.execute(stmt)
    new_tournament = result.scalars().first()
    assert new_tournament is not None
    assert new_tournament.name == "T1"
    assert len(new_tournament.teams) == 0

'''
    Test
    1. check update_tournament_status_to_registration
    2. check game creation
'''
@pytest.mark.asyncio
async def test_games_creation():
    session = await get_db_session()
    user_model = await add_user_to_db(session, "U1", "123456")
    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.add_tournament(AddTournamentRequestMessage(user_code=user_model.code,
                                                                    tournament_name="T1",
                                                                    start_at=now() + timedelta(hours=2),
                                                                    start_registration_at=now() - timedelta(seconds=10),
                                                                    end_registration_at=now() + timedelta(seconds=10)))
    assert response is not None
    assert response.success is True
    # tournament_id = response.tournament_id
    tournament_id = 1
    
    await update_tournament_status_to_registration(session)
    
    team_model1 = await add_team_to_db(session, user_model.id, "T1")
    team_model2 = await add_team_to_db(session, user_model.id, "T2")
    team_model3 = await add_team_to_db(session, user_model.id, "T3")
    team_model4 = await add_team_to_db(session, user_model.id, "T4")
    
    teams = [team_model1, team_model2, team_model3, team_model4]
    
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_id,
                                                                                           team_id=team_model1.id))
    assert response is not None
    assert response.success is True
    
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_id,
                                                                                           team_id=team_model2.id))
    assert response is not None
    assert response.success is True
    
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_id,
                                                                                           team_id=team_model3.id))
    assert response is not None
    assert response.success is True
    
    response = await tm.register_team_in_tournament(RegisterTeamInTournamentRequestMessage(user_code=user_model.code,
                                                                                           tournament_id=tournament_id,
                                                                                           team_id=team_model4.id))
    assert response is not None
    assert response.success is True
    
    # create games to check all are created in database
    games = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            games.append((teams[i].id, teams[j].id))
            
    await asyncio.sleep(10)
    
    await update_tournament_status_to_wait_for_start(session)
    
    response = await tm.get_tournament(tournament_id)
    assert len(response.teams) == 4
    assert len(response.games) == len(games)
    
    for g in response.games:
        if (g.left_team_id, g.right_team_id) in games:
            games.remove((g.left_team_id, g.right_team_id))
            assert True
        elif (g.right_team_id, g.left_team_id) in games:
            games.remove((g.right_team_id, g.left_team_id))
            assert True
        else:
            assert False
        
    assert len(games) == 0
    
    team_ids = list(map(lambda team: team.team_id,response.teams))
    print(team_ids)
    for t in teams:
        if t.id not in team_ids:
            assert False
        

@pytest.mark.asyncio
async def test_get_user_info_for_tournament_owner():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    
    session.expunge_all()

    tm = TournamentManager(db_session=session, minio_client=None)
    response = await tm.add_tournament(AddTournamentRequestMessage(user_code=user_model1.code,
                                                                    tournament_name="T1",
                                                                    start_at=now() + timedelta(hours=2),
                                                                    start_registration_at=now() - timedelta(seconds=10),
                                                                    end_registration_at=now() + timedelta(seconds=10)))
    
    assert response is not None
    assert response.success is True

    session.expunge_all()

    stmt = select(TournamentModel).filter_by(name="T1")
    result = await session.execute(stmt)
    tournament = result.scalars().first()

    um = UserManager(session)
    response = await um.get_user_info(GetUserRequestMessage(user_code=user_model1.code))
    assert response is not None
    assert response.owned_tournament_ids == [tournament.id]
    

@pytest.mark.asyncio
async def test_remove_team_success():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    
    tournament_model = await add_tournament_to_db(session, user_model1.id, "T1", 
                                                  start_at=now() + timedelta(hours=2),
                                                  start_registration_at=now() - timedelta(seconds=10),
                                                  end_registration_at=now() + timedelta(seconds=10),
                                                  status=TournamentStatus.REGISTRATION)
    
    team1 = await add_team_to_db(session, user_model1.id, "T1", tournament_model)

    session.expunge_all()

    tm = TeamManager(session)
    response = await tm.remove_team(RemoveTeamRequestMessage(user_code="123456", team_id=team1.id))
    assert response is not None
    assert response.success is False
    assert response.error == 'Team is in an ongoing tournament and cannot be deleted.'


@pytest.mark.asyncio
async def test_update_team_success():
    session = await get_db_session()
    user_model1 = await add_user_to_db(session, "U1", "123456")
    
    team1 = await add_team_to_db(session, user_model1.id, "T1")

    session.expunge_all()

    tm = TeamManager(session)

    response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id=team1.id, base_team_name="cyrus", team_config_json="{}"))
    assert response is not None
    assert isinstance(response, GetTeamResponseMessage)

    session.expunge_all()

    stmt = select(TeamModel).filter_by(name="T1")
    result = await session.execute(stmt)
    new_team = result.scalars().first()
    assert new_team is not None
    assert new_team.name == "T1"
    assert new_team.base_team == "cyrus"
    assert new_team.config == "{}"