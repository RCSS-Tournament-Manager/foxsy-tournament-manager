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
from models.runner_model import RunnerModel, RunnerStatusEnum
from models.runner_log_model import RunnerLogModel
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from managers.runner_manager import RunnerManager
from models.tournament_model import TournamentModel, TournamentStatus
from models.game_model import GameModel, GameStatusEnum
from tests.db_utils import *
from utils.messages import *
from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_get_runner_success():
    session = await get_db_session()
    response = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:8000", 10, datetime.now(), None)
    assert response is not None
    assert response.status == RunnerStatusEnum.RUNNING
    assert response.address == "127.0.0.1:8000"
    assert response.available_games_count == 10
    assert response.start_time is not None
    assert response.end_time is None

    session.expunge_all()
    
    runner_manager = RunnerManager(session)
    response = await runner_manager.get_runner(response.id)
    assert response is not None
    assert isinstance(response, GetRunnerResponseMessage)
    assert response.id == response.id
    assert response.address == "127.0.0.1:8000"
    assert response.available_games_count == 10
    assert response.start_time is not None
    assert response.end_time is None
    assert response.status == RunnerStatusEnum.RUNNING
    
    
    await session.close()

@pytest.mark.asyncio
async def test_get_runner_failed_runner_not_found():
    session = await get_db_session()
    response = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:8000", 10, datetime.now(), None)
    
    session.expunge_all()
    
    runner_manager = RunnerManager(session)
    response = await runner_manager.get_runner(response.id + 1)
    assert response is not None
    assert isinstance(response, ResponseMessage)
    assert response.success == False
    assert response.error == "Runner not found"
    
    await session.close()

@pytest.mark.asyncio
async def test_get_all_runners_success():
    session = await get_db_session()
    response = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:8000", 10, datetime.now(), None)
    response = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:9000", 10, datetime.now(), None)
    response = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.2:9000", 10, datetime.now(), None)
    
    session.expunge_all()
    
    runner_manager = RunnerManager(session)
    response = await runner_manager.get_all_runners()
    assert response is not None
    assert isinstance(response, GetAllRunnersResponseMessage)
    assert len(response.runners) == 3
    assert any(runner.address == "127.0.0.1:8000" for runner in response.runners)
    assert any(runner.address == "127.0.0.1:9000" for runner in response.runners)
    assert any(runner.address == "127.0.0.2:9000" for runner in response.runners)
    
    await session.close()

@pytest.mark.asyncio
async def test_register_runner_success():
    session = await get_db_session()
    
    runner_manager = RunnerManager(session)
    now_time = datetime.now() - timedelta(days=1)
    register_message = RegisterGameRunnerRequest(
        ip="127.0.0.1",
        port=8000,
        available_games_count=10
    )
    response = await runner_manager.register(register_message)
    assert response is not None
    assert isinstance(response, ResponseMessage)
    assert response.success == True

    session.expunge_all()

    stmt = select(RunnerModel)
    result = await session.execute(stmt)
    assert result is not None
    scalars = result.scalars().all()
    assert len(scalars) == 1
    runner: RunnerModel = scalars[0]
    assert runner is not None
    assert runner.status == RunnerStatusEnum.RUNNING
    assert runner.address == "127.0.0.1:8000"
    assert runner.available_games_count == 10
    assert runner.start_time is not None
    assert runner.start_time > now_time
    assert runner.end_time is None

    await session.close()

