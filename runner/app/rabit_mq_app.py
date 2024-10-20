import asyncio
import json
import aio_pika as pika
import logging
from utils.messages import *
import traceback
from game_runner.runner_manager import RunnerManager


logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
class RabbitMQConsumer:
    def __init__(self, manager, rabbitmq_ip, rabbitmq_port, shared_queue, username, password):
        self.logger = logging.getLogger(__name__)
        self.manager: RunnerManager = manager
        self.rabbitmq_ip = rabbitmq_ip
        self.rabbitmq_port = rabbitmq_port
        self.shared_queue_name = shared_queue
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.shared_queue = None
        self.message_queue = asyncio.Queue()
        self.requested_command: RunnerCommandMessageEnum = None
        self.paused = False
        self.update = False

    async def connect(self):
        while True:
            try:
                # credentials = pika.PlainCredentials(self.username, self.password)
                # parameters = pika.ConnectionParameters(host=self.rabbitmq_ip,
                #                                        port=self.rabbitmq_port,
                #                                        credentials=credentials)
                self.connection = await pika.connect_robust(f'amqp://{self.username}:{self.password}@{self.rabbitmq_ip}:{self.rabbitmq_port}')
                self.channel = await self.connection.channel()
                self.shared_queue = await self.channel.declare_queue(self.shared_queue_name)
                break
            except pika.exceptions.AMQPConnectionError:
                self.logger.error("Failed to connect to RabbitMQ, retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def consume_shared_queue(self, message: pika.abc.AbstractIncomingMessage):
        await self.message_queue.put(message)

    async def check_requested_command(self):
        if self.manager.requested_command is None:
            self.logger.debug("No command requested")
            return
        self.requested_command = self.manager.requested_command
        self.logger.info(f"Requested command: {self.requested_command}")
        self.manager.requested_command = None
        if self.requested_command == RunnerCommandMessageEnum.STOP:
            self.logger.info("Received STOP command. Stopping...")
        elif self.requested_command == RunnerCommandMessageEnum.PAUSE:
            self.logger.info("Received PAUSE command. Pausing...")
        elif self.requested_command == RunnerCommandMessageEnum.UPDATE:
            self.logger.info("Received UPDATE command. Updating...")
            # await asyncio.sleep(10)
        elif self.requested_command == RunnerCommandMessageEnum.RESUME:
            self.logger.info("Received RESUME command. Resuming...")
            self.paused = False
            self.update = False

    async def process_messages(self):
        try:
            while self.requested_command != RunnerCommandMessageEnum.STOP:
                await self.check_requested_command()
                if self.paused or self.update or self.requested_command == RunnerCommandMessageEnum.PAUSE or self.requested_command == RunnerCommandMessageEnum.UPDATE:
                    self.logger.debug("Paused. Waiting for 1 second..." if self.paused else "Update in progress. Waiting for 1 second...")
                    if self.requested_command == RunnerCommandMessageEnum.PAUSE:
                        self.logger.info("Pause requested. Pausing...")
                        self.requested_command = None
                        await self.manager.update_status_to(RunnerStatusMessageEnum.PAUSED)
                        self.update = False
                        self.paused = True
                    elif self.requested_command == RunnerCommandMessageEnum.UPDATE:
                        self.logger.info("Update requested. Updating...")
                        self.requested_command = None
                        await self.manager.update_status_to(RunnerStatusMessageEnum.UPDATING)
                        self.paused = False
                        self.update = True
                    await asyncio.sleep(1)
                    continue
                if self.requested_command == RunnerCommandMessageEnum.RESUME:
                    self.logger.info("Resuming...")
                    self.requested_command = None
                    await self.manager.update_status_to(RunnerStatusMessageEnum.RUNNING)
                try:
                    message = await self.message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    self.logger.debug("No messages in queue. Waiting for 1 second...")
                    await asyncio.sleep(1)
                    continue

                async with message.process(ignore_processed=True):
                    self.logger.debug(f"Received message: {message.body}")
                    try:
                        message_body = message.body
                        message_body_decoded = message_body.decode()
                        message_body_decoded = message_body_decoded.replace("'", '"')
                        message_body_decoded = message_body_decoded.replace(' ', '')
                        message_body_decoded = message_body_decoded.replace('\r\n', '')
                        data = json.loads(message_body_decoded)
                        data = dict(data)
                    except Exception as e:
                        self.logger.error(f"Failed to parse message: {e}")
                        await message.ack()
                        traceback.print_exc()
                        continue
                    self.logger.info(f"Received message: {data}")
                    self.logger.debug(f"Message type: {data.get('type')}")

                    async def handle_error(error, ack=True):
                        self.logger.error(f"Failed to parse message: {error}")
                        if ack:
                            await message.ack()
                        else:
                            await message.nack(requeue=True)
                        self.logger.info("Waiting for 5 seconds before re-consuming...")
                        await asyncio.sleep(5)

                    try:
                        game_info_message = GameInfoMessage(**data)
                        GameInfoMessage.model_validate(game_info_message.model_dump())
                        res: GameStartedMessage = await self.manager.add_game(game_info_message, True)
                    except Exception as e:
                        await handle_error(e)
                        continue

                    if res.success is False:
                        await handle_error(res.error, False)
                    else:
                        await message.ack()
            await self.manager.update_status_to(RunnerStatusMessageEnum.STOPPED)
        except Exception as e:
            self.logger.fatal(f"y Error: {e}")
            traceback.print_exc()

    async def start_consuming(self):
        await self.shared_queue.consume(self.consume_shared_queue)

    async def run(self):
        await self.connect()
        asyncio.create_task(self.start_consuming())
        await self.process_messages()