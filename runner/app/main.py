import time
import logging
import logging.config
from utils.logging_config import get_logging_config
from game_runner.manager import Manager
from game_runner.game import GameInfo
import os
from fast_api_app import FastApiApp

log_dir = '../data/logs'
os.makedirs(log_dir, exist_ok=True)
logging.config.dictConfig(get_logging_config(log_dir))

game_runner_manager = Manager('../data')
game_runner_manager.set_available_games_count(2)
fast_api_app = FastApiApp(game_runner_manager)

#
# game_info1 = GameInfo.from_json(
#     {
#         'game_id': 1,
#         'left_team_name': 'team1',
#         'right_team_name': 'team2',
#         'left_team_config_id': 1,
#         'right_team_config_id': 2,
#         'left_base_team_name': 'helios',
#         'right_base_team_name': 'hermes',
#         'server_config': ''
#     }
# )
#
# game_info2 = GameInfo.from_json(
#     {
#         'game_id': 2,
#         'left_team_name': 'team3',
#         'right_team_name': 'team4',
#         'left_team_config_id': 3,
#         'right_team_config_id': 4,
#         'left_base_team_name': 'helios',
#         'right_base_team_name': 'hermes',
#         'server_config': ''
#     }
# )

# game_runner_manager.add_game(game_info1)
# game_runner_manager.add_game(game_info2)
#

fast_api_app.run()