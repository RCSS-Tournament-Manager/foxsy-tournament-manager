from datetime import datetime
from utils.messages import *
from models.tournament_model import TournamentModel, TournamentStatus
from models.team_model import TeamModel
from models.game_model import GameModel, GameStatus
from models.user_model import UserModel
from models.message_convertor import MessageConvertor
from sqlalchemy.orm import selectinload
from sqlalchemy import select, exists, and_
import asyncio
import logging
from storage.minio_client import MinioClient
from typing import AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession


class TournamentManager:
    def __init__(self, db_session: AsyncSession, minio_client: MinioClient):
        self.logger = logging.getLogger(__name__)
        self.logger.info('TournamentManager created')
        self.db_session = db_session
        self.minio_client = minio_client

    async def add_tournament(self, message: AddTournamentRequestMessage) -> ResponseMessage:
        self.logger.info(f"add_tournament: {message}")
        session = self.db_session

        stmt = select(UserModel).filter_by(code=message.user_code)
        user = await session.execute(stmt)
        user = user.scalars().first()
        user_id = user.id
        
        # check tournament name is unique
        stmt = select(TournamentModel).filter_by(name=message.tournament_name)
        result = await session.execute(stmt)
        existing_tournament = result.scalars().first()
        if existing_tournament:
            return ResponseMessage(success=False, error='Tournament name is not unique')
        
        new_tournament = MessageConvertor.convert_add_tournament_request_message_to_tournament_model(message, user_id)
        session.add(new_tournament)

        await session.commit()
        await session.refresh(new_tournament)

        self.logger.debug(f"Added tournament with id: {new_tournament.id} {new_tournament}")

        return ResponseMessage(success=True, error=None)

    async def get_tournament(self, tournament_id: int) -> TournamentMessage:
        self.logger.info(f"get_tournament: {tournament_id}")
        session = self.db_session

        stmt = select(TournamentModel).options(
            selectinload(TournamentModel.teams),
            selectinload(TournamentModel.games)
        ).where(TournamentModel.id == tournament_id)

        result = await session.execute(stmt)
        tournament = result.scalars().first()

        if not tournament:
            return None

        tournament_message = MessageConvertor.convert_tournament_model_to_tournament_message(tournament)
        self.logger.info(f"get_tournament: {tournament_message}")
        return tournament_message

    async def get_tournaments(self) -> GetTournamentsResponseMessage:
        self.logger.info(f"get_tournaments")
        session = self.db_session

        stmt = select(TournamentModel).options(
            selectinload(TournamentModel.teams),
            selectinload(TournamentModel.games)
        )

        result = await session.execute(stmt)
        tournaments = result.scalars().all()
        
        tournament_messages = GetTournamentsResponseMessage()
        tournament_messages.tournaments = [MessageConvertor.convert_tournament_model_to_tournament_summary_message(tournament) for tournament in tournaments]
        self.logger.info(f"get_tournaments: {tournament_messages}")
        return tournament_messages

    async def run_smart_contract(self):
        self.logger.info("Running smart contract")
        while True:
            self.logger.info("Sending request to smart contract")
            await asyncio.sleep(60)

    async def handle_game_started(self, json: AddGameResponse):
        self.logger.info(f"game_started: {json}")
        session = self.db_session

        stmt = select(GameModel).where(GameModel.id == json.game_id)
        result = await session.execute(stmt)
        game = result.scalars().first()

        if not game:
            return
        if not json.success:
            return

        game.status = GameStatus.IN_PROGRESS
        await session.commit()

    async def handle_game_finished(self, json: GameInfoSummary):
        self.logger.info(f"game_finished: {json}")
        session = self.db_session

        stmt = select(GameModel).options(
            selectinload(GameModel.tournament),
            selectinload(GameModel.tournament.games)
        ).where(GameModel.id == json.game_id)

        result = await session.execute(stmt)
        game = result.scalars().first()

        if not game:
            return

        game.status = GameStatus.FINISHED
        game.left_score = json.left_score
        game.right_score = json.right_score

        # Check if all games in the tournament are finished
        tournament = game.tournament
        if all(g.status == GameStatus.FINISHED for g in tournament.games):
            tournament.done = True

        await session.commit()

    async def get_game(self, game_id: int):
        self.logger.info(f"get_game: {game_id}")
        session = self.db_session

        stmt = select(GameModel).options(
            selectinload(GameModel.tournament)
        ).where(GameModel.id == game_id)

        result = await session.execute(stmt)
        game = result.scalars().first()

        if not game:
            return None

        game_message = MessageConvertor.convert_game_model_to_game_message(game)
        self.logger.info(f"get_game: {game_message}")
        return game_message
    
    async def register_team(self, message: RegisterTeamInTournamentRequestMessage) -> ResponseMessage:
        self.logger.info(f"register_team: {message}")
        
        stmt = select(UserModel).filter_by(code=message.user_code)
        user = await self.db_session.execute(stmt)
        user = user.scalars().first()
        user_id = user.id
        
        stmt = select(TeamModel).options(
            selectinload(TeamModel.tournaments)
            ).filter_by(id=message.team_id, user_id=user_id)
        team = await self.db_session.execute(stmt)
        team = team.scalars().first()
        
        stmt = select(TournamentModel).options(
            selectinload(TournamentModel.teams)
            ).filter_by(id=message.tournament_id)
        tournament = await self.db_session.execute(stmt)
        tournament = tournament.scalars().first()
        
        if not team or not tournament:
            return ResponseMessage(success=False, error='Team or tournament not found')
        
        # if tournament.status != TournamentStatus.REGISTRATION:
        #     return ResponseMessage(success=False, error='Tournament is not in registration phase')
        
        # if datetime.now() < tournament.start_registration_at or datetime.now() > tournament.end_registration_at:
        #     return ResponseMessage(success=False, error='Registration time is over')
        
        if team in tournament.teams:
            return ResponseMessage(success=False, error='Team is already registered')
        
        team.tournaments.append(tournament)
        await self.db_session.commit()
        
        return ResponseMessage(success=True, error=None)
        

    # Use self.minio_client in your methods
    async def download_log_file(self, game_id: int, file_path: str):
        self.logger.info(f"Downloading log file for game_id: {game_id}")
        log_file_name = f"{game_id}.zip"

        # Run the blocking I/O operation in a separate thread
        success = await asyncio.to_thread(
            self.minio_client.download_file,
            bucket_name=self.minio_client.game_log_bucket_name,
            object_name=log_file_name,
            file_path=file_path
        )

        if success:
            self.logger.info(f"Log file for game_id {game_id} downloaded successfully.")
        else:
            self.logger.error(f"Failed to download log file for game_id {game_id}.")
