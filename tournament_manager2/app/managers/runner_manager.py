# managers/runner_manager.py

from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.runner_model import RunnerModel, RunnerStatusEnum
from models.game_model import GameModel, GameStatusEnum
from models.runner_log_model import RunnerLogModel, LogLevelEnum
from models.tournament_model import TournamentModel, TournamentStatus
import logging
import traceback

from datetime import datetime
from utils.messages import (
    GameStartedMessage,
    GameFinishedMessage,
    RegisterGameRunnerRequest,
    ResponseMessage,
    GetRunnerResponseMessage,
    GetAllRunnersResponseMessage,
    GetRunnerLogResponseMessage,
    RunnerLog
)
from sqlalchemy.exc import SQLAlchemyError

# import aio_pika
# from aio_pika import Message, DeliveryMode, ExchangeType
# import json
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
                status=runner.status.to_RunnerStatusMessageEnum(),
                address=runner.address,
                available_games_count=runner.available_games_count
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
                    status=runner.status.to_RunnerStatusMessageEnum(),
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
                existing_runner.status = RunnerStatusEnum.RUNNING
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
                    status=RunnerStatusEnum.RUNNING,  # Set status to RUNNING upon registration
                    address=address,
                    available_games_count=json.available_games_count,
                    start_time=datetime.utcnow()
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

    async def pause_runner(self, runner_id: int) -> ResponseMessage:
        self.logger.info(f"pause_runner: Runner ID {runner_id}")
        try:
            stmt = select(RunnerModel).where(RunnerModel.id == runner_id)
            result = await self.db_session.execute(stmt)
            runner = result.scalars().first()

            if not runner:
                self.logger.error(f"Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")

            previous_status = runner.status
            runner.status = RunnerStatusEnum.PAUSED
            runner.end_time = datetime.utcnow()

            log = RunnerLogModel(
                runner_id=runner.id,
                message="Runner has been paused.",
                log_level=LogLevelEnum.WARNING,
                previous_status=previous_status,
                new_status=runner.status
            )
            self.db_session.add(log)

            # Commit Changes
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

            previous_status = runner.status
            runner.status = RunnerStatusEnum.CRASHED
            runner.end_time = datetime.utcnow()

            log = RunnerLogModel(
                runner_id=runner.id,
                message="Runner has crashed.",
                log_level=LogLevelEnum.ERROR,
                previous_status=previous_status,
                new_status=runner.status
            )
            self.db_session.add(log)

            # Commit Changes
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

    async def send_command(self, runner_id: int, command: str) -> ResponseMessage:#, command_type: Optional[RunnerCommandTypeEnum] = None, parameters: Optional[Dict[str, str]] = None) -> ResponseMessage:
        self.logger.info(f"send_command: Sending command '{command}' to runner {runner_id} ") # with type '{command_type}' and parameters {parameters}")
        try:
            # Retrieve the runner
            runner_response = await self.get_runner(runner_id)
            if isinstance(runner_response, ResponseMessage) and not runner_response.success:
                self.logger.error(f"send_command: Runner with id {runner_id} not found")
                return ResponseMessage(success=False, error="Runner not found")
            
            runner = runner_response  # Type: GetRunnerResponseMessage

            # Publish the command to RabbitMQ
            # TODO: Implement RabbitMQ Publisher?
            # connection = await aio_pika.connect_robust("amqp://???/")

            # async with connection:
            #     # Create a channel
            #     channel = await connection.channel()

            #     exchange = await channel.declare_exchange(
            #         name='runner_commands', type=ExchangeType.DIRECT
            #     )

            #     message_body = {
            #         "command": command,
            #         "runner_id": runner_id,
            #     }
            #     message = Message(
            #         body=json.dumps(message_body).encode(),
            #         delivery_mode=DeliveryMode.PERSISTENT,
            #     )

            #     routing_key = f"runner.{runner_id}"
            #     await exchange.publish(
            #         message, routing_key=routing_key
            #     )
            
            # TODO: or use API request?
            scheme = "http"  # or "https" if you're using SSL/TLS
            ip=runner.address.split(":")[0]
            port=runner.address.split(":")[1]
            runner_api_url = f"{scheme}://{ip}:{port}/runner/receive_command" #TODO: is this correct?

            # Prepare the command data
            command_data = {
                "command": command,
                # "parameters": parameters or {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(runner_api_url, json=command_data) as resp:
                    if resp.status == 200:
                        response_data = await resp.json()
                        if response_data.get("success"):
                            self.logger.info(f"send_command: Command '{command}' successfully sent to runner {runner_id}")
                            res = ResponseMessage(
                                    success=response_data.get("success"),
                                    error=response_data.get("error"),
                                    value=response_data.get("value"),
                                    message=response_data.get("message"))
                            return res
                        else:
                            error_message = response_data.get("error", "Unknown error")
                            self.logger.error(f"send_command: Runner responded with error: {error_message}")
                            return ResponseMessage(success=False, error=error_message)
                    else:
                        error_message = f"Runner returned status code {resp.status}"
                        self.logger.error(f"send_command: {error_message}")
                        return ResponseMessage(success=False, error=error_message)
            
            self.logger.info(f"send_command: Command '{command}' successfully sent to runner {runner_id}")
            return ResponseMessage(success=True, error=None)
        except Exception as e:
            self.logger.error(f"send_command: Unexpected error: {e}")
            traceback.print_exc()
            return ResponseMessage(success=False, error=str(e))