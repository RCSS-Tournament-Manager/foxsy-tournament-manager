import requests
import logging


class MessageSender:
    def __init__(self, host, port, api_key):
        self.host = host
        self.port = port
        self.api_key = api_key

    async def send_message(self, route, message):
        logging.info(f"Sending message to {route} with message: {message} host: {self.host} port: {self.port} api_key: {self.api_key}")
        response = requests.post(
            #f"{self.host}:{self.port}/{route}",
            f"http://{self.host}:{self.port}/{route}",
            headers={"api-key": f"{self.api_key}"},
            json=message,
        )
        logging.info(f"Response: {response.status_code}")
        return response
