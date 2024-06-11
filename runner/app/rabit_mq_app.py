import asyncio
import json
import aio_pika as pika

class RabbitMQConsumer:
    def __init__(self, manager, rabbitmq_ip, rabbitmq_port, shared_queue='games', specific_queue=None):
        self.manager = manager
        self.rabbitmq_ip = rabbitmq_ip
        self.rabbitmq_port = rabbitmq_port
        self.shared_queue_name = shared_queue
        self.specific_queue_name = specific_queue
        # self.stop_event = Event()
        self.connection = None
        self.channel = None
        self.shared_queue = None
        self.specific_queue = None

    async def connect(self):
        while True:
            try:
                self.connection = await pika.connect_robust(f'amqp://{self.rabbitmq_ip}:{self.rabbitmq_port}')
                self.channel = await self.connection.channel()
                self.shared_queue = await self.channel.declare_queue(self.shared_queue_name) # TODO CHECK AUTO ACK?
                self.specific_queue = await self.channel.declare_queue(self.specific_queue_name)
                break
            except pika.exceptions.AMQPConnectionError:
                print("Failed to connect to RabbitMQ, retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def consume_shared_queue(self, message: pika.abc.AbstractIncomingMessage):
        async with message.process(ignore_processed=True):
            data = json.loads(message.body.decode())
            if self.manager.available_games_count > 0 and data['action'] == 'add_game':
                await self.manager.add_game(json.loads(data['game_info']))
                await message.ack()
            else:
                await message.nack(requeue=True)

    async def consume_specific_queue(self, message: pika.abc.AbstractIncomingMessage):
        async with message.process(ignore_processed=True):
            data = json.loads(message.body.decode())
            if data['action'] == 'stop_game_by_game_id':
                self.manager.stop_game_by_game_id(data['game_id'])
            elif data['action'] == 'stop_game_by_port':
                self.manager.stop_game_by_port(data['port'])
            await message.ack()
        

    async def start_consuming(self):
        consumers_tasks = [
            asyncio.create_task(self.shared_queue.consume(self.consume_shared_queue)),
            asyncio.create_task(self.specific_queue.consume(self.consume_specific_queue))
        ]
        await asyncio.gather(*consumers_tasks)
        while True:
            await asyncio.sleep(1)

    def stop_consuming(self):
        # self.stop_event.set()
        self.shared_thread.join()
        self.specific_thread.join()
        if self.connection:
            self.connection.close()