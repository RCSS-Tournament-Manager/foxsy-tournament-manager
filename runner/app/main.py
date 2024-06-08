import logging
import logging.config
from utils.logging_config import get_logging_config
from game_runner.manager import Manager
import os
from fast_api_app import FastApiApp
import argparse


def get_args():
    parser = argparse.ArgumentParser(description="RoboCup Soccer Simulation 2D Game Runner FastAPI app")
    parser.add_argument("--data-dir", type=str, default="../data", help="Directory to store data files")
    parser.add_argument("--log-dir", type=str, default="../data/logs", help="Directory to store log files")
    parser.add_argument("--api-key", type=str, default="secret", help="API key for authentication")
    parser.add_argument("--max_games_count", type=int, default=2, help="Maximum number of games to run")
    parser.add_argument("--use-fast-api", action="store_true", help="Use FastAPI app")
    parser.add_argument("--fast-api-port", type=int, default=8082, help="Port to run FastAPI app")
    parser.add_argument("--use-rabbitmq", action="store_true", help="Use RabbitMQ")
    parser.add_argument("--rabbitmq-host", type=str, default="localhost", help="RabbitMQ host")
    parser.add_argument("--rabbitmq-port", type=int, default=5672, help="RabbitMQ port")
    parser.add_argument("--runner-manager-ip", type=str, default="localhost", help="Runner manager IP address")
    parser.add_argument("--runner-manager-port", type=int, default=5672, help="Runner manager port")
    parser.add_argument("--storage-ip", type=str, default="localhost", help="Storage IP address")
    parser.add_argument("--storage-port", type=int, default=5672, help="Storage port")
    args, unknown = parser.parse_known_args()
    return args


args = get_args()
data_dir = args.data_dir
log_dir = args.log_dir
api_key = args.api_key
api_key_name = "api_key"

os.makedirs(log_dir, exist_ok=True)
logging.config.dictConfig(get_logging_config(log_dir))

logging.info('GameRunner started')
logging.debug(f'args: {args}')

game_runner_manager = Manager(data_dir)
game_runner_manager.set_available_games_count(2)

if args.use_fast_api:
    fast_api_app = FastApiApp(game_runner_manager, api_key, api_key_name, args.fast_api_port)
    fast_api_app.run()