import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.settings = {}

    def load_config(self, args, config_file):
        """
        Load configuration from default, file, and command-line arguments.

        Args:
            args: Parsed command-line arguments
            config_file: Path to the YAML config file

        Returns:
            Dict containing the merged configuration
        """
        # Default configuration
        default_config = {
            "config": {
                "update_base_teams_at_startup": True,
                "data_dir": "../data",
                "log_dir": "../data/logs",
                "api_key": "api-key",
                "max_games_count": 2,
                "use_fast_api": True,
                "fast_api_ip": "127.0.0.1",
                "fast_api_port": 8082,
                "use_rabbitmq": True,
                "rabbitmq_host": "localhost",
                "rabbitmq_port": 5672,
                "rabbitmq_username": "guest",
                "rabbitmq_password": "guest1234",
                "to_runner_queue": "to_runner",
                "connect_to_tournament_manager": True,
                "tournament_manager_ip": "localhost",
                "tournament_manager_port": 8085,
                "tournament_manager_api_key": "api-key",
                "use_minio": True,
                "minio_endpoint": "localhost:9000",
                "minio_access_key": "guest",
                "minio_secret_key": "guest1234",
                "server_bucket_name": "server",
                "base_team_bucket_name": "baseteam",
                "team_config_bucket_name": "teamconfig",
                "game_log_bucket_name": "gamelog",
                "default_param": "runner",
            },
            "base_teams": [
                {
                    "name": "cyrus",
                    "force_pull": True,
                    "download": [
                        {
                            "type": "url",
                            "url": "https://github.com/Cyrus2D/FoxsyCyrus2DBase/releases/latest/download/cyrus.zip",
                        },
                        {
                            "type": "minio",
                            "bucket": "baseteam",
                            "object": "cyrus.zip",
                        }
                    ],
                }
            ],
        }

        # Load config from file
        file_config = self._load_yaml_config(config_file) if config_file else {}

        # Convert args to dict and remove None values
        args_dict = {k: v for k, v in vars(args).items() if v is not None}

        # Merge configurations
        merged_config = default_config.copy()
        merged_config["config"].update(file_config.get("config", {}))
        merged_config["config"].update(args_dict)
        merged_config["base_teams"] = file_config.get("base_teams", merged_config["base_teams"])

        self.settings = merged_config
        return merged_config

    def _load_yaml_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.

        Args:
            config_file: Path to the YAML config file

        Returns:
            Dict containing the configuration from the YAML file
        """
        if not config_file.endswith(".yml"):
            raise ValueError("Config file must be a .yml file")

        if not os.path.exists(config_file):
            logger.warning(f"Config file {config_file} does not exist. Using default configuration.")
            return {}

        with open(config_file, "r") as file:
            return yaml.safe_load(file)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key to retrieve
            default: The default value to return if the key is not found

        Returns:
            The configuration value for the given key
        """
        return self.settings.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access to configuration values.

        Args:
            key: The configuration key to retrieve

        Returns:
            The configuration value for the given key
        """
        return self.settings[key]

# Global configuration instance
config = Config()

def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        The global Config instance
    """
    return config