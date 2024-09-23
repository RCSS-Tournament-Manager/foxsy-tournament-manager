from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.database_manager import DatabaseManager
from models import UserModel, TeamModel, TournamentModel, RunnerModel, RunnerLogModel, GameModel
from sqlalchemy.exc import SQLAlchemyError

async def get_db_session():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False)
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables in the in-memory database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return async_session()

async def add_user_to_db(session, user_name, user_code):
    try:
        user_model = UserModel()
        user_model.name = user_name
        user_model.code = user_code
        session.add(user_model)
        await session.commit()
        return user_model
    except SQLAlchemyError as e:
        return None
    except Exception as e:
        return None

async def add_team_to_db(session, user_id, team_name, tournament=None):
    try:
        team_model = TeamModel()
        team_model.user_id = user_id
        team_model.name = team_name
        team_model.base_team = team_name
        if tournament is not None:
            team_model.tournaments.append(tournament)
        session.add(team_model)
        await session.commit()
        return team_model
    except SQLAlchemyError as e:
        return None
    except Exception as e:
        return None

async def add_tournament_to_db(session, owner_id, tournament_name, start_at, start_registration_at, end_registration_at, status, teams=None):
    try:
        tournament_model = TournamentModel()
        tournament_model.owner_id = owner_id
        tournament_model.name = tournament_name
        tournament_model.start_at = start_at
        tournament_model.start_registration_at = start_registration_at
        tournament_model.end_registration_at = end_registration_at
        tournament_model.status = status
        if teams is not None:
            tournament_model.teams = teams
        session.add(tournament_model)
        await session.commit()
        return tournament_model
    except SQLAlchemyError as e:
        return None
    except Exception as e:
        return None

async def add_runner_to_db(session, status, address, available_games_count, start_time, end_time) -> RunnerModel:
    try:
        runner_model = RunnerModel()
        runner_model.status = status
        runner_model.address = address
        runner_model.available_games_count = available_games_count
        runner_model.start_time = start_time
        runner_model.end_time = end_time
        session.add(runner_model)
        await session.commit()
        return runner_model
    except SQLAlchemyError as e:
        return None
    except Exception as e:
        return None

async def add_runner_log_to_db(session, runner_id, message, timestamp):
    try:
        runner_log_model = RunnerLogModel()
        runner_log_model.runner_id = runner_id
        runner_log_model.message = message
        runner_log_model.timestamp = timestamp
        session.add(runner_log_model)
        await session.commit()
        return runner_log_model
    except SQLAlchemyError as e:
        return None
    except Exception as e:
        return None

async def add_game_to_db(session, tournament_id, team1_id, team2_id, status, runner_id=None):
    try:
        game_model = GameModel()
        game_model.tournament_id = tournament_id
        game_model.left_team_id = team1_id
        game_model.right_team_id = team2_id
        game_model.status = status
        if runner_id is not None:
            game_model.runner_id = runner_id
        session.add(game_model)
        await session.commit()
        return game_model
    except SQLAlchemyError as e:
        await session.rollback()
        return None
    except Exception as e:
        return None

class TestDBUtils:
    def __init__(self) -> None:
        self.engine = None
        self.async_session = None
        pass

    async def init(self):
        # Create the async engine
        self.engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False)

        # Create the sessionmaker
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        if self.async_session is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        session = self.async_session()
        return session

async def get_db_manager_and_session():
    db_manager = TestDBUtils()
    await db_manager.init()
    session = await db_manager.get_session()
    return db_manager, session