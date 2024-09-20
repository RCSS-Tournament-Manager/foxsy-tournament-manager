from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from managers.database_manager import DatabaseManager
from models import UserModel, TeamModel, TournamentModel

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
    user_model = UserModel()
    user_model.name = user_name
    user_model.code = user_code
    session.add(user_model)
    await session.commit()
    return user_model

async def add_team_to_db(session, user_id, team_name, tournament=None):
    team_model = TeamModel()
    team_model.user_id = user_id
    team_model.name = team_name
    if tournament is not None:
        team_model.tournaments.append(tournament)
    session.add(team_model)
    await session.commit()
    return team_model

async def add_tournament_to_db(session, owner_id, tournament_name, start_at, start_registration_at, end_registration_at, status):
    tournament_model = TournamentModel()
    tournament_model.owner_id = owner_id
    tournament_model.name = tournament_name
    tournament_model.start_at = start_at
    tournament_model.start_registration_at = start_registration_at
    tournament_model.end_registration_at = end_registration_at
    tournament_model.status = status
    session.add(tournament_model)
    await session.commit()
    return tournament_model

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
        async with self.async_session() as session:
            return session

async def get_db_manager_and_session():
    db_manager = TestDBUtils()
    await db_manager.init()
    session = await db_manager.get_session()
    return db_manager, session