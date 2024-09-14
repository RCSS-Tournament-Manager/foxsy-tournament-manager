# main.py or a separate module

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exists
from sqlalchemy.orm import selectinload
from models.tournament_model import TournamentModel
from models.game_model import GameModel, GameStatus
from models.team_model import TeamModel
from typing import Dict
from managers.database_manager import DatabaseManager
from utils.rmq_message_sender import RmqMessageSender
from models.message_convertor import GameInfoMessage


def create_game_info_message(game: GameModel, left_team: TeamModel, right_team: TeamModel) -> GameInfoMessage:
    game_info_message = GameInfoMessage(
        game_id=game.id,
        left_team_name=game.left_team.name,
        right_team_name=game.right_team.name,
        left_team_config_json=left_team.config,
        right_team_config_json=right_team.config,
        left_base_team_name=left_team.base_team,
        right_base_team_name=right_team.base_team,
        server_config=""
    )
    game_info_message.fix_json()
    return game_info_message


async def run_game_sender(
    db_manager: DatabaseManager,
    rabbitmq_manager: RmqMessageSender
):
    async for session in db_manager.get_session():
        current_time = datetime.utcnow()
        
        # Subquery to check for pending games
        pending_games_subquery = (
            select(GameModel.id)
            .where(
                GameModel.tournament_id == TournamentModel.id,
                GameModel.status == GameStatus.PENDING
            )
            .exists()
        )

        # Query for tournaments that need processing
        result = await session.execute(
            select(TournamentModel)
            .options(
                selectinload(TournamentModel.teams),
                selectinload(TournamentModel.games)
            )
            .where(
                TournamentModel.done == False,
                TournamentModel.start_at <= current_time,
                pending_games_subquery
            )
        )
        tournaments = result.scalars().all()

        for tournament in tournaments:
            # Process each tournament
            print(f"Processing tournament: {tournament.name}")
            games = tournament.games
            for game in games:
                if game.status != GameStatus.PENDING:
                    continue
                left_team = game.left_team
                right_team = game.right_team
                print(f"Sending game: {left_team.name} vs {right_team.name} to runner")
                game_info_message = create_game_info_message(game, left_team, right_team)
                await rabbitmq_manager.publish_message(
                    queue_name="to_runner_queue",
                    message=game_info_message
                )
                game.status = GameStatus.IN_QUEUE
            await session.commit()


# async def run_game_sender(self):
#         self.logger.info("Running game sender")
#         while True:
#             session = self.db_session
#             current_time = datetime.now()
#             tournaments = (session.query(TournamentModel)
#                         .options(joinedload(TournamentModel.teams), joinedload(TournamentModel.games))
#                         .filter(
#                 TournamentModel.done == False,
#                 TournamentModel.start_at < current_time,
#                 exists().where(
#                     (GameModel.tournament_id == TournamentModel.id) &
#                     (GameModel.status == 'pending')
#                 )
#             ).all())

#             for tournament in tournaments:
#                 self.logger.info(f"Starting tournament: {tournament.name}")
#                 teams = tournament.teams
#                 games = tournament.games
#                 for game in games:
#                     if game.status != GameStatus.PENDING:
#                         continue
#                     left_team = game.left_team
#                     right_team = game.right_team
#                     self.logger.info(f"Sending game: {left_team.name} vs {right_team.name} to runner")
#                     game_info_message = create_game_info_message(game, left_team, right_team)
#                     await self.rmq_message_sender.send_message(game_info_message.dict())
#                     game.status = GameStatus.IN_QUEUE

#                 session.commit()
#             session.close()
#             await asyncio.sleep(10)