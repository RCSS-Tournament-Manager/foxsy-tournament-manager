import logging
import logging.config
from utils.logging_config import get_logging_config
import os
import argparse
from managers.tournament_manager import TournamentManager
from fast_api_app import FastApiApp
import asyncio
import signal
from managers.database_manager import DatabaseManager
from utils.rmq_message_sender import RmqMessageSender
from storage.minio_client import MinioClient
from managers.scheduler import Scheduler
from managers.run_game_sender import run_game_sender_by_manager


logging.warning("This is a warning message")

def get_args():
    parser = argparse.ArgumentParser(description='RoboCup Soccer Simulation 2D Tournament Manager app')
    parser.add_argument('--data-dir', type=str, default='../data', help='Directory to store data files')
    parser.add_argument('--log-dir', type=str, default='../data/logs', help='Directory to store log files')
    parser.add_argument("--tmp-game-log-dir", type=str, default="../data/game_logs", help="Directory to store temporary game log files")
    parser.add_argument('--db', default='example.db', help='Database file name')
    parser.add_argument("--api-key", type=str, default="api-key", help="API key for authentication")
    parser.add_argument("--fast-api-port", type=int, default=8085, help="Port to run FastAPI app")
    parser.add_argument("--rabbitmq-use", type=bool, default=True, help="Use RabbitMQ")
    parser.add_argument("--rabbitmq-host", type=str, default="localhost", help="RabbitMQ host")
    parser.add_argument("--rabbitmq-port", type=int, default=5672, help="RabbitMQ port")
    parser.add_argument("--rabbitmq-username", type=str, default="guest", help="RabbitMQ username")
    parser.add_argument("--rabbitmq-password", type=str, default="guest1234", help="RabbitMQ password")
    parser.add_argument("--to-runner-queue", type=str, default="to_runner", help="To runner queue name")
    parser.add_argument("--minio-use", type=bool, default=True, help="Use Minio")
    parser.add_argument("--minio-endpoint", type=str, default="localhost:9000", help="Minio endpoint")
    parser.add_argument("--minio-access-key", type=str, default="guest", help="Minio access key")
    parser.add_argument("--minio-secret-key", type=str, default="guest1234", help="Minio secret key")
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

logging.info(args)

os.makedirs(log_dir, exist_ok=True)
logging.config.dictConfig(get_logging_config(log_dir))

logging.info('Tournament Manager started')
logging.debug(f'args: {args}')


async def main():
    database_path = os.path.abspath(os.path.join(args.data_dir, args.db))
    logging.info(f'{database_path=}')

    database_manager = DatabaseManager('sqlite+aiosqlite:///{}'.format(f'{database_path}'))
    await database_manager.init_db()  # Initialize the database (create tables)

    # Initialize MinioClient
    minio_client = None
    if args.minio_use:
        minio_client = MinioClient(
            endpoint_url=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            secure=False,  # Set to True if using HTTPS
            server_bucket_name=args.server_bucket_name,
            base_team_bucket_name=args.base_team_bucket_name,
            team_config_bucket_name=args.team_config_bucket_name,
            game_log_bucket_name=args.game_log_bucket_name
        )
        await minio_client.init()
        await minio_client.wait_to_connect()
        await minio_client.create_buckets()
        
    if args.rabbitmq_use:
        rmq_message_sender = RmqMessageSender(args.rabbitmq_host, args.rabbitmq_port, args.to_runner_queue,
                                            args.rabbitmq_username,
                                            args.rabbitmq_password)
        await rmq_message_sender.connect()

    async def run_fastapi():
        logging.info('Starting FastAPI app')
        fast_api_app = FastApiApp(database_manager, minio_client, api_key, api_key_name, args.fast_api_port)
        fast_api_app.game_log_tmp_path = args.tmp_game_log_dir
        await fast_api_app.run()

    async def running_game_sender():
        # Initialize and start the scheduler
        if not args.rabbitmq_use:
            logging.error("RabbitMQ is not used. Exiting...")
            return
        scheduler = Scheduler(
            interval=10,  # Run every 10 seconds
            function=run_game_sender_by_manager,
            rabbitmq_manager=rmq_message_sender,
            db_manager=database_manager
        )
        scheduler.run()

    async def run_smart_contract():
        pass
        # await tournament_manager.run_smart_contract()

    async def shutdown(signal, loop):
        logging.info(f"Received exit signal {signal.name}...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        [task.cancel() for task in tasks]

        logging.info("Cancelling outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()

    loop = asyncio.get_running_loop()

    signals = (signal.SIGINT, signal.SIGTERM)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop)))

    try:
        await asyncio.gather(run_fastapi(), running_game_sender())
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        loop.close()
        logging.info("Successfully shut down the application.")

if __name__ == "__main__":
    asyncio.run(main())

