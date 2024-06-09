import logging
import logging.config
from utils.logging_config import get_logging_config
from game_runner.manager import Manager
import os
from fast_api_app import FastApiApp
import argparse
from storage.minio_client import MinioClient
from rabit_mq_app import RabbitMQConsumer


def get_args():
    parser = argparse.ArgumentParser(description="RoboCup Soccer Simulation 2D Game Runner FastAPI app")
    parser.add_argument("--data-dir", type=str, default="../data", help="Directory to store data files")
    parser.add_argument("--log-dir", type=str, default="../data/logs", help="Directory to store log files")
    parser.add_argument("--api-key", type=str, default="api-key", help="API key for authentication")
    parser.add_argument("--max_games_count", type=int, default=2, help="Maximum number of games to run")
    parser.add_argument("--use-fast-api", default=True, action="store_true", help="Use FastAPI app")
    parser.add_argument("--fast-api-port", type=int, default=8082, help="Port to run FastAPI app")
    parser.add_argument("--use-rabbitmq", default=False, action="store_true", help="Use RabbitMQ")
    parser.add_argument("--rabbitmq-host", type=str, default="localhost", help="RabbitMQ host")
    parser.add_argument("--rabbitmq-port", type=int, default=5672, help="RabbitMQ port")
    parser.add_argument("--runner-manager-ip", type=str, default="localhost", help="Runner manager IP address")
    parser.add_argument("--runner-manager-port", type=int, default=5672, help="Runner manager port")
    parser.add_argument("--minio-endpoint", type=str, default="localhost:9000", help="Minio endpoint")
    parser.add_argument("--minio-access-key", type=str, default="minioadmin", help="Minio access key")
    parser.add_argument("--minio-secret-key", type=str, default="minioadmin", help="Minio secret key")
    parser.add_argument("--server-bucket-name", type=str, default="server", help="Server bucket name")
    parser.add_argument("--base-team-bucket-name", type=str, default="baseteam", help="Team bucket name")
    parser.add_argument("--team-config-bucket-name", type=str, default="teamconfig", help="Team config bucket name")
    parser.add_argument("--game-log-bucket-name", type=str, default="gamelog", help="Match bucket name")
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

minio_client = MinioClient(
    endpoint=args.minio_endpoint,
    access_key=args.minio_access_key,
    secret_key=args.minio_secret_key,
    secure=False,
    server_bucket_name=args.server_bucket_name,
    base_team_bucket_name=args.base_team_bucket_name,
    team_config_bucket_name=args.team_config_bucket_name,
    game_log_bucket_name=args.game_log_bucket_name
)

game_runner_manager = Manager(data_dir, minio_client)
game_runner_manager.set_available_games_count(2)

if args.use_fast_api:
    fast_api_app = FastApiApp(game_runner_manager, api_key, api_key_name, args.fast_api_port)
    fast_api_app.run()
elif args.use_rabbitmq:
    rabbitmq_ip = "localhost"  # Replace with your RabbitMQ IP
    rabbitmq_port = 5672  # Replace with your RabbitMQ port
    specific_queue = "specific_queue_name"  # Replace with your specific queue name

    rabbitmq_consumer = RabbitMQConsumer(game_runner_manager, rabbitmq_ip, rabbitmq_port, specific_queue=specific_queue)
    rabbitmq_consumer.start_consuming()