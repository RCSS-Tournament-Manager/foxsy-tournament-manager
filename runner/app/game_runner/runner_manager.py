import asyncio
from utils.tools import Tools
from game_runner.game import Game
import logging
import os
from storage.storage_client import StorageClient
from data_dir import DataDir
from utils.messages import *
from utils.message_sender import MessageSender
from storage.downloader import Downloader
from enum import Enum
import requests

class RunnerManager:
    def __init__(self, data_dir: str, storage_client: StorageClient, message_sender: MessageSender, runner_id: int, config: dict):
        self.logger = logging.getLogger(__name__)
        self.logger.info('GameRunnerManager created')
        self.available_games_count = 0
        self.available_ports = []
        self.games: dict[int, Game] = {}
        self.data_dir = data_dir
        self.storage_client = storage_client
        self.message_sender = message_sender
        self.check_server()
        self.lock = asyncio.Lock()
        self.runner_id = runner_id
        self.status = RunnerStatusMessageEnum.RUNNING
        self.requested_command: RunnerCommandMessageEnum = None
        self.config = config
        
    def check_server(self):
        server_dir = os.path.join(self.data_dir, DataDir.server_dir_name)
        server_path = os.path.join(server_dir, 'rcssserver')
        if not os.path.exists(server_dir):
            self.logger.info(f'Creating server directory: {server_dir}')
            os.makedirs(server_dir)
        if not os.path.exists(server_path) and self.storage_client is not None:
            if self.storage_client.check_connection():
                self.storage_client.download_file(self.storage_client.server_bucket_name, 'rcssserver', server_path)
            else:
                self.logger.error(f'Storage connection error, server not found')

        if not os.path.exists(server_path):
            Downloader.download_server(server_dir)

        if not os.path.exists(server_path):
            raise FileNotFoundError(f'Server not found')

    def set_available_games_count(self, max_games_count):
        self.logger.info(f'GameRunnerManager set_available_games_count: {max_games_count}')
        self.available_games_count = max_games_count
        self.available_ports = list(range(6000, 6000 + 10 * max_games_count, 10))
        self.logger.info(f'GameRunnerManager available_ports: {self.available_ports}')

    def get_available_port(self):
        if self.available_games_count == 0:
            return None
        port = self.available_ports.pop()
        self.logger.info(f'GameRunnerManager get_available_port: {port}')
        return port

    def free_port(self, port):
        self.logger.info(f'GameRunnerManager free_port: {port}')
        self.available_games_count += 1
        self.available_ports.append(port)

    async def add_game(self, game_info: GameInfoMessage, called_from_rabbitmq: bool = False) -> GameStartedMessage:
        async with self.lock:
            #TODO try except
            self.logger.info(f'GameRunnerManager adding game: {game_info}')
            if self.status != RunnerStatusMessageEnum.RUNNING:
                self.logger.warning(f'GameRunnerManager add_game: Runner is not running. Current status: {self.status}')
                return GameStartedMessage(game_id=game_info.game_id, success=False, runner_id=self.runner_id, error=f'Runner is {self.status}')
            if self.available_games_count == 0:
                self.logger.warning(f'GameRunnerManager add_game: No available games')
                return GameStartedMessage(game_id=game_info.game_id, success=False, runner_id=self.runner_id, error='No available games')
            self.logger.info(f'GameRunnerManager add_game: {game_info}')
            port = self.get_available_port()
            if port is None:
                self.logger.warning(f'GameRunnerManager add_game: No available ports')
                return GameStartedMessage(game_id=game_info.game_id, success=False, runner_id=self.runner_id, error='No available ports')
            self.available_games_count -= 1
            game = Game(game_info, port, self.data_dir, self.storage_client)
            game.finished_event = self.on_finished_game
            self.games[port] = game
            self.games[port].check()
            asyncio.create_task(game.run_game())
            res = GameStartedMessage(game_id=game_info.game_id, success=True, port=port, runner_id=self.runner_id)
            if called_from_rabbitmq:
                try:
                    game_started_message = GameStartedMessage(game_id=game_info.game_id, port=port, success=True, runner_id=self.runner_id)
                    if self.message_sender is not None:
                        await self.message_sender.send_message('from_runner/game_started', game_started_message.model_dump())
                except Exception as e:
                    self.logger.error(f'GameRunnerManager add_game (Can not send game_started message): {e}')
            return res

    async def on_finished_game(self, game: Game):
        async with self.lock:
            try:
                self.logger.info(f'GameRunnerManager on_finished_game: Game{game.game_info.game_id}')
                self.free_port(game.port)
                game_finished_message = GameFinishedMessage(game_id=game.game_info.game_id, 
                                                            success=True, 
                                                            left_score=game.game_result[0],
                                                            right_score=game.game_result[1],
                                                            left_penalty=game.game_result[2],
                                                            right_penalty=game.game_result[3],
                                                            runner_id=self.runner_id)
                if self.message_sender is not None:
                    await self.message_sender.send_message('from_runner/game_finished', game_finished_message.model_dump())
                del self.games[game.port]
            except Exception as e:
                self.logger.error(f'GameRunnerManager on_finished_game: {e}')

    def get_games(self):
        self.logger.info(f'GameRunnerManager get_games')
        res: GetGamesResponse = GetGamesResponse(games=[])
        for game in self.games.values():
            res.games.append(game.to_summary())
        return res

    async def stop_game_by_port(self, port: int):
        self.logger.info(f'GameRunnerManager stop_game_by_port: {port}')
        game = self.games.get(port)
        res: StopGameResponse = StopGameResponse(game_port=port, success=False)
        if game is None:
            self.logger.error(f'GameRunnerManager stop_game_by_port[{port}]: game not found')
            res.error = 'Game not found'
            return res
        res.game_id = game.game_info.game_id
        try:
            await game.stop()
        except Exception as e:
            self.logger.error(f'GameRunnerManager stop_game_by_port[{port}]: {e}')
            res.error = str(e)
            return res
        res.success = True
        return res

    def get_game_by_game_id(self, game_id: int):
        self.logger.info(f'GameRunnerManager get_game_by_game_id: {game_id}')
        for port, game in self.games.items():
            if game.game_info.game_id == game_id:
                return game
        return None

    async def stop_game_by_game_id(self, game_id: int):
        self.logger.info(f'GameRunnerManager stop_game_by_game_id: {game_id}')
        game = self.get_game_by_game_id(game_id)
        res: StopGameResponse = StopGameResponse(game_id=game_id, success=False)
        if game is None:
            self.logger.error(f'GameRunnerManager stop_game_by_game_id[{game_id}]: game not found')
            res.error = 'Game not found'
            return res
        res.game_port = game.port
        try:
            await game.stop()
        except Exception as e:
            self.logger.error(f'GameRunnerManager stop_game_by_game_id[{game_id}]: {e}')
            res.error = str(e)
            return res
        res.success = True
        return res

    async def get_status(self):
        return ResponseMessage(value=self.status)

    async def receive_command(self, req_command: RequestedCommandToRunnerMessage) -> ResponseMessage:
        self.logger.info(f'GameRunnerManager receive_command: {req_command}')
        command = req_command.command
        try:
            if command == RunnerCommandMessageEnum.PAUSE:
                if self.status == RunnerStatusMessageEnum.PAUSED:
                    self.logger.warning("Runner is already paused.")
                    return ResponseMessage(success=False, error="400", value="Runner is already paused.")
                else:
                    self.requested_command = command
                    self.logger.info("Pausing Runner: No longer accepting new games.")
                    return ResponseMessage(success=True, value="Runner is pausing. No new games will be accepted.")
            elif command == RunnerCommandMessageEnum.RESUME:
                if self.status == RunnerStatusMessageEnum.RUNNING:
                    self.logger.warning("Runner is already running.")
                    return ResponseMessage(success=False, error="400", value="Runner is already running.")
                elif self.status == RunnerStatusMessageEnum.UPDATING:
                    self.logger.warning("Runner is updating, Can't resume.")
                    return ResponseMessage(success=False, error="400", value="Runner is updating, Can't resume.")
                else:
                    self.requested_command = command
                    self.logger.info("Resuming Runner: Accepting new games.")
                    return ResponseMessage(success=True, value="Runner has resumed accepting games.")
            elif command == RunnerCommandMessageEnum.STOP:
                    self.requested_command = command
                    self.logger.info("Stopping Runner: Initiating shutdown.")
                    return ResponseMessage(success=True, value="Runner is stopping.")
            elif command == RunnerCommandMessageEnum.HELLO:
                self.logger.info("Hello - Command from TM")
                return ResponseMessage(success=True, value="Hello, TM!", obj={"success": True, "value": "Hello - Direct Command, TM!", "error": None})
            elif command == RunnerCommandMessageEnum.UPDATE:
                if self.status == RunnerStatusMessageEnum.RUNNING:
                    self.logger.warning("Runner is already running, Can't update.")
                    return ResponseMessage(success=False, error="400", value="Runner is running, Can't update.")
                self.logger.info("Update Command from TM")
                try: 
                    self.requested_command = command
                    # asyncio.create_task(self.update_status_to(RunnerStatusMessageEnum.UPDATING))
                    try:
                        self.logger.info('RunnerManager checking base teams')
                        print(self.config)
                        print(self.config['base_teams'])
                        if 'base_teams' not in self.config or self.config['base_teams'] is None:
                            self.logger.error('No base teams found in config')
                            # asyncio.create_task(self.update_status_to(RunnerStatusMessageEnum.PAUSED))
                            self.requested_command = RunnerCommandMessageEnum.PAUSE     
                            return ResponseMessage(success=False, error="400", value="No base teams found in config")
                        asyncio.create_task(self.update_all_default_base_teams(req_command=req_command))
                        self.logger.info('RunnerManager updating base teams')
                        # await self.update_all_default_base_teams(req_command=req_command)
                    except Exception as e:
                        self.logger.error(f'Error on updating base teams: {e}')
                        return ResponseMessage(success=False, error=str(e))
                    
                    return ResponseMessage(success=True, value="Update Command recived", obj={"success": True, "value": "Update Command recived", "error": None})
                except Exception as e:
                    self.logger.error(f'Error on updating base teams: {e}')
                    return ResponseMessage(success=False, error=str(e))
            else:
                raise ValueError(f"Unknown command: {command}")
        except Exception as e:
            self.logger.error(f'GameRunnerManager receive_command[{command}]: {e}')
            return ResponseMessage(success=False, error=str(e))

    async def update_status_to(self, new_status: RunnerStatusMessageEnum):
        self.logger.info(f'GameRunnerManager update_status_to: {new_status}')
        self.status = new_status
        # Notify TM about the pause
        pause_status = RunnerStatusMessage(runner_id=self.runner_id,status=self.status,timestamp=datetime.utcnow().isoformat())
        if self.message_sender:
            await self.message_sender.send_message('from_runner/status_update', pause_status.model_dump())
            # await self.send_status_log(self.pv_status, self.status)
    
    async def send_status_log(self,pv_status, status):
        log = SubmitRunnerLog(
            runner_id=self.runner_id,
            message=f"Status changed from {pv_status} to {status}.",
            log_level=LogLevelMessageEnum.INFO,
            timestamp=datetime.utcnow().isoformat()
        )
        await self.message_sender.send_message('from_runner/submit_log', log.model_dump())
    
    async def shutdown(self): # TODO: there is one in main.py
        self.logger.info("Shutting down the Runner...")
        self.logger.info("Runner has shutdown.")
        await asyncio.sleep(1)
        await asyncio.get_event_loop().stop()
    
    async def update_all_default_base_teams(self, req_command: RequestedCommandToRunnerMessage):
        self.logger.info('GameRunnerManager update_all_default_base_teams')
        teams = req_command.base_teams
        use_git = req_command.use_git
        if teams is None or len(teams) == 0:
            self.logger.warning('No base teams found in command, update all teams')
            teams = self.config['base_teams']
        self.logger.info(f"Updating base teams")
        for base_team in teams:
            self.logger.info(f"Updating base team: {base_team}")
            # await asyncio.sleep(5)
            try:
                if use_git:
                    if base_team['download']['type'] == 'url':
                        await self.update_base_url(base_team['name'], base_team['download']['url'])
                    else:
                        self.logger.error(f'error no url found in base team: {base_team}')
                else:
                    if base_team['download']['type'] == 'minio':
                        await self.update_base_minio(base_team['name'], base_team['download']['bucket'], base_team['download']['object'])
                    else:
                        self.logger.error(f'error no minio found in base team: {base_team}')
            except Exception as e:
                self.logger.error(f'Error on downloading team: {e}')
                continue
        self.requested_command = RunnerCommandMessageEnum.PAUSE        

    async def update_base_minio(
            self, 
            base_team_name: str, 
            bucket_name: str,
            file_name: str
        ):
        self.logger.info(f'GameRunnerManager minio update_base: {base_team_name}, github')


        base_teams_dir = os.path.join(self.data_dir, DataDir.base_team_dir_name)
        base_team_path = os.path.join(base_teams_dir, base_team_name)
        self.logger.debug(f'Check base team {base_team_name}, path: {base_team_path}, dir: {base_teams_dir}')


        #  -- check if base team already exists
        if os.path.exists(base_team_path) and \
            not os.path.exists(os.path.join(base_team_path, 'start.sh')):
            
            self.logger.debug(f'Base team {base_team_name} already exists')
            self.logger.error(f'Base team {base_team_name} start.sh not found')
            Tools.remove_dir(base_team_path)
                

        #  -- check if base team dir is not a file
        if os.path.isfile(base_teams_dir):
            self.logger.error(f'Base teams dir {base_teams_dir} is a file')
            Tools.remove_dir(base_teams_dir)



        #  -- create base team dir if not exists
        if not os.path.exists(base_teams_dir):
            self.logger.info(f'Creating base teams directory: {base_teams_dir}')
            os.makedirs(base_teams_dir, exist_ok=True)

        
        base_team_zip_path = os.path.join(base_teams_dir, f'{base_team_name}.zip')
        zip_file_downloaded = False

        self.logger.debug(f'Downloading base team {base_team_name} from storage')
        try:
            self.storage_client.download_file(
                bucket_name,
                file_name,
                base_team_zip_path
            )
            zip_file_downloaded = True
        except Exception as e:
            self.logger.error(f'Failed to download {base_team_name}: {e}')
            return False, f'Failed to download {base_team_name}: {e}'


        if not zip_file_downloaded:
            self.logger.info(f'Downloading base team from storage')
            return False, 'Failed to download base team from storage'

        if zip_file_downloaded:
            self.logger.debug(f'Unzip base team {base_team_name}')
            Tools.unzip_file(base_team_zip_path, base_teams_dir)
            os.remove(base_team_zip_path)

        if os.path.exists(os.path.join(base_team_path)):
            self.logger.debug(f'Setting permissions for base team {base_team_name}')
            Tools.set_permissions_recursive(base_team_path, 0o777)

        self.logger.debug(f'Check base team {base_team_name} start.sh')
        if not os.path.exists(os.path.join(base_team_path, 'start.sh')):
            self.logger.error(f'Base team {base_team_name} start.sh not found')
            Tools.remove_dir(base_team_path)
            return False, f'Base team {base_team_name} start.sh not found'

        return True, "Base team updated successfully"
    
    async def update_base_url(
            self, 
            base_team_name: str,
            download_url:str
        ):
        self.logger.info(f'GameRunnerManager update_base: {base_team_name}, github')


        base_teams_dir = os.path.join(self.data_dir, DataDir.base_team_dir_name)
        base_team_path = os.path.join(base_teams_dir, base_team_name)
        self.logger.debug(f'Check base team {base_team_name}, path: {base_team_path}, dir: {base_teams_dir}')


        #  -- check if base team already exists
        if os.path.exists(base_team_path) and \
            not os.path.exists(os.path.join(base_team_path, 'start.sh')):
            
            self.logger.debug(f'Base team {base_team_name} already exists')
            self.logger.error(f'Base team {base_team_name} start.sh not found')
            Tools.remove_dir(base_team_path)
                

        #  -- check if base team dir is not a file
        if os.path.isfile(base_teams_dir):
            self.logger.error(f'Base teams dir {base_teams_dir} is a file')
            Tools.remove_dir(base_teams_dir)



        #  -- create base team dir if not exists
        if not os.path.exists(base_teams_dir):
            self.logger.info(f'Creating base teams directory: {base_teams_dir}')
            os.makedirs(base_teams_dir, exist_ok=True)

        
        base_team_zip_path = os.path.join(base_teams_dir, f'{base_team_name}.zip')
        zip_file_downloaded = False

        self.logger.debug(f'Downloading base team {base_team_name} from url')
        try:
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(base_team_zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                zip_file_downloaded = True
        except Exception as e:
            self.logger.error(f'Failed to download {base_team_name}: {e}')
            return False, f'Failed to download {base_team_name}: {e}'


        if not zip_file_downloaded:
            self.logger.info(f'Downloading base team from url')
            return False, 'Failed to download base team from url'

        if zip_file_downloaded:
            self.logger.debug(f'Unzip base team {base_team_name}')
            Tools.unzip_file(base_team_zip_path, base_teams_dir)
            os.remove(base_team_zip_path)

        if os.path.exists(os.path.join(base_team_path)):
            self.logger.debug(f'Setting permissions for base team {base_team_name}')
            Tools.set_permissions_recursive(base_team_path, 0o777)

        self.logger.debug(f'Check base team {base_team_name} start.sh')
        if not os.path.exists(os.path.join(base_team_path, 'start.sh')):
            self.logger.error(f'Base team {base_team_name} start.sh not found')
            Tools.remove_dir(base_team_path)
            return False, f'Base team {base_team_name} start.sh not found'

        return True, "Base team updated successfully"
