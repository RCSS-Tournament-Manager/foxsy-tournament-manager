from abc import ABC, abstractmethod


class StorageClient(ABC):
    def __init__(self, server_bucket_name, base_team_bucket_name, team_config_bucket_name, game_log_bucket_name):
        self.server_bucket_name = server_bucket_name
        self.base_team_bucket_name = base_team_bucket_name
        self.team_config_bucket_name = team_config_bucket_name
        self.game_log_bucket_name = game_log_bucket_name
    @abstractmethod
    def upload_file(self, bucket_name, file_path, object_name):
        pass

    @abstractmethod
    def download_file(self, bucket_name, object_name, file_path):
        pass

    @abstractmethod
    def check_connection(self):
        pass