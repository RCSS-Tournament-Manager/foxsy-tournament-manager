import asyncio
import logging
import logging.config
from utils.logging_config import get_logging_config
from game_runner.manager import Manager
import os
from fast_api_app import FastApiApp
import argparse
from storage.minio_client import MinioClient
from rabit_mq_app import RabbitMQConsumer
import aio_pika as pika
import signal
from utils.message_sender import MessageSender
from utils.messages import *


pika.logger.setLevel(logging.ERROR)


def get_args():
    parser = argparse.ArgumentParser(description="RoboCup Soccer Simulation 2D Game Runner FastAPI app")
    parser.add_argument("--data-dir", type=str, default="../data", help="Directory to store data files")
    parser.add_argument("--log-dir", type=str, default="../data/logs", help="Directory to store log files")
    parser.add_argument("--api-key", type=str, default="api-key", help="API key for authentication")
    parser.add_argument("--max_games_count", type=int, default=2, help="Maximum number of games to run")
    parser.add_argument("--use-fast-api", default=True, action="store_true", help="Use FastAPI app")
    parser.add_argument("--fast-api-port", type=int, default=8082, help="Port to run FastAPI app")
    parser.add_argument("--use-rabbitmq", default=True, action="store_true", help="Use RabbitMQ")
    parser.add_argument("--rabbitmq-host", type=str, default="localhost", help="RabbitMQ host")
    parser.add_argument("--rabbitmq-port", type=int, default=5672, help="RabbitMQ port")
    parser.add_argument("--to-runner-queue", type=str, default="to_runner", help="To runner queue name")
    parser.add_argument("--to-runner-manager-queue", type=str, default="to_runner_manager", help="To runner manager queue name")
    parser.add_argument("--shared-queue", type=str, default="shared_queue", help="Shared queue name")
    parser.add_argument("--runner-manager-ip", type=str, default="localhost", help="Runner manager IP address")
    parser.add_argument("--runner-manager-port", type=int, default=5672, help="Runner manager port")
    parser.add_argument("--runner-manager-api-key", type=str, default="runner-manager-api-key", help="Runner manager API key")
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
    server_bucket_name=args.server_bucket_name,
    base_team_bucket_name=args.base_team_bucket_name,
    team_config_bucket_name=args.team_config_bucket_name,
    game_log_bucket_name=args.game_log_bucket_name
)

minio_client.init(endpoint=args.minio_endpoint,
                  access_key=args.minio_access_key,
                  secret_key=args.minio_secret_key,
                  secure=False,)

message_sender = MessageSender(args.runner_manager_ip, args.runner_manager_port, args.runner_manager_api_key)
register_resp = message_sender.send_message("register", RegisterMessage(ip="localhost", port=args.fast_api_port,
                                                                        available_games_count=args.max_games_count))


game_runner_manager = Manager(data_dir, minio_client, message_sender)
game_runner_manager.set_available_games_count(2)

async def run_fastapi():
    logging.info('Starting FastAPI app')
    fast_api_app = FastApiApp(game_runner_manager, api_key, api_key_name, args.fast_api_port)
    await fast_api_app.run()

async def run_rmq():
    logging.info('Starting RabbitMQ Consumer')
    rabbitmq_consumer = RabbitMQConsumer(game_runner_manager,
                                         args.rabbitmq_host, args.rabbitmq_port,
                                         args.to_runner_queue)
    await rabbitmq_consumer.run()

async def shutdown(signal, loop):
    logging.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]

    logging.info("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def main():
    loop = asyncio.get_event_loop()

    signals = (signal.SIGINT, signal.SIGTERM)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop)))

    try:
        if args.use_fast_api and args.use_rabbitmq:
            loop.run_until_complete(asyncio.gather(run_fastapi(), run_rmq()))
        elif args.use_fast_api:
            loop.run_until_complete(run_fastapi())
        elif args.use_rabbitmq:
            loop.run_until_complete(run_rmq())
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        loop.close()
        logging.info("Successfully shut down the application.")

if __name__ == "__main__":
    asyncio.run(main())
