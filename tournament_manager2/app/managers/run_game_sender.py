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


logger = logging.getLogger("update_tournament_status")

def create_game_info_message(game: GameModel, left_team: TeamModel, right_team: TeamModel) -> GameInfoMessage:
    game_info_message = GameInfoMessage(
        game_id=game.id,
        left_team_name=left_team.name,
        right_team_name=right_team.name,
        left_team_config_json_encoded=left_team.config_encoded,
        right_team_config_json_encoded=right_team.config_encoded,
        left_base_team_name=left_team.base_team,
        right_base_team_name=right_team.base_team,
        server_config=""
    )
    return game_info_message


async def update_tournament_status_to_registration(
    session: AsyncSession
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
    for tournament in tournaments:
        tournament.status = TournamentStatus.REGISTRATION
    await session.commit()
    logger.info(f"Updated {len(tournaments)} tournaments to REGISTRATION status")
        

async def create_all_games(
    session: AsyncSession,
    tournament_ids: list[int]
):
    tournament_manager = TournamentManager(session, None)
    
    for tournament_id in tournament_ids:
        await tournament_manager.create_all_games(tournament_id)
        logger.info(f"Created games for tournament with id: {tournament_id}")
    
    
async def update_tournament_status_to_wait_for_start(
    session: AsyncSession
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
    logger.info(f"Updated {len(tournaments)} tournaments to WAIT_FOR_START status")
        
    if len(tournament_ids) > 0:
        await create_all_games(session, tournament_ids)
    

async def update_tournament_status_to_in_progress(
    session: AsyncSession,
    rabbitmq_manager: RmqMessageSender = None,
    game_list: list[GameInfoMessage] = None
):
    current_time = datetime.utcnow()
    result = await session.execute(
        select(TournamentModel)
        .options(selectinload(TournamentModel.games))
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
            # load left and right team
            game_model = await session.execute(
                select(GameModel)
                .where(GameModel.id == game.id)
                .options(selectinload(GameModel.left_team), selectinload(GameModel.right_team))
            )
            game_model = game_model.scalars().first()

            left_team = game_model.left_team
            right_team = game_model.right_team
            logger.info(f"Sending game: {left_team.name} vs {right_team.name} to runner")
            game_info_message = create_game_info_message(game_model, left_team, right_team)
            logger.info(f"Game info message: {game_info_message}")
            if rabbitmq_manager is not None:
                await rabbitmq_manager.publish_message(
                    message=game_info_message.model_dump(),
                )
            else:
                game_list.append(game_info_message)
            game.status = GameStatusEnum.IN_QUEUE
        await session.commit()
        
        
async def run_game_sender_by_session(
    rabbitmq_manager: RmqMessageSender,
    session: AsyncSession
):
    
    await update_tournament_status_to_registration(session)
    await update_tournament_status_to_wait_for_start(session)
    await update_tournament_status_to_in_progress(session, rabbitmq_manager)
    
async def run_game_sender_by_manager(
    rabbitmq_manager: RmqMessageSender,
    db_manager: DatabaseManager
):
    logger.info("Running game sender by manager")
    async for session in db_manager.get_session():
        await run_game_sender_by_session(rabbitmq_manager, session)