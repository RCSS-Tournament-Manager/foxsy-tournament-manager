import asyncio
from game_runner.game import Game
import logging
import os
from storage.storage_client import StorageClient
from data_dir import DataDir
from utils.messages import *
from utils.message_sender import MessageSender
from storage.downloader import Downloader

class RunnerManager:
    def __init__(self, data_dir: str, storage_client: StorageClient, message_sender: MessageSender):
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

    async def add_game(self, game_info: GameInfoMessage, called_from_rabbitmq: bool = False):
        async with self.lock:
            #TODO try except
            self.logger.info(f'GameRunnerManager adding game: {game_info}')
            if self.available_games_count == 0:
                return AddGameResponse(game_id=game_info.game_id, status='failed',
                                       success=False, error='No available games')
            self.logger.info(f'GameRunnerManager add_game: {game_info}')
            port = self.get_available_port()
            if port is None:
                return AddGameResponse(game_id=game_info.game_id, status='failed',
                                       success=False, error='No available ports')
            self.available_games_count -= 1
            game = Game(game_info, port, self.data_dir, self.storage_client)
            game.finished_event = self.on_finished_game
            self.games[port] = game
            self.games[port].check()
            asyncio.create_task(game.run_game())
            res = AddGameResponse(game_id=game_info.game_id, status='starting', success=True, port=port)
            if called_from_rabbitmq:
                try:
                    await self.message_sender.send_message('game_started', res.dict())
                except Exception as e:
                    self.logger.error(f'GameRunnerManager add_game (Can not send game_started message): {e}')
            return res

    async def on_finished_game(self, game: Game):
        async with self.lock:
            try:
                self.logger.info(f'GameRunnerManager on_finished_game: Game{game.game_info.game_id}')
                self.free_port(game.port)
                await self.message_sender.send_message('game_finished', game.to_summary().dict())
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