@pytest.mark.asyncio
async def test_register_runner_success_duplicate_update():
    session = await get_db_session()
    response = await add_runner_to_db(session, RunnerStatusEnum.PAUSED, "127.0.0.1:8000", 10, datetime.now() - timedelta(days=2), None)
    assert response is not None

    now_time = datetime.now() - timedelta(days=1)

    session.expunge_all()
    
    runner_manager = RunnerManager(session)
    now_time = datetime.now() - timedelta(days=1)
    register_message = RegisterGameRunnerRequest(
        ip="127.0.0.1",
        port=8000,
        available_games_count=10
    )
    response = await runner_manager.register(register_message)
    assert response is not None
    assert isinstance(response, ResponseMessage)
    assert response.success == True

    session.expunge_all()

    stmt = select(RunnerModel)
    result = await session.execute(stmt)
    assert result is not None
    scalars = result.scalars().all()
    assert len(scalars) == 1
    runner: RunnerModel = scalars[0]
    assert runner is not None
    assert runner.status == RunnerStatusEnum.RUNNING
    assert runner.address == "127.0.0.1:8000"
    assert runner.available_games_count == 10
    assert runner.start_time is not None
    assert runner.start_time > now_time
    assert runner.end_time is None

    await session.close()

async def f(session: AsyncSession):
    try:
        stmt_game = select(GameModel).options(selectinload(GameModel.left_team), selectinload(GameModel.right_team)).options(selectinload(GameModel.tournament)).options(selectinload(GameModel.runner)).filter(GameModel.id == 1)
        result_game = await session.execute(stmt_game)
        game = result_game.scalars().first()

        await session.refresh(game)
        # game = await session.merge(game)
        # game.status = GameStatusEnum.IN_PROGRESS
        game.left_score = 3
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        r = str(e)
        return ResponseMessage(success=False, error="Database error occurred")
    except Exception as e:
        return ResponseMessage(success=False, error=str(e))

@pytest.mark.asyncio
async def test_handle_game_started_success():
    session = await get_db_session()
    runner_model = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:8000", 10, datetime.now(), None)
    assert runner_model is not None

    user_model = await add_user_to_db(session, "user1", "code1")
    team_model1 = await add_team_to_db(session, user_model.id, "team1")
    team_model2 = await add_team_to_db(session, user_model.id, "team2")
    tournament_model = await add_tournament_to_db(session, user_model.id, "tournament1", datetime.now(), datetime.now(), datetime.now(), TournamentStatus.IN_PROGRESS)
    game_model: GameModel = await add_game_to_db(session, tournament_model.id, team_model1.id, team_model2.id, GameStatusEnum.IN_QUEUE)
    
    session.expunge_all()

    runner_manager = RunnerManager(session)
    response = await runner_manager.handle_game_started(GameStartedMessage(
        runner_id=runner_model.id,
        game_id=game_model.id,
        success=True,
        port=6000,
        status="starting"
    ))

    assert response is not None
    assert isinstance(response, ResponseMessage)
    assert response.success == True

    session.expunge_all()

    stmt = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.id == runner_model.id)
    result = await session.execute(stmt)
    runner:RunnerModel = result.scalars().first()
    assert runner is not None
    assert runner.status == RunnerStatusEnum.RUNNING
    assert len(runner.games) == 1

    stmt = select(GameModel).where(GameModel.id == game_model.id)
    result = await session.execute(stmt)
    game:GameModel = result.scalars().first()
    assert game is not None
    assert game.status == GameStatusEnum.IN_PROGRESS
    assert game.port == 6000
    assert game.runner_id == runner_model.id

    await session.close()


