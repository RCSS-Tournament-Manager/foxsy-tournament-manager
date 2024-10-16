# managers/runner_manager.py

from typing import List, Optional, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.runner_model import RunnerModel
from models.game_model import GameModel, GameStatusEnum
from models.runner_log_model import RunnerLogModel, LogLevelEnum
from models.tournament_model import TournamentModel, TournamentStatus
import logging
import traceback
from utils.message_sender import MessageSender
from datetime import datetime
from utils.messages import *
from sqlalchemy.exc import SQLAlchemyError

import aiohttp

class RunnerManager:
    def __init__(self, db_session: AsyncSession):
        self.logger = logging.getLogger(__name__)
        self.logger.info('RunnerManager created')
        self.db_session = db_session

    async def get_runner(self, runner_id: int) -> Union[GetRunnerResponseMessage, ResponseMessage]:
        self.logger.info(f"get_runner: {runner_id}")
        try:
            stmt = select(RunnerModel).where(RunnerModel.id == runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.warning(f"Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")
            
            return GetRunnerResponseMessage(
                id=runner.id,
                start_time=runner.start_time,
                end_time=runner.end_time,
                status=runner.status,
                address=runner.address,
                available_games_count=runner.available_games_count,
                requested_command=runner.requested_command
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_runner: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_runner: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def get_all_runners(self) -> Union[GetAllRunnersResponseMessage, ResponseMessage]:
        self.logger.info("get_all_runners")
        try:
            stmt = select(RunnerModel)
            result = await self.db_session.execute(stmt)
            runners = result.scalars().all()

            runners_list = []
            for runner in runners:
                runners_list.append(GetRunnerResponseMessage(
                    id=runner.id,
                    start_time=runner.start_time,
                    end_time=runner.end_time,
                    status=runner.status,
                    address=runner.address,
                    available_games_count=runner.available_games_count
                ))

            return GetAllRunnersResponseMessage(runners=runners_list)
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_all_runners: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_all_runners: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def get_runner_logs(self, runner_id: int) -> List[RunnerLog]:
        self.logger.info(f"get_runner_logs: {runner_id}")
        try:
            stmt = select(RunnerLogModel).where(RunnerLogModel.runner_id == runner_id).order_by(RunnerLogModel.timestamp.desc())
            result = await self.db_session.execute(stmt)
            logs = result.scalars().all()

            logs_list = []
            for log in logs:
                logs_list.append(RunnerLog(
                    log_id=log.id,
                    message=log.message,
                    timestamp=log.timestamp,
                    log_level=log.log_level.value,
                    previous_status=log.previous_status.value if log.previous_status else None,
                    new_status=log.new_status.value if log.new_status else None
                ))

            return logs_list
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_runner_logs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in get_runner_logs: {e}")
            return []
          
    async def handle_game_started(self, json: GameStartedMessage) -> ResponseMessage:
        self.logger.info(f"handle_game_started: {json}")
        try:
            # Retrieve Runner
            stmt_runner = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.id == json.runner_id)
            result_runner = await self.db_session.execute(stmt_runner)
            runner = result_runner.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {json.runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            if not json.success:
                self.logger.warning(f"Game {json.game_id} failed to start")
                return ResponseMessage(success=False, error="Failed to start game")

            # Retrieve Game
            stmt_game = select(GameModel).options(selectinload(GameModel.runner)).options(selectinload(GameModel.tournament)).options(selectinload(GameModel.left_team)).options(selectinload(GameModel.right_team)).where(GameModel.id == json.game_id)
            result_game = await self.db_session.execute(stmt_game)
            game = result_game.scalars().first()
            if not game:
                self.logger.error(f"Game with id {json.game_id} not found")
                return ResponseMessage(success=False, error="Game not found")

            # Update runner
            runner.games.append(game)

            # Start the game
            game.status = GameStatusEnum.RUNNING
            game.start_time = datetime.utcnow()
            game.port = json.port
            game.runner = runner


            # Commit Changes
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

    async def handle_game_finished(self, json: GameFinishedMessage) -> ResponseMessage:
        self.logger.info(f"handle_game_finished: {json}")
        try:
            # Runner
            stmt_runner = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.id == json.runner_id)
            result_runner = await self.db_session.execute(stmt_runner)
            runner = result_runner.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {json.runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            # Game
            stmt_game = select(GameModel).options(selectinload(GameModel.runner)).options(selectinload(GameModel.tournament)).options(selectinload(GameModel.left_team)).options(selectinload(GameModel.right_team)).where(GameModel.id == json.game_id)
            result_game = await self.db_session.execute(stmt_game)
            game = result_game.scalars().first()

            if not game:
                self.logger.error(f"Game with id {json.game_id} not found")
                return ResponseMessage(success=False, error="Game not found")

            # Finish the game
            game.status = GameStatusEnum.FINISHED
            game.left_score = json.left_score
            game.right_score = json.right_score
            game.end_time = datetime.utcnow()
            
            # Remove game from runner
            runner.games.remove(game)

            # Update Tournament
            # Check if all games in the tournament are finished
            stmt_tournament = select(TournamentModel).options(selectinload(TournamentModel.owner)).options(selectinload(TournamentModel.games)).options(selectinload(TournamentModel.teams)).where(TournamentModel.id == game.tournament.id)
            result_tournament = await self.db_session.execute(stmt_tournament)
            tournament = result_tournament.scalars().first()
            if all(g.status == GameStatusEnum.FINISHED for g in tournament.games):
                tournament.done = True
                tournament.status = TournamentStatus.FINISHED

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
        self.logger.info(f"Attempting to register runner with address: {json.ip}:{json.port}")
        address = f"{json.ip}:{json.port}"
        try:
            # Check if a runner with the same address already exists
            stmt = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.address == address)
            result = await self.db_session.execute(stmt)
            existing_runner = result.scalars().first()

            if existing_runner:
                self.logger.info(f"Runner with address {address} already exists. Updating status to RUNNING.")

                # Update the runner's status to RUNNING
                existing_runner.status = RunnerStatusMessageEnum.RUNNING
                existing_runner.start_time = datetime.utcnow()
                existing_runner.end_time = None  # Reset end_time if previously set
                existing_runner.available_games_count = json.available_games_count  # Optionally update this field

                # Commit Changes
                await self.db_session.commit()
                self.logger.info(f"Runner with address {address} successfully updated to RUNNING.")
                return ResponseMessage(success=True, error=None, value=str(existing_runner.id))
            else:
                self.logger.info(f"No existing runner with address {address}. Creating a new runner.")

                # Create a new runner
                new_runner = RunnerModel(
                    status=RunnerStatusMessageEnum.RUNNING,  # Set status to RUNNING upon registration
                    address=address,
                    available_games_count=json.available_games_count,
                    start_time=datetime.utcnow(),
                    last_updated = datetime.utcnow()
                )
                self.db_session.add(new_runner)
                await self.db_session.commit()
                await self.db_session.refresh(new_runner)
                self.logger.info(f"Registered new runner with id: {new_runner.id} and address: {new_runner.address}")
                return ResponseMessage(success=True, error=None, value=str(new_runner.id))
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in register: {e}")
            return ResponseMessage(success=False, error="Database error occurred")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in register: {e}")
            return ResponseMessage(success=False, error=str(e))

    async def send_command_to_runners(self, runner_ids: List[int], command: RunnerCommandMessageEnum) -> List[Dict[str, Any]]: # A list of responses from each runner.
        self.logger.info(f"send_command_to_runners: Sending command '{command}' to runners: {runner_ids}")
        try:
            if not runner_ids or len(runner_ids) == 0:
                stmt = select(RunnerModel).where(RunnerModel.status != RunnerStatusMessageEnum.CRASHED).where(RunnerModel.status != RunnerStatusMessageEnum.STOPPED) # not crashed or stopped
                result = await self.db_session.execute(stmt)
                runners = result.scalars().all()

                if not runners:
                    self.logger.warning("No runners available to send the command")
                    return []
                
                runner_ids = [runner.id for runner in runners]
                self.logger.info(f"send_command_to_runners: No runner IDs provided. Using all available runners: {runner_ids}")

            responses = []
            for runner_id in runner_ids:
                response = await self.send_command(runner_id, command)
                responses.append({"runner_id": runner_id, "response": response})
            return responses
        except Exception as e:
            self.logger.error(f"send_command_to_runners: Unexpected error: {e}")
            traceback.print_exc()
            return []
                
    async def send_command(self, runner_id: int, command: RunnerCommandMessageEnum) -> ResponseMessage:#, command_type: Optional[RunnerCommandTypeEnum] = None, parameters: Optional[Dict[str, str]] = None) -> ResponseMessage:
        self.logger.info(f"send_command: Sending command '{command}' to runner {runner_id} ") # with type '{command_type}' and parameters {parameters}")
        try:
            # Retrieve the runner
            runner_response = await self.get_runner(runner_id)
            if isinstance(runner_response, ResponseMessage) and not runner_response.success:
                self.logger.error(f"send_command: Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")
            
            runner: RunnerModel = runner_response 
            
            # check if the runner is stopped or crashed
            if runner.status == RunnerStatusMessageEnum.STOPPED or runner.status == RunnerStatusMessageEnum.CRASHED:
                self.logger.error(f"send_command: Runner with id {runner_id} is stopped or crashed.")
                return ResponseMessage(success=False, error="Runner is stopped or crashed.")
            
            ip=runner.address.split(":")[0]
            port=runner.address.split(":")[1]
            RUNNER_API_KEY = "api-key"  # TODO: get from environment variable or configuration file // os.getenv("RUNNER_API_KEY")

            # Prepare the command data
            coommand = RequestedCommandToRunnerMessage(command=command)

            message_sender = MessageSender(ip, port, RUNNER_API_KEY)
            resp = await message_sender.send_message("runner/receive_command", coommand.model_dump())
            
            if resp.status_code == 200:
                response_data = resp.json()
                if response_data.get("success"):
                    self.logger.info(f"send_command: Command '{command}' successfully sent to runner {runner_id}")
                    runner.requested_command = command # todo it does not work
                    await self.db_session.commit()
                    res = ResponseMessage(
                            success=response_data.get("success"),
                            error=response_data.get("error"),
                            value=response_data.get("value"),
                            message=response_data.get("message"))
                    return res
                else:
                    error_message = response_data.get("error", "Unknown error")
                    value_message = response_data.get("value", None)
                    self.logger.error(f"send_command: Runner responded with error: {error_message}")
                    return ResponseMessage(success=False, error=error_message, value=value_message)
            else:
                error_message = f"Runner returned status code {resp.status}"
                # value_message = resp.get("value", None)
                self.logger.error(f"send_command: {error_message}")
                return ResponseMessage(success=False, error=error_message) #, value=value_message)
        except Exception as e:
            self.logger.error(f"send_command: Unexpected error: {e}")
            traceback.print_exc()
            return ResponseMessage(success=False, error=str(e))
    
    async def handle_status_update(self, status_message: RunnerStatusMessage) -> ResponseMessage:
        self.logger.info(f"Handling status update for Runner ID {status_message.runner_id}: {status_message.status}")
        try:

            stmt = select(RunnerModel).where(RunnerModel.id == status_message.runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.error(f"Runner with ID {status_message.runner_id} not found.")
                return ResponseMessage(success=False, error="Runner not found.")

            # Check if the status is needs changing
            if runner.status == status_message.status:
                self.logger.info(f"Runner ID {runner.id} is already in status '{runner.status}'. No update needed.")
                return ResponseMessage(success=True, value="Status is already up-to-date.", error=None)

            runner.status = RunnerStatusMessageEnum(status_message.status)
            runner.last_updated = datetime.utcnow()
            runner.requested_command = RunnerCommandMessageEnum.NONE

            # Commit the transaction
            await self.db_session.commit()

            self.logger.info(f"Runner ID {runner.id} status updated to '{runner.status}' successfully.")
            return ResponseMessage(success=True, value="Runner status updated successfully.", error=None)
        
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            self.logger.error(f"Database error in handle_status_update: {e}")
            return ResponseMessage(success=False, error="Database error occurred.")
        
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Unexpected error in handle_status_update: {e}")
            traceback.print_exc()
            return ResponseMessage(success=False, error=str(e))
