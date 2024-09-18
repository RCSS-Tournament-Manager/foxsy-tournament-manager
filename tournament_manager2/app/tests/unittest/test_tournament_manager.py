import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from managers.tournament_manager import TournamentManager
from models.base import Base
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from models.tournament_model import TournamentModel, TournamentStatus
from managers.database_manager import DatabaseManager
from utils.messages import AddTeamRequestMessage, AddTournamentRequestMessage, AddUserRequestMessage, GetTeamRequestMessage, RegisterTeamInTournamentRequestMessage, RemoveTeamRequestMessage, UpdateTeamRequestMessage

async def get_db_session ()-> DatabaseManager:
    db = DatabaseManager('sqlite+aiosqlite:///:memory:')
    await db.init_db()

    return db

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

@pytest.mark.asyncio
async def test_add_tournament():
    db = await get_db_session()
    async with db as session:
        await make_user(session)
        tm = TournamentManager(db_session=session, minio_client=None)
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T1",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now(),
                                                                       end_registration_at=now() + timedelta(hours=1) + timedelta(minutes=45)))
        assert response is not None
        assert response.success is True
        
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T1",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now(),
                                                                       end_registration_at=now() + timedelta(hours=1) + timedelta(minutes=45)))
        assert response is not None
        assert response.success is False
        assert response.error == 'Tournament name is not unique'
        
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T3",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now(),
                                                                       end_registration_at=now() + timedelta(hours=3) + timedelta(minutes=45)))
        assert response is not None
        assert response.success is False
        
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T4",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now() + timedelta(hours=4),
                                                                       end_registration_at=now() + timedelta(hours=3) + timedelta(minutes=45)))
        assert response is not None
        assert response.success is False
        assert response.error == 'Invalid time range'
        
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T5",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now() + timedelta(hours=3) + timedelta(minutes=50),
                                                                       end_registration_at=now() + timedelta(hours=3) + timedelta(minutes=45)))
        assert response is not None
        assert response.success is False
        assert response.error == 'Invalid time range'
        

@pytest.mark.asyncio
async def test_register_team():
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TournamentManager(db_session=session, minio_client=None)
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T1",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now(),
                                                                       end_registration_at=now() + timedelta(hours=1) + timedelta(minutes=45)))
        
        assert response is not None
        assert response.success is True
        tournament_id = int(response.value)
        
        await update_tournament_status_to_registration(session)
        
        team1 = await make_team(session)
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                tournament_id=tournament_id,
                                                                                team_id=team1.team_id))
        assert response is not None
        assert response.success is True
        
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                 tournament_id=tournament_id,
                                                                                team_id=team1.team_id))
        assert response is not None
        assert response.success is False
        assert response.error == 'Team is already registered'

        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                tournament_name="T2",
                                                                start_at=now() + timedelta(hours=1),
                                                                start_registration_at=now() - timedelta(hours=2),
                                                                end_registration_at=now() + timedelta(seconds=5)))
        assert response is not None
        assert response.success is True    
        tournament_id = int(response.value)
        
        await update_tournament_status_to_registration(session)
        #sleep 10 seconds
        await asyncio.sleep(10)
        
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                tournament_id=tournament_id,
                                                                                team_id=team1.team_id))
        assert response is not None
        assert response.success is False
        assert response.error == 'Registration time is over'    


@pytest.mark.asyncio
async def test_games(): # TODO USE run_game_sender; RMQ
    async_session = await get_db_session()
    async with async_session() as session:
        await make_user(session)
        tm = TournamentManager(db_session=session, minio_client=None)
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T1",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now() - timedelta(seconds=10),
                                                                       end_registration_at=now() + timedelta(second==10)))
        assert response is not None
        assert response.success is True
        # tournament_id = response.tournament_id
        tournament_id = 1
        
        team1 = await make_team(session)
        team2 = await make_team(session, team_name="T2")
        team3 = await make_team(session, team_name="T3")
        team4 = await make_team(session, team_name="T4")
        
        teams = [team1, team2, team3, team4]
        
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                tournament_id=tournament_id,
                                                                                team_id=team1.team_id))
        assert response is not None
        assert response.success is True
        
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                tournament_id=tournament_id,
                                                                                team_id=team2.team_id))
        assert response is not None
        assert response.success is True
        
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                tournament_id=tournament_id,
                                                                                team_id=team3.team_id))
        assert response is not None
        assert response.success is True
        
        response = await tm.register_team(RegisterTeamInTournamentRequestMessage(user_code="123456",
                                                                                tournament_id=tournament_id,
                                                                                team_id=team4.team_id))
        assert response is not None
        assert response.success is True
        
        await tm.create_all_games(tournament_id)
        response = await tm.get_tournament(tournament_id)
        # check all games are created
        for i in range(4):
            for j in range(i+1, 4):
                response.games[i*4+j].left_team_id == teams[i].team_id
                response.games[i*4+j].right_team_id == teams[j].team_id
                response.games[i*4+j].status == 'pending'
        
        team_ids = list(map(lambda team: team.team_id,response.teams))
        for t in teams:
            if t not in team_ids:
                assert False
        

# TODO test remove team when in the tournament or game
# TODO test update team when in the tournament or game