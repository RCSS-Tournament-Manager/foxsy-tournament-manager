import asyncio
import json
import aio_pika as pika
import logging

class RabbitMQConsumer:
    def __init__(self, manager, rabbitmq_ip, rabbitmq_port, shared_queue):
        self.manager = manager
        self.rabbitmq_ip = rabbitmq_ip
        self.rabbitmq_port = rabbitmq_port
        self.shared_queue_name = shared_queue
        self.connection = None
        self.channel = None
        self.shared_queue = None
        self.message_queue = asyncio.Queue()

    async def connect(self):
        while True:
            try:
                self.connection = await pika.connect_robust(f'amqp://{self.rabbitmq_ip}:{self.rabbitmq_port}')
                self.channel = await self.connection.channel()
                self.shared_queue = await self.channel.declare_queue(self.shared_queue_name)
                break
            except pika.exceptions.AMQPConnectionError:
                logging.error("Failed to connect to RabbitMQ, retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def consume_shared_queue(self, message: pika.abc.AbstractIncomingMessage):
        await self.message_queue.put(message)

    async def process_messages(self):
        while True:
            message = await self.message_queue.get()
            async with message.process(ignore_processed=True):
                data = json.loads(message.body.decode())
                logging.debug(f"Received message: {data}")
                if self.manager.available_games_count > 0 and data['action'] == 'add_game':
                    logging.info(f"Adding game: {data['game_info']}")
                    await self.manager.add_game(json.loads(data['game_info']))
                    # TODO: Check output of add game and send response back to the sender
                    await message.ack()
                else:
                    await message.nack(requeue=True)
                    logging.info("Waiting for 5 seconds before re-consuming...")
                    await asyncio.sleep(5)

    async def start_consuming(self):
        await self.shared_queue.consume(self.consume_shared_queue)

    async def run(self):
        await self.connect()
        asyncio.create_task(self.start_consuming())
        await self.process_messages()