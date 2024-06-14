import asyncio
from typing import Union
from game_runner.game import Game
import logging
import os
from storage.storage_client import StorageClient
from data_dir import DataDir
from utils.messages import *


class Manager:
    def __init__(self, data_dir: str, storage_client: StorageClient):
        logging.info('GameRunnerManager created')
        self.available_games_count = 0
        self.available_ports = []
        self.games: dict[int, Game] = {}
        self.data_dir = data_dir
        self.storage_client = storage_client
        self.check_server()
        self.lock = asyncio.Lock()

    def check_server(self):
        server_dir = os.path.join(self.data_dir, DataDir.server_dir_name)
        server_path = os.path.join(server_dir, 'rcssserver')
        if not os.path.exists(server_dir) or not os.path.exists(server_path):
            if not os.path.exists(server_dir):
                os.makedirs(server_dir)
            if self.storage_client.check_connection():
                self.storage_client.download_file(self.storage_client.server_bucket_name, 'rcssserver', server_path)
            else:
                logging.error(f'Storage connection error, server not found')
                raise FileNotFoundError(f'Server not found')

    def set_available_games_count(self, max_games_count):
        logging.info(f'GameRunnerManager set_available_games_count: {max_games_count}')
        self.available_games_count = max_games_count
        self.available_ports = list(range(6000, 6000 + 10 * max_games_count, 10))
        logging.info(f'GameRunnerManager available_ports: {self.available_ports}')

    def get_available_port(self):
        if self.available_games_count == 0:
            return None
        port = self.available_ports.pop()
        logging.info(f'GameRunnerManager get_available_port: {port}')
        return port

    def free_port(self, port):
        logging.info(f'GameRunnerManager free_port: {port}')
        self.available_games_count += 1
        self.available_ports.append(port)

    async def add_game(self, game_info: GameInfoMessage):
        async with self.lock:
            if self.available_games_count == 0:
                return AddGameResponse(game_id=game_info.game_id, status='failed',
                                       success=False, error='No available games')
            logging.info(f'GameRunnerManager add_game: {game_info}')
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
            return AddGameResponse(game_id=game_info.game_id, status='starting', success=True)

    async def on_finished_game(self, game: Game):
        async with self.lock:
            logging.error(f'GameRunnerManager on_finished_game: Game{game.game_info.game_id}')
            self.free_port(game.port)
            del self.games[game.port]

    def get_games(self):
        logging.info(f'GameRunnerManager get_games')
        res: GetGamesResponse = GetGamesResponse(games=[])
        for game in self.games.values():
            res.games.append(game.to_summary())
        return res

    async def stop_game_by_port(self, port: int):
        logging.info(f'GameRunnerManager stop_game_by_port: {port}')
        game = self.games.get(port)
        res: StopGameResponse = StopGameResponse(game_port=port, success=False)
        if game is None:
            logging.error(f'GameRunnerManager stop_game_by_port[{port}]: game not found')
            res.error = 'Game not found'
            return res
        res.game_id = game.game_info.game_id
        try:
            await game.stop()
        except Exception as e:
            logging.error(f'GameRunnerManager stop_game_by_port[{port}]: {e}')
            res.error = str(e)
            return res
        res.success = True
        return res

    def get_game_by_game_id(self, game_id: int):
        logging.info(f'GameRunnerManager get_game_by_game_id: {game_id}')
        for port, game in self.games.items():
            if game.game_info.game_id == game_id:
                return game
        return None

    async def stop_game_by_game_id(self, game_id: int):
        logging.info(f'GameRunnerManager stop_game_by_game_id: {game_id}')
        game = self.get_game_by_game_id(game_id)
        res: StopGameResponse = StopGameResponse(game_id=game_id, success=False)
        if game is None:
            logging.error(f'GameRunnerManager stop_game_by_game_id[{game_id}]: game not found')
            res.error = 'Game not found'
            return res
        res.game_port = game.port
        try:
            await game.stop()
        except Exception as e:
            logging.error(f'GameRunnerManager stop_game_by_game_id[{game_id}]: {e}')
            res.error = str(e)
            return res
        res.success = True
        return res

    async def handle_message(self, message_json: dict):
        message_type = message_json["type"]
        if message_type == "add_game":
            message = AddGameMessage(**message_json)
            return await self.add_game(message.game_info)
        elif message_type == "stop_game":
            message = StopGameMessage(**message_json)
            return await self.stop_game_by_game_id(message.game_id)
        elif message_type == "get_games":
            GetGamesMessage(**message_json)
            return self.get_games()
        else:
            raise ValueError(f"Invalid message type: {message_type}")
