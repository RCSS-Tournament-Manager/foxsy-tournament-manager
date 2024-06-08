from typing import Union
from game_runner.game import Game, GameInfo
import logging


class Manager:
    def __init__(self, data_dir: str):
        logging.info('GameRunnerManager created')
        self.available_games_count = 0
        self.available_ports = []
        self.games: dict[int, Game] = {}
        self.data_dir = data_dir

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

    def add_game(self, game_info: Union[GameInfo, dict]):
        if isinstance(game_info, dict):
            game_info = GameInfo.from_json(game_info)
        logging.info(f'GameRunnerManager add_game: {game_info}')
        port = self.get_available_port()
        if port is None:
            return None
        self.available_games_count -= 1
        game = Game(game_info, port, self.data_dir)
        game.finished_event = self.on_finished_game
        self.games[port] = game
        self.games[port].run_game()
        return game

    def on_finished_game(self, game: Game):
        logging.error(f'GameRunnerManager on_finished_game: {game}')
        self.free_port(game.port)
        del self.games[game.port]

    def get_games(self):
        logging.info(f'GameRunnerManager get_games')
        res = {}
        for port, game in self.games.items():
            res[port] = game.to_dict()
        return res


