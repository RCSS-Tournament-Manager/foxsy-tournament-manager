import requests
import logging


class MessageSender:
    def __init__(self, host, port, api_key):
        self.host = host
        self.port = port
        self.api_key = api_key

    async def send_message(self, route, message):
        logging.info(f"Sending message to {route} with message: {message}")
        response = requests.post(
            f"{self.host}:{self.port}/{route}",
            headers={"Authorization": f"{self.api_key}"},
            json={"message": message},
        )
        logging.info(f"Response: {response.status_code}")
