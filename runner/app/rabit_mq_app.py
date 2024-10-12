import asyncio
import json
import aio_pika as pika
import logging
from utils.messages import *
import traceback



class RabbitMQConsumer:
    def __init__(self, manager, rabbitmq_ip, rabbitmq_port, shared_queue, username, password):
        self.manager = manager
        self.rabbitmq_ip = rabbitmq_ip
        self.rabbitmq_port = rabbitmq_port
        self.shared_queue_name = shared_queue
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.shared_queue = None
        self.message_queue = asyncio.Queue()

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
                logging.error("Failed to connect to RabbitMQ, retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def consume_shared_queue(self, message: pika.abc.AbstractIncomingMessage):
        await self.message_queue.put(message)

    async def process_messages(self):
        try:
            while True:
                message = await self.message_queue.get()
                async with message.process(ignore_processed=True):
                    logging.debug(f"Received message: {message.body}")
                    try:
                        if self.manager.status.to_RunnerStatusMessageEnum() != RunnerStatusMessageEnum.RUNNING: 
                            logging.info(f"Runner status is {self.manager.status}. Deferring message processing.")
                            await message.nack(requeue=True)
                            self.logger.info("Waiting for 10 seconds before checking Runner status again...")
                            await asyncio.sleep(10) 
                            continue
                        message_body = message.body
                        message_body_decoded = message_body.decode()
                        message_body_decoded = message_body_decoded.replace("'", '"')
                        message_body_decoded = message_body_decoded.replace(' ', '')
                        message_body_decoded = message_body_decoded.replace('\r\n', '')
                        data = json.loads(message_body_decoded)
                        data = dict(data)
                    except Exception as e:
                        logging.error(f"Failed to parse message: {e}")
                        await message.ack()
                        traceback.print_exc()
                        continue
                    logging.info(f"Received message: {data}")
                    logging.debug(f"Message type: {data.get('type')}")

                    async def handle_error(error, ack=True):
                        logging.error(f"Failed to parse message: {error}")
                        if ack:
                            await message.ack()
                        else:
                            await message.nack(requeue=True)
                        logging.info("Waiting for 5 seconds before re-consuming...")
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
        except Exception as e:
            logging.fatal(f"y Error: {e}")
            traceback.print_exc()

    async def start_consuming(self):
        await self.shared_queue.consume(self.consume_shared_queue)

    async def run(self):
        await self.connect()
        asyncio.create_task(self.start_consuming())
        await self.process_messages()