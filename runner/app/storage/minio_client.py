from minio import Minio
from minio.error import S3Error
from storage.storage_client import StorageClient
import logging


class MinioClient(StorageClient):
    def __init__(self, endpoint, access_key, secret_key, secure=True, server_bucket_name="server",
                 base_team_bucket_name="baseteam", team_config_bucket_name="teamconfig",
                 game_log_bucket_name="gamelog"):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.server_bucket_name = server_bucket_name
        self.base_team_bucket_name = base_team_bucket_name
        self.team_config_bucket_name = team_config_bucket_name
        self.game_log_bucket_name = game_log_bucket_name

    def upload_file(self, bucket_name, file_path, object_name):
        try:
            self.client.fput_object(bucket_name, object_name, file_path)
            logging.info(f"'{file_path}' is successfully uploaded as '{object_name}' in '{bucket_name}' bucket.")
        except S3Error as e:
            logging.error(f"Error occurred: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            logging.info(f"'{object_name}' is successfully downloaded to '{file_path}' from '{bucket_name}' bucket.")
            return True
        except S3Error as e:
            logging.error(f"Error occurred: {e}")
            return False

    def check_connection(self):
        try:
            self.client.list_buckets()
            return True
        except S3Error as e:
            logging.error(f"Error occurred: {e}")
            return False

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
