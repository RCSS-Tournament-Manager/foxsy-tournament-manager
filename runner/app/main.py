import time
import logging
import logging.config
from utils.logging_config import get_logging_config
from game_runner.manager import GameRunnerManager
from game_runner.game import GameInfo
import os


log_dir = '../data/logs'
os.makedirs(log_dir, exist_ok=True)
# Configure logging
logging.config.dictConfig(get_logging_config(log_dir))

game_runner_manager = GameRunnerManager()
game_runner_manager.set_available_games_count(2)


game_info1 = GameInfo()
game_info1.from_json(
    {
        'game_id': 1,
        'left_team_name': 'team1',
        'right_team_name': 'team2',
        'left_team_config_id': 1,
        'right_team_config_id': 2,
        'left_base_team_name': 'helios',
        'right_base_team_name': 'hermes',
        'server_config': ''
    }
)

game_info2 = GameInfo()
game_info2.from_json(
    {
        'game_id': 2,
        'left_team_name': 'team3',
        'right_team_name': 'team4',
        'left_team_config_id': 3,
        'right_team_config_id': 4,
        'left_base_team_name': 'helios',
        'right_base_team_name': 'hermes',
        'server_config': ''
    }
)

game_runner_manager.add_game(game_info1, '../data')
game_runner_manager.add_game(game_info2, '../data')

while True:
    time.sleep(1)