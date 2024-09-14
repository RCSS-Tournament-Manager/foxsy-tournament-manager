# managers/minio_client.py

import aiobotocore.session
import asyncio
import logging
from botocore.exceptions import ClientError, EndpointConnectionError
from typing import Optional

class MinioClient:
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
        server_bucket_name: str = None,
        base_team_bucket_name: str = None,
        team_config_bucket_name: str = None,
        game_log_bucket_name: str = None
    ):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.session = None
        self.client = None

        # Buckets
        self.server_bucket_name = server_bucket_name
        self.base_team_bucket_name = base_team_bucket_name
        self.team_config_bucket_name = team_config_bucket_name
        self.game_log_bucket_name = game_log_bucket_name

    async def init(self):
        # Initialize the aiobotocore session
        self.session = aiobotocore.session.get_session()

        # Build the endpoint URL with the correct scheme
        scheme = 'https' if self.secure else 'http'
        endpoint_url = f"{scheme}://{self.endpoint_url}"

        # Create the client
        self.client = await self.session.create_client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ).__aenter__()

    async def close(self):
        if self.client:
            await self.client.__aexit__(None, None, None)

    async def upload_file(self, bucket_name: str, file_path: str, object_name: str):
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            await self.client.put_object(Bucket=bucket_name, Key=object_name, Body=data)
            logging.info(f"'{file_path}' is successfully uploaded as '{object_name}' in '{bucket_name}' bucket.")
        except Exception as e:
            logging.error(f"Error occurred while uploading: {e}")

    async def download_file(self, bucket_name: str, object_name: str, file_path: str):
        try:
            response = await self.client.get_object(Bucket=bucket_name, Key=object_name)
            async with response['Body'] as stream:
                data = await stream.read()
            with open(file_path, 'wb') as f:
                f.write(data)
            logging.info(f"'{object_name}' is successfully downloaded to '{file_path}' from '{bucket_name}' bucket.")
            return True
        except Exception as e:
            logging.error(f"Error occurred while downloading: {e}")
            return False

    async def download_log_file(self, log_file_name: str, file_path: str):
        return await self.download_file(self.game_log_bucket_name, log_file_name, file_path)

    async def check_connection(self) -> bool:
        try:
            await self.client.list_buckets()
            return True
        except EndpointConnectionError as e:
            logging.error(f"Connection error: {e}")
            return False
        except ClientError as e:
            logging.error(f"Client error: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return False

    async def wait_to_connect(self):
        while not await self.check_connection():
            logging.error("Failed to connect to MinIO, retrying in 5 seconds...")
            await asyncio.sleep(5)
        logging.info("Connected to MinIO.")

    async def create_buckets(self):
        buckets = [
            self.server_bucket_name,
            self.base_team_bucket_name,
            self.team_config_bucket_name,
            self.game_log_bucket_name,
        ]
        for bucket_name in buckets:
            if bucket_name:
                await self.create_bucket(bucket_name)

    async def create_bucket(self, bucket_name: str):
        try:
            # Check if bucket exists
            response = await self.client.list_buckets()
            existing_buckets = [b['Name'] for b in response['Buckets']]
            if bucket_name in existing_buckets:
                logging.info(f"Bucket '{bucket_name}' already exists.")
                return
            await self.client.create_bucket(Bucket=bucket_name)
            logging.info(f"Bucket '{bucket_name}' is successfully created.")
        except ClientError as e:
            if e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
                logging.info(f"Bucket '{bucket_name}' already exists.")
            else:
                logging.error(f"Error occurred while creating bucket: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred while creating bucket: {e}")
