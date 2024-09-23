import asyncio
import aio_pika as pika
import json
import logging

class RmqMessageSender:
    def __init__(self, host: str, port: int, queue_name: str, username: str, password: str):
        self.logger = logging.getLogger(__name__)
        self.logger.info('RmqMessageSender created')
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.shared_queue = None

    async def connect(self):
        while True:
            try:
                self.logger.info(f'Connecting to RabbitMQ: {self.host}:{self.port}')
                self.connection = await pika.connect_robust(f'amqp://{self.username}:{self.password}@{self.host}:{self.port}')
                self.channel = await self.connection.channel()
                self.shared_queue = await self.channel.declare_queue(self.queue_name)
                self.logger.info('Connected to RabbitMQ')
                break
            except pika.exceptions.AMQPConnectionError:
                self.logger.error('Failed to connect to RabbitMQ. Retrying...')
                await asyncio.sleep(5)

    async def publish_message(self, message: dict):
        message_json = json.dumps(message)
        await self.channel.default_exchange.publish(
            pika.Message(body=message_json.encode(), delivery_mode=pika.DeliveryMode.PERSISTENT),
            routing_key=self.queue_name
        )
        self.logger.info(f"Sent message: {message_json}")

    async def close(self):
        self.logger.info('Closing RabbitMQ connection')
        await self.connection.close()