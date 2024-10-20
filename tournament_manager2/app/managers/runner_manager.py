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

    async def get_runner_model(self, runner_id: int) -> Optional[RunnerModel]:
        self.logger.info(f"get_runner_model: {runner_id}")
        try:
            stmt = select(RunnerModel).where(RunnerModel.id == runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.warning(f"Runner with id {runner_id} not found")
                return None
            
            return runner
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_runner_model: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in get_runner_model: {e}")
            return None

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
                    available_games_count=runner.available_games_count,
                    requested_command=runner.requested_command
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
            # self.logger.debug("Retrieving runner details...")
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
            # self.logger.debug("Retrieving game details...")
            stmt_game = select(GameModel).options(
                selectinload(GameModel.runner),
                selectinload(GameModel.tournament),
                selectinload(GameModel.left_team),
                selectinload(GameModel.right_team)
            ).where(GameModel.id == json.game_id)
            result_game = await self.db_session.execute(stmt_game)
            game = result_game.scalars().first()
            if not game:
                self.logger.error(f"Game with id {json.game_id} not found")
                return ResponseMessage(success=False, error="Game not found")

            # Update runner
            # self.logger.debug("Updating runner with the new game...")
            runner.games.append(game)

            # Start the game
            # self.logger.debug("Setting game status to RUNNING and assigning port...")
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
            # self.logger.debug("Retrieving runner details...")
            stmt_runner = select(RunnerModel).options(selectinload(RunnerModel.games)).where(RunnerModel.id == json.runner_id)
            result_runner = await self.db_session.execute(stmt_runner)
            runner = result_runner.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {json.runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            # Game
            # self.logger.debug("Retrieving game details...")
            stmt_game = select(GameModel).options(
                selectinload(GameModel.runner),
                selectinload(GameModel.tournament),
                selectinload(GameModel.left_team),
                selectinload(GameModel.right_team)
            ).where(GameModel.id == json.game_id)
            result_game = await self.db_session.execute(stmt_game)
            game = result_game.scalars().first()

            if not game:
                self.logger.error(f"Game with id {json.game_id} not found")
                return ResponseMessage(success=False, error="Game not found")

            # Finish the game
            # self.logger.debug("Updating game status to FINISHED and recording scores...")
            game.status = GameStatusEnum.FINISHED
            game.left_score = json.left_score
            game.right_score = json.right_score
            game.end_time = datetime.utcnow()
            
            # Remove game from runner
            # self.logger.debug("Removing game from runner's active games...")
            runner.games.remove(game)

            # Update Tournament
            # self.logger.debug("Checking if all games in the tournament are finished...")
            stmt_tournament = select(TournamentModel).options(
                selectinload(TournamentModel.owner),
                selectinload(TournamentModel.games),
                selectinload(TournamentModel.teams)
            ).where(TournamentModel.id == game.tournament.id)
            result_tournament = await self.db_session.execute(stmt_tournament)
            tournament = result_tournament.scalars().first()
            if all(g.status == GameStatusEnum.FINISHED for g in tournament.games):
                # self.logger.debug("All games finished. Updating tournament status to FINISHED...")
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
            self.logger.debug("Checking for existing runner with the same address...")
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
                self.logger.debug("Creating a new RunnerModel instance...")
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

    async def send_command_to_runners(self, runner_ids: List[int], command: RequestedCommandToRunnerMessage) -> List[Dict[str, Any]]:
        self.logger.info(f"send_command_to_runners: Sending command '{command}' to runners: {runner_ids}")
        try:
            if not runner_ids or len(runner_ids) == 0:
                self.logger.debug("No runner IDs provided. Fetching all active runners...")
                stmt = select(RunnerModel).where(
                    RunnerModel.status.notin_([RunnerStatusMessageEnum.CRASHED, RunnerStatusMessageEnum.STOPPED])
                )
                result = await self.db_session.execute(stmt)
                runners = result.scalars().all()

                if not runners:
                    self.logger.warning("No runners available to send the command")
                    return []
                
                runner_ids = [runner.id for runner in runners]
                self.logger.info(f"send_command_to_runners: Using all available runners: {runner_ids}")

            responses = []
            for runner_id in runner_ids:
                self.logger.debug(f"Sending command to Runner ID {runner_id}...")
                # TODO: run in tasks
                response = await self.send_command(runner_id, command)
                responses.append({"runner_id": runner_id, "response": response})
            return responses
        except Exception as e:
            self.logger.error(f"send_command_to_runners: Unexpected error: {e}")
            traceback.print_exc()
            return []
                
    async def send_command(self, runner_id: int, req_command: RequestedCommandToRunnerMessage) -> ResponseMessage:
        command = req_command.command
        self.logger.info(f"send_command: Sending command '{command}' to runner {runner_id}")
        try:
            # Retrieve the runner
            runner = await self.get_runner_model(runner_id)
            if not runner:
                self.logger.error(f"send_command: Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")
            
            # Check if the runner is stopped or crashed
            if runner.status in [RunnerStatusMessageEnum.STOPPED, RunnerStatusMessageEnum.CRASHED]:
                self.logger.error(f"send_command: Runner with id {runner_id} is stopped or crashed.")
                return ResponseMessage(success=False, error="Runner is stopped or crashed.")

            if runner.status is not RunnerStatusMessageEnum.PAUSED and command is RunnerCommandMessageEnum.UPDATE:
                if runner.requested_command is RunnerCommandMessageEnum.PAUSE:
                    self.logger.info(f"runner {runner_id} is pausing, please wait for the pause to complete")
                    return ResponseMessage(success=False, error=f"Runner {runner_id} is pausing, please wait for the pause to complete.") 
                else:
                    self.logger.error(f"runner {runner_id} is not paused, cannot send update command")
                    return ResponseMessage(success=False, error=f"Runner {runner_id} is not paused, Cannot send update command.")
            
            if runner.status is RunnerStatusMessageEnum.UPDATING and command is RunnerCommandMessageEnum.RESUME:
                self.logger.info(f"runner {runner_id} is updating, please wait for the update to complete")
                return ResponseMessage(success=False, error=f"Runner {runner_id} is updating, please wait for the update to complete.")
            
            try:
                ip, port = runner.address.split(":")
            except ValueError:
                self.logger.error(f"send_command: Invalid runner address format for runner {runner_id}: {runner.address}")
                return ResponseMessage(success=False, error="Invalid runner address format.")

            RUNNER_API_KEY = "api-key"  # TODO: get from environment variable or configuration file // os.getenv("RUNNER_API_KEY")
            logging.info(f"send_command: Connecting to runner {runner_id} at {ip}:{port} with API key {RUNNER_API_KEY}")
            message_sender = MessageSender(ip, port, RUNNER_API_KEY)

            # Prepare the command data
            command_data = req_command

            self.logger.debug(f"Sending '{command_data}' to the runner...")
            # Send the command
            resp = await message_sender.send_message("runner/receive_command", command_data.model_dump())
            
            if resp.status_code == 200:
                response_data = resp.json()
                if response_data.get("success"):
                    self.logger.info(f"Command '{command}' successfully sent to runner {runner_id}")
                    self.logger.debug("Updating runner's requested_command in the database...")
                    runner.requested_command = command
                    await self.db_session.commit()
                    self.logger.info(f"Runner {runner_id} requested_command updated to '{command}'")
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
                error_message = f"Runner returned status code {resp.status_code}"
                self.logger.error(f"send_command: {error_message}")
                return ResponseMessage(success=False, error=error_message)
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

            # Check if the status needs changing
            if runner.status == status_message.status:
                self.logger.info(f"Runner ID {runner.id} is already in status '{runner.status}'. No update needed.")
                return ResponseMessage(success=True, value="Status is already up-to-date.", error=None)

            self.logger.debug("Updating runner status...")
            runner.status = RunnerStatusMessageEnum(status_message.status)
            runner.last_updated = datetime.utcnow()
            runner.requested_command = RunnerCommandMessageEnum.NONE
            self.logger.info(f"Runner ID {runner.id} status updated to '{runner.status}'.")
            self.logger.info(f"Runner ID {runner.id} requested_command reset to '{runner.requested_command}'.")

            # Commit the transaction
            await self.db_session.commit()

            self.logger.info(f"Runner ID {runner.id} status updated successfully.")
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
