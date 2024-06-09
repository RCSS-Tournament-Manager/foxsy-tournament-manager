import json
import time
import pika
from threading import Thread, Event

class RabbitMQConsumer:
    def __init__(self, manager, rabbitmq_ip, rabbitmq_port, shared_queue='games', specific_queue=None):
        self.manager = manager
        self.rabbitmq_ip = rabbitmq_ip
        self.rabbitmq_port = rabbitmq_port
        self.shared_queue = shared_queue
        self.specific_queue = specific_queue
        self.stop_event = Event()
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_ip, port=self.rabbitmq_port))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.shared_queue)
                self.channel.queue_declare(queue=self.specific_queue)
                break
            except pika.exceptions.AMQPConnectionError:
                print("Failed to connect to RabbitMQ, retrying in 5 seconds...")
                time.sleep(5)

    def consume_shared_queue(self):
        def callback(ch, method, properties, body):
            message = json.loads(body)
            if self.manager.available_games_count > 0 and message['action'] == 'add_game':
                self.manager.add_game(message['game_info'])
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        while not self.stop_event.is_set():
            try:
                self.channel.basic_consume(queue=self.shared_queue, on_message_callback=callback, auto_ack=False)
                self.channel.start_consuming()
            except pika.exceptions.StreamLostError:
                print("Lost connection to RabbitMQ, reconnecting...")
                self.connect()

    def consume_specific_queue(self):
        def callback(ch, method, properties, body):
            message = json.loads(body)
            if message['action'] == 'stop_game_by_game_id':
                self.manager.stop_game_by_game_id(message['game_id'])
            elif message['action'] == 'stop_game_by_port':
                self.manager.stop_game_by_port(message['port'])
            ch.basic_ack(delivery_tag=method.delivery_tag)

        while not self.stop_event.is_set():
            try:
                self.channel.basic_consume(queue=self.specific_queue, on_message_callback=callback, auto_ack=False)
                self.channel.start_consuming()
            except pika.exceptions.StreamLostError:
                print("Lost connection to RabbitMQ, reconnecting...")
                self.connect()

    def start_consuming(self):
        self.shared_thread = Thread(target=self.consume_shared_queue)
        self.shared_thread.start()
        self.specific_thread = Thread(target=self.consume_specific_queue)
        self.specific_thread.start()
        while not self.stop_event.is_set():
            time.sleep(1)

    def stop_consuming(self):
        self.stop_event.set()
        self.shared_thread.join()
        self.specific_thread.join()
        if self.connection:
            self.connection.close()