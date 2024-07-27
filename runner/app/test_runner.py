from game_runner.runner_manager import RunnerManager
from game_runner.game import GameInfo
import time

game_runner_manager = RunnerManager('../data')

game_info1 = GameInfo.from_json(
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

game_info2 = GameInfo.from_json(
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

game_runner_manager.add_game(game_info1)
game_runner_manager.add_game(game_info2)

while True:
    time.sleep(1)
    print(game_runner_manager.get_games())
