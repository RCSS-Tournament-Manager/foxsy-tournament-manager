import asyncio
import logging
import logging.config
import sys
from utils.base_teams import download_base_teams
from utils.config import get_config_file, get_settings
from utils.args_helper import ArgsHelper
from utils.logging_config import get_logging_config
from game_runner.runner_manager import RunnerManager
import os
from fast_api_app import FastApiApp
import argparse
from storage.minio_client import MinioClient
from rabit_mq_app import RabbitMQConsumer
import aio_pika as pika
import signal
from utils.message_sender import MessageSender
from utils.messages import *
import json


pika.logger.setLevel(logging.ERROR)

def get_args():
    parser = argparse.ArgumentParser(description="RoboCup Soccer Simulation 2D Game Runner FastAPI app")
    parser.add_argument("--data-dir", type=str, help="Directory to store data files")
    parser.add_argument("--log-dir", type=str, help="Directory to store log files")
    parser.add_argument("--api-key", type=str, help="API key for authentication")
    parser.add_argument("--max_games_count", type=int, help="Maximum number of games to run")
    parser.add_argument("--use-fast-api", type=ArgsHelper.str_to_bool, help="Use FastAPI app (true/false or 1/0)")
    parser.add_argument("--fast-api-ip", type=str, help="IP to run FastAPI app")
    parser.add_argument("--fast-api-port", type=int, help="Port to run FastAPI app")
    parser.add_argument("--use-rabbitmq", type=ArgsHelper.str_to_bool, help="Use RabbitMQ (true/false or 1/0)")
    parser.add_argument("--rabbitmq-host", type=str, help="RabbitMQ host")
    parser.add_argument("--rabbitmq-port", type=int, help="RabbitMQ port")
    parser.add_argument("--rabbitmq-username", type=str, help="RabbitMQ username")
    parser.add_argument("--rabbitmq-password", type=str, help="RabbitMQ password")
    parser.add_argument("--to-runner-queue", type=str, help="To runner queue name")
    parser.add_argument("--connect-to-tournament-manager", type=ArgsHelper.str_to_bool, help="Connect to Tournament Manager (true/false or 1/0)")
    parser.add_argument("--tournament-manager-ip", type=str, help="Tournament manager IP address")
    parser.add_argument("--tournament-manager-port", type=int, help="Tournament manager port")
    parser.add_argument("--tournament-manager-api-key", type=str, help="Tournament manager API key")
    parser.add_argument("--use-minio", type=ArgsHelper.str_to_bool, help="Use Minio (true/false or 1/0)")
    parser.add_argument("--minio-endpoint", type=str, help="Minio endpoint")
    parser.add_argument("--minio-access-key", type=str, help="Minio access key")
    parser.add_argument("--minio-secret-key", type=str, help="Minio secret key")
    parser.add_argument("--server-bucket-name", type=str, help="Server bucket name")
    parser.add_argument("--base-team-bucket-name", type=str, help="Team bucket name")
    parser.add_argument("--team-config-bucket-name", type=str, help="Team config bucket name")
    parser.add_argument("--game-log-bucket-name", type=str, help="Match bucket name")
    parser.add_argument("--config", type=str, help="default.yml config file", default="default.yml")
    args, unknown = parser.parse_known_args()
    return args

# ---------------------------- DEFAULT CONFIG 
args = get_args()
config = get_config_file(args)
settings = get_settings(args,config)
data_dir = settings['config']['data_dir']
log_dir = settings['config']['log_dir']
api_key = settings['config']['api_key']
api_key_name = "api-key"

# ---------------------------- 
os.makedirs(log_dir, exist_ok=True)
logging.config.dictConfig(get_logging_config(log_dir))

logging.info('GameRunner started')
logging.debug(f'args: {args}')
logging.info(settings)

# ---------------------------- MINIO CLIENT
minio_client = None
if settings['config']['use_minio']:
    minio_client = MinioClient(
        server_bucket_name=settings['config']['server_bucket_name'],
        base_team_bucket_name=settings['config']['base_team_bucket_name'],
        team_config_bucket_name=settings['config']['team_config_bucket_name'],
        game_log_bucket_name=settings['config']['game_log_bucket_name']
    )

    minio_client.init(endpoint=settings['config']['minio_endpoint'],
                      access_key=settings['config']['minio_access_key'],
                      secret_key=settings['config']['minio_secret_key'],
                      secure=False)

    minio_client.wait_to_connect()

    minio_client.create_buckets()



# ---------------------------- MESSAGE SENDER
message_sender = None
if settings['config']['connect_to_tournament_manager']:
    message_sender = MessageSender(
        settings['config']['tournament_manager_ip'], 
        settings['config']['tournament_manager_port'], 
        settings['config']['tournament_manager_api_key']
    )
runner_id = None

async def send_register_message():
    global runner_id
    while settings['config']['connect_to_tournament_manager']:
        try:
            register_resp = await message_sender.send_message(
                "from_runner/register",
                RegisterGameRunnerRequest(
                    ip=settings['config']['fast_api_ip'],
                    port=settings['config']['fast_api_port'],
                    available_games_count=settings['config']['max_games_count']
                ).model_dump()
            )
            logging.info(f"Register response: {register_resp}")
            register_resp_content = json.loads(register_resp.content.decode('utf-8'))
            register_resp = ResponseMessage(**register_resp_content)
            if register_resp.success:
                runner_id = int(register_resp.value)
                logging.info(f"Registered as runner with id: {runner_id}")
            break
        except Exception as e:
            logging.error(f"Failed to send register message: {e}")
            await asyncio.sleep(5)


async def main():
    global runner_id
    await send_register_message()

    game_runner_manager = RunnerManager(
        data_dir=data_dir, 
        storage_client=minio_client, 
        message_sender=message_sender, 
        runner_id=runner_id,
        config=settings
    )


    # ---------------------------- DOWNLOAD BASE TEAMS
    try:
        await download_base_teams(game_runner_manager, settings)
    except Exception as e:
        logging.error(f"Failed to download base teams: {e}")
                

    game_runner_manager.set_available_games_count(2)

    # download base teams by default

    async def run_fastapi():
        logging.info('Starting FastAPI app')
        fast_api_app = FastApiApp(game_runner_manager, api_key, api_key_name, settings['config']['fast_api_port'])
        await fast_api_app.run()

    async def run_rmq():
        logging.info('Starting RabbitMQ Consumer')
        rabbitmq_consumer = RabbitMQConsumer(
            manager=game_runner_manager,
            rabbitmq_ip=settings['config']['rabbitmq_host'], 
            rabbitmq_port=settings['config']['rabbitmq_port'],
            shared_queue=settings['config']['to_runner_queue'],
            username=settings['config']['rabbitmq_username'], 
            password=settings['config']['rabbitmq_password']
        )
        await rabbitmq_consumer.run()

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
        if settings['config']['use_fast_api'] and settings['config']['use_rabbitmq']:
            await asyncio.gather(run_fastapi(), run_rmq())
        elif settings['config']['use_fast_api']:
            await run_fastapi()
        elif settings['config']['use_rabbitmq']:
            await run_rmq()
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        loop.close()
        logging.info("Successfully shut down the application.")


if __name__ == "__main__":
    asyncio.run(main())
