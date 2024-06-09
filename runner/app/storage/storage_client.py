from abc import ABC, abstractmethod


class StorageClient(ABC):
    @abstractmethod
    def upload_file(self, bucket_name, file_path, object_name):
        pass

    @abstractmethod
    def download_file(self, bucket_name, object_name, file_path):
        pass

    @abstractmethod
    def check_connection(self):
        pass