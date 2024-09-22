# main.py or a separate module

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exists
from sqlalchemy.orm import selectinload
from models.tournament_model import TournamentModel, TournamentStatus
from models.game_model import GameModel, GameStatusEnum
from models.team_model import TeamModel
from typing import Dict
from managers.database_manager import DatabaseManager
from utils.rmq_message_sender import RmqMessageSender
from models.message_convertor import GameInfoMessage
import logging
from managers.tournament_manager import TournamentManager


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


async def update_tournament_status_to_registration(
    db_manager: DatabaseManager
):
    logger = logging.getLogger("update_tournament_status")
    async for session in db_manager.get_session():
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
        for tournament in tournaments:
            tournament.status = TournamentStatus.REGISTRATION
        await session.commit()
        logger.info(f"Updated {len(tournaments)} tournaments to REGISTRATION status")
        

async def create_all_games(
    db_manager: DatabaseManager,
    tournament_ids: list[int]
):
    logger = logging.getLogger("update_tournament_status")
    async for session in db_manager.get_session():
        tournament_manager = TournamentManager(session)
        
        for tournament_id in tournament_ids:
            await tournament_manager.create_all_games(tournament_id)
            logger.info(f"Created games for tournament with id: {tournament_id}")
    
    
async def update_tournament_status_to_wait_for_start(
    db_manager: DatabaseManager
):
    logger = logging.getLogger("update_tournament_status")
    tournament_ids = []
    async for session in db_manager.get_session():
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
        logger.info(f"Updated {len(tournaments)} tournaments to WAIT_FOR_START status")
        
    if len(tournament_ids) > 0:
        await create_all_games(db_manager, tournament_ids)
    

async def update_tournament_status_to_in_progress(
    db_manager: DatabaseManager,
    rabbitmq_manager: RmqMessageSender
):
    logger = logging.getLogger("update_tournament_status")
    async for session in db_manager.get_session():
        current_time = datetime.utcnow()
        result = await session.execute(
            select(TournamentModel)
            .where(
                TournamentModel.status == TournamentStatus.WAIT_FOR_START,
                TournamentModel.start_at <= current_time,
                TournamentModel.status != TournamentStatus.IN_PROGRESS
            )
        )
        tournaments = result.scalars().all()
        for tournament in tournaments:
            tournament.status = TournamentStatus.IN_PROGRESS
        await session.commit()
        logger.info(f"Updated {len(tournaments)} tournaments to IN_PROGRESS status")
        
        for tournament in tournaments:
            # Process each tournament
            logger.info(f"Processing tournament: {tournament.name}")
            games: list[GameModel] = tournament.games
            for game in games:
                left_team = game.left_team
                right_team = game.right_team
                logger.info(f"Sending game: {left_team.name} vs {right_team.name} to runner")
                game_info_message = create_game_info_message(game, left_team, right_team)
                await rabbitmq_manager.publish_message(
                    queue_name="to_runner_queue",
                    message=game_info_message
                )
                game.status = GameStatusEnum.IN_QUEUE
            await session.commit()
        
        
async def run_game_sender(
    db_manager: DatabaseManager,
    rabbitmq_manager: RmqMessageSender
):
    await update_tournament_status_to_registration(db_manager)
    await update_tournament_status_to_wait_for_start(db_manager)
    await update_tournament_status_to_in_progress(db_manager, rabbitmq_manager)
    