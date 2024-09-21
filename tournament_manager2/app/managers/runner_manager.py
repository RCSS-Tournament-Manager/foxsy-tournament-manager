# managers/runner_manager.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.runner_model import RunnerModel, RunnerLogModel, RunnerStatusEnum
from models.game_model import GameModel, GameStatus
import logging

from datetime import datetime
from utils.messages import (
    AddGameResponse,
    GameInfoSummary,
    RegisterGameRunnerRequest,
    ResponseMessage,
    GetRunnerResponseMessage,
    GetAllRunnersResponseMessage,
    GetRunnerLogResponseMessage,
    RunnerLog
)
from sqlalchemy.exc import SQLAlchemyError

class RunnerManager:
    def __init__(self, db_session: AsyncSession):
        self.logger = logging.getLogger(__name__)
        self.logger.info('RunnerManager created')
        self.db_session = db_session

    async def get_runner(self, runner_id: int) -> Optional[GetRunnerResponseMessage]:
        self.logger.info(f"get_runner: {runner_id}")
        try:
            stmt = select(RunnerModel).where(RunnerModel.id == runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.warning(f"Runner with id {runner_id} not found")
                return None

            return GetRunnerResponseMessage(
                id=runner.id,
                start_time=runner.start_time,
                end_time=runner.end_time,
                status=runner.status.value,
                address=runner.address,
                available_games_count=runner.available_games_count
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_runner: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in get_runner: {e}")
            return None

    async def get_all_runners(self) -> List[GetRunnerResponseMessage]:
        self.logger.info("get_all_runners")
        try:
            stmt = select(RunnerModel)
            result = await self.db_session.execute(stmt)
            runners = result.scalars().all()

            return [
                GetRunnerResponseMessage(
                    id=runner.id,
                    start_time=runner.start_time,
                    end_time=runner.end_time,
                    status=runner.status.value,
                    address=runner.address,
                    available_games_count=runner.available_games_count
                ) for runner in runners
            ]
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_all_runners: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in get_all_runners: {e}")
            return []

    async def get_runner_logs(self, runner_id: int) -> List[RunnerLog]:
        self.logger.info(f"get_runner_logs: {runner_id}")
        try:
            stmt = select(RunnerLogModel).where(RunnerLogModel.runner_id == runner_id).order_by(RunnerLogModel.timestamp.desc())
            result = await self.db_session.execute(stmt)
            logs = result.scalars().all()

            return [
                RunnerLog(
                    log_id=log.id,
                    message=log.message,
                    timestamp=log.timestamp
                ) for log in logs
            ]
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_runner_logs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in get_runner_logs: {e}")
            return []

    async def handle_game_started(self, json: AddGameResponse) -> ResponseMessage:
        self.logger.info(f"handle_game_started: {json}")
        try:
            # Retrieve Runner
            stmt_runner = select(RunnerModel).where(RunnerModel.id == json.runner_id)
            result_runner = await self.db_session.execute(stmt_runner)
            runner = result_runner.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {json.runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            if not json.success:
                self.logger.warning(f"Game {json.game_id} failed to start")
                return ResponseMessage(success=False, error="Failed to start game")

            # Retrieve Game
            stmt_game = select(GameModel).where(GameModel.id == json.game_id)
            result_game = await self.db_session.execute(stmt_game)
            game = result_game.scalars().first()

            if not game:
                self.logger.error(f"Game with id {json.game_id} not found")
                return ResponseMessage(success=False, error="Game not found")

            runner.status = RunnerStatusEnum.RUNNING
            runner.start_time = datetime.utcnow()

            game.status = GameStatus.IN_PROGRESS
            game.start_time = datetime.utcnow()

            if game.runner_id != runner.id:
                game.runner_id = runner.id

            await self.db_session.commit()
            self.logger.info(f"Game {json.game_id} started by Runner {json.runner_id}")
            return ResponseMessage(success=True, error=None)
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in handle_game_started: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in handle_game_started: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def handle_game_finished(self, json: GameInfoSummary) -> ResponseMessage:
        self.logger.info(f"handle_game_finished: {json}")
        try:
            # Runner
            stmt_runner = select(RunnerModel).where(RunnerModel.id == json.runner_id)
            result_runner = await self.db_session.execute(stmt_runner)
            runner = result_runner.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {json.runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            # Game
            stmt_game = select(GameModel).where(GameModel.id == json.game_id)
            result_game = await self.db_session.execute(stmt_game)
            game = result_game.scalars().first()

            if not game:
                self.logger.error(f"Game with id {json.game_id} not found")
                return ResponseMessage(success=False, error="Game not found")

            # Update Runner and Game Statuses
            runner.status = RunnerStatusEnum.RUNNING
            runner.end_time = datetime.utcnow()
            game.status = GameStatus.FINISHED
            game.left_score = json.left_score
            game.right_score = json.right_score
            game.end_time = datetime.utcnow()

            # Commit Changes
            await self.db_session.commit()
            self.logger.info(f"Game {json.game_id} finished by Runner {json.runner_id}")
            return ResponseMessage(success=True, error=None)
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in handle_game_finished: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in handle_game_finished: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def register(self, json: RegisterGameRunnerRequest) -> ResponseMessage:
        self.logger.info(f"Attempting to register runner with address: {json.address}")
        try:
            # Check if a runner with the same address already exists
            stmt = select(RunnerModel).where(RunnerModel.address == json.address)
            result = await self.db_session.execute(stmt)
            existing_runner = result.scalars().first()

            if existing_runner:
                self.logger.info(f"Runner with address {json.address} already exists. Updating status to RUNNING.")
                
                # Update the runner's status to RUNNING
                existing_runner.status = RunnerStatusEnum.RUNNING
                existing_runner.start_time = datetime.utcnow()
                existing_runner.end_time = None  # Reset end_time if previously set
                existing_runner.available_games_count = json.available_games_count  # Optionally update this field

                existing_runner.log_event("Runner status updated to RUNNING upon re-registration.")

                await self.db_session.commit()
                self.logger.info(f"Runner with address {json.address} successfully updated to RUNNING.")
                return ResponseMessage(success=True, error=None)
            else:
                self.logger.info(f"No existing runner with address {json.address}. Creating a new runner.")
                
                # Create a new runner
                new_runner = RunnerModel(
                    status=RunnerStatusEnum.RUNNING,  # Set status to RUNNING upon registration
                    address=json.address,
                    available_games_count=json.available_games_count,
                    start_time=datetime.utcnow()
                )
                self.db_session.add(new_runner)
                await self.db_session.commit()
                await self.db_session.refresh(new_runner)
                self.logger.info(f"Registered new runner with id: {new_runner.id} and address: {new_runner.address}")
                return ResponseMessage(success=True, error=None)
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in register: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in register: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def pause_runner(self, runner_id: int) -> ResponseMessage:
        self.logger.info(f"pause_runner: Runner ID {runner_id}")
        try:
            stmt = select(RunnerModel).where(RunnerModel.id == runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            runner.status = RunnerStatusEnum.PAUSED
            runner.end_time = datetime.utcnow()
            runner.log_event("Runner has been paused.")

            await self.db_session.commit()
            self.logger.info(f"Runner {runner_id} has been paused.")
            return ResponseMessage(success=True, error=None)
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in pause_runner: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in pause_runner: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def mark_runner_crashed(self, runner_id: int) -> ResponseMessage:
        self.logger.info(f"mark_runner_crashed: Runner ID {runner_id}")
        try:
            stmt = select(RunnerModel).where(RunnerModel.id == runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            runner.status = RunnerStatusEnum.CRASHED
            runner.end_time = datetime.utcnow()
            runner.log_event("Runner has crashed.")

            await self.db_session.commit()
            self.logger.info(f"Runner {runner_id} marked as crashed.")
            return ResponseMessage(success=True, error=None)
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in mark_runner_crashed: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in mark_runner_crashed: {e}")
            return ResponseMessage(success=False, error=str(e))