# managers/tournament_manager.py

from datetime import datetime
from utils.messages import *
from models.tournament_model import TournamentModel
from models.team_model import TeamModel
from models.game_model import GameModel, GameStatus
from models.message_convertor import MessageConvertor
from sqlalchemy.orm import selectinload
from sqlalchemy import select, exists, and_
import asyncio
import logging
from storage.minio_client import MinioClient
from typing import AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession


class TournamentManager:
    def __init__(self, db_session: AsyncSession, minio_client: MinioClient = None):
        self.logger = logging.getLogger(__name__)
        self.logger.info('TournamentManager created')
        self.db_session = db_session
        self.minio_client = minio_client

    async def add_tournament(self, message: AddTournamentRequestMessage) -> AddTournamentResponseMessage:
        self.logger.info(f"add_tournament: {message}")
        session = self.db_session

        new_tournament = MessageConvertor.convert_add_tournament_request_message_to_tournament_model(message)
        session.add(new_tournament)

        # Perform validation checks
        if len(message.teams) < 2:
            return AddTournamentResponseMessage(tournament_id=None, success=False, error="At least 2 teams are required")

        if len(message.teams) != len(set([team.team_name for team in message.teams])):
            return AddTournamentResponseMessage(tournament_id=None, success=False, error="Teams are not unique")

        if any([len(team.team_name) == 0 or len(team.base_team_name) == 0 for team in message.teams]):
            return AddTournamentResponseMessage(tournament_id=None, success=False, error="Team name and base team name are required")

        await session.commit()
        await session.refresh(new_tournament)

        new_tournament_id = new_tournament.id
        self.logger.debug(f"Added tournament with id: {new_tournament_id} {new_tournament}")

        # Process teams
        new_teams = []
        for team in message.teams:
            team_model = MessageConvertor.convert_team_message_to_team_model(team)
            team_model.tournament_id = new_tournament_id  # Assign foreign key
            new_teams.append(team_model)
            self.logger.debug(f"Adding team: {team_model}")

        session.add_all(new_teams)
        await session.commit()

        # After committing, the team IDs are available
        await session.refresh_all(new_teams)

        # Process games
        new_games = []
        for t1 in range(len(new_teams)):
            for t2 in range(t1 + 1, len(new_teams)):
                team1 = new_teams[t1]
                team2 = new_teams[t2]
                new_game = GameModel(
                    left_team_id=team1.id,
                    right_team_id=team2.id,
                    tournament_id=new_tournament_id,
                    status=GameStatus.PENDING
                )
                new_games.append(new_game)
                self.logger.debug(f"Adding game: {new_game}")

        session.add_all(new_games)
        await session.commit()

        self.logger.info(f"Added tournament, games, teams with tournament id: {new_tournament_id}")
        return AddTournamentResponseMessage(tournament_id=new_tournament_id, success=True, error=None)

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

    async def get_tournaments(self) -> List[TournamentMessage]:
        self.logger.info(f"get_tournaments")
        session = self.db_session

        stmt = select(TournamentModel).options(
            selectinload(TournamentModel.teams),
            selectinload(TournamentModel.games)
        )

        result = await session.execute(stmt)
        tournaments = result.scalars().all()

        tournament_messages = [MessageConvertor.convert_tournament_model_to_tournament_message(tournament) for tournament in tournaments]
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