@pytest.mark.asyncio
async def test_handle_game_finished_success_tournament_not_finished():
    session = await get_db_session()
    runner_model = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:8000", 10, datetime.now(), None)
    user_model = await add_user_to_db(session, "user1", "code1")
    team_model1 = await add_team_to_db(session, user_model.id, "team1")
    team_model2 = await add_team_to_db(session, user_model.id, "team2")
    team_model3 = await add_team_to_db(session, user_model.id, "team3")
    tournament_model = await add_tournament_to_db(session, user_model.id, "tournament1", datetime.now(), datetime.now(), datetime.now(), TournamentStatus.IN_PROGRESS, [team_model1, team_model2, team_model3])
    game_model1 = await add_game_to_db(session, tournament_model.id, team_model1.id, team_model2.id, GameStatusEnum.IN_PROGRESS, runner_model.id)
    game_model2 = await add_game_to_db(session, tournament_model.id, team_model2.id, team_model3.id, GameStatusEnum.IN_PROGRESS, runner_model.id)

    session.expunge_all()

    runner_manager = RunnerManager(session)
    response = await runner_manager.handle_game_finished(GameFinishedMessage(
        runner_id=runner_model.id,
        game_id=game_model1.id,
        left_score=1,
        right_score=2
    ))

    assert response is not None
    assert isinstance(response, ResponseMessage)
    assert response.success == True

    session.expunge_all()

    stmt = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.id == runner_model.id)
    result = await session.execute(stmt)
    runner = result.scalars().first()
    assert runner is not None
    assert runner.status == RunnerStatusEnum.RUNNING
    assert len(runner.games) == 1

    stmt = select(GameModel).where(GameModel.id == game_model1.id)
    result = await session.execute(stmt)
    game: GameModel = result.scalars().first()
    assert game is not None
    assert game.status == GameStatusEnum.FINISHED
    assert game.left_score == 1
    assert game.right_score == 2
    assert game.runner == None

    stmt = select(GameModel).options(selectinload(GameModel.runner)).where(GameModel.id == game_model2.id)
    result = await session.execute(stmt)
    game: GameModel = result.scalars().first()
    assert game is not None
    assert game.status == GameStatusEnum.IN_PROGRESS
    assert game.runner.id == runner_model.id

    stmt = select(TournamentModel).options(selectinload(TournamentModel.games)).options(selectinload(TournamentModel.teams)).where(TournamentModel.id == tournament_model.id)
    result = await session.execute(stmt)
    tournament: TournamentModel = result.scalars().first()
    assert tournament is not None
    assert tournament.status == TournamentStatus.IN_PROGRESS
    assert len(tournament.games) == 2
    assert tournament.done == False
    assert len(tournament.teams) == 3

@pytest.mark.asyncio
async def test_handle_game_finished_success():
    session = await get_db_session()
    runner_model = await add_runner_to_db(session, RunnerStatusEnum.RUNNING, "127.0.0.1:8000", 10, datetime.now(), None)
    user_model = await add_user_to_db(session, "user1", "code1")
    team_model1 = await add_team_to_db(session, user_model.id, "team1")
    team_model2 = await add_team_to_db(session, user_model.id, "team2")
    tournament_model = await add_tournament_to_db(session, user_model.id, "tournament1", datetime.now(), datetime.now(), datetime.now(), TournamentStatus.IN_PROGRESS, [team_model1, team_model2])
    game_model1 = await add_game_to_db(session, tournament_model.id, team_model1.id, team_model2.id, GameStatusEnum.IN_PROGRESS, runner_model.id)

    session.expunge_all()

    runner_manager = RunnerManager(session)
    response = await runner_manager.handle_game_finished(GameFinishedMessage(
        runner_id=runner_model.id,
        game_id=game_model1.id,
        left_score=1,
        right_score=2
    ))

    assert response is not None
    assert isinstance(response, ResponseMessage)
    assert response.success == True

    session.expunge_all()

    stmt = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.id == runner_model.id)
    result = await session.execute(stmt)
    runner = result.scalars().first()
    assert runner is not None
    assert runner.status == RunnerStatusEnum.RUNNING
    assert len(runner.games) == 0

    stmt = select(GameModel).where(GameModel.id == game_model1.id)
    result = await session.execute(stmt)
    game: GameModel = result.scalars().first()
    assert game is not None
    assert game.status == GameStatusMessageEnum.FINISHED
    assert game.left_score == 1
    assert game.right_score == 2
    assert game.runner == None

    stmt = select(TournamentModel).options(selectinload(TournamentModel.games)).options(selectinload(TournamentModel.teams)).where(TournamentModel.id == tournament_model.id)
    result = await session.execute(stmt)
    tournament: TournamentModel = result.scalars().first()
    assert tournament is not None
    assert tournament.status == TournamentStatus.FINISHED
    assert len(tournament.games) == 1
    assert tournament.done == True
    assert len(tournament.teams) == 2
