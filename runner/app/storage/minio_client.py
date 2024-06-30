from minio import Minio
from minio.error import S3Error
from storage.storage_client import StorageClient
import logging
import time


class MinioClient(StorageClient):
    def __init__(self, server_bucket_name, base_team_bucket_name, team_config_bucket_name, game_log_bucket_name):
        super().__init__(server_bucket_name, base_team_bucket_name, team_config_bucket_name, game_log_bucket_name)
        self.client = None

    def init(self, endpoint, access_key, secret_key, secure=True):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
    def upload_file(self, bucket_name, file_path, object_name):
        try:
            self.client.fput_object(bucket_name, object_name, file_path)
            logging.info(f"'{file_path}' is successfully uploaded as '{object_name}' in '{bucket_name}' bucket.")
        except Exception as e:
            logging.error(f"Error occurred: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        try:
            logging.debug(f"Downloading '{object_name}' from '{bucket_name}' bucket to '{file_path}'")
            self.client.fget_object(bucket_name, object_name, file_path)
            logging.info(f"'{object_name}' is successfully downloaded to '{file_path}' from '{bucket_name}' bucket.")
            return True
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return False

    def check_connection(self):
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return False

    def wait_to_connect(self):
        while not self.check_connection():
            logging.error("Failed to connect to Minio, retrying in 5 seconds...")
            time.sleep(5)

    def create_buckets(self):
        self.create_bucket(self.server_bucket_name)
        self.create_bucket(self.base_team_bucket_name)
        self.create_bucket(self.team_config_bucket_name)
        self.create_bucket(self.game_log_bucket_name)

    def create_bucket(self, bucket_name):
        try:
            self.client.make_bucket(bucket_name)
            logging.info(f"Bucket '{bucket_name}' is successfully created.")
        except S3Error as e:
            if e.code == "BucketAlreadyOwnedByYou":
                logging.info(f"Bucket '{bucket_name}' already exists.")
            else:
                logging.error(f"Error occurred: {e}")

# Example usage:
# if __name__ == "__main__":
#     # Initialize the Minio client
#     minio_client = MinioClient(
#         endpoint="localhost:9000",
#         access_key="minioadmin",
#         secret_key="minioadmin",
#         secure=False
#     )
#
#     # Upload a file
#     minio_client.upload_file(
#         bucket_name="mybucket",
#         file_path="t.txt",
#         object_name="remote_file.txt"
#     )
#
#     # Download a file
#     minio_client.download_file(
#         bucket_name="mybucket",
#         object_name="Screenshot 2024-02-20 200127.png",
#         file_path="./downloads/screenshot.png"
#     )
