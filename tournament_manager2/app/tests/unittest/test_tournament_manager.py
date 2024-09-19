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
from tests.db_utils import get_db_session
from utils.messages import AddTeamRequestMessage, AddTournamentRequestMessage, AddUserRequestMessage, GetTeamRequestMessage, GetUserRequestMessage, RegisterTeamInTournamentRequestMessage, RemoveTeamRequestMessage, UpdateTeamRequestMessage

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
async def test_add_tournament():
    db = await get_db_session()
    async for session in db():
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
    db = await get_db_session()
    async for session in db():
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
async def test_games_creation(): # TODO USE run_game_sender; RMQ
    db = await get_db_session()
    async for session in db():
        await make_user(session)
        tm = TournamentManager(db_session=session, minio_client=None)
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T1",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now() - timedelta(seconds=10),
                                                                       end_registration_at=now() + timedelta(seconds=10)))
        assert response is not None
        assert response.success is True
        # tournament_id = response.tournament_id
        tournament_id = 1
    
    async for session in db():
        await update_tournament_status_to_registration(session)
    
    async for session in db():
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
    
    # create games to check all are created in database
    games = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            games.append((teams[i].team_id, teams[j].team_id))
            
    await asyncio.sleep(10)
    
    async for session in db():
        await update_tournament_status_to_wait_for_start(session)
    
    async for session in db():
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
            if t.team_id not in team_ids:
                assert False
        

@pytest.mark.asyncio
async def test_remove_or_update_teams_after_games_created():
    db = await get_db_session()
    async for session in db():
        await make_user(session)
        tm = TournamentManager(db_session=session, minio_client=None)
        response = await tm.add_tournament(AddTournamentRequestMessage(user_code="123456",
                                                                       tournament_name="T1",
                                                                       start_at=now() + timedelta(hours=2),
                                                                       start_registration_at=now() - timedelta(seconds=10),
                                                                       end_registration_at=now() + timedelta(seconds=10)))
        assert response is not None
        assert response.success is True
        # tournament_id = response.tournament_id
        tournament_id = 1
    
    async for session in db():
        await update_tournament_status_to_registration(session)
    
    async for session in db():
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
    
    await asyncio.sleep(10)
    
    async for session in db():
        await update_tournament_status_to_wait_for_start(session)
        
    async for session in db():
        um = UserManager(session)
        response = await um.get_user_info(GetUserRequestMessage(user_code="123456"))
        assert response is not None
        assert response.in_tournament_ids == [tournament_id]
        assert response.owned_tournament_ids == [tournament_id]
    
    async for session in db():
        tm = TeamManager(session)
        response = await tm.remove_team(RemoveTeamRequestMessage(user_code="123456", team_id=team1.team_id))
        assert response is not None
        assert response.success is False
        assert response.error == 'Team is in an ongoing tournament and cannot be deleted.'

        response = await tm.update_team(UpdateTeamRequestMessage(user_code="123456", team_id=team1.team_id, team_name="T5"))
        assert response is not None
        assert response.success is False
        assert response.error == 'Team is in an ongoing tournament and cannot be updated.'