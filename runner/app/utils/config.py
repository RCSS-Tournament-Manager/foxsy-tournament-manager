import os
import yaml

import logging

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
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
            "download": {
                "type": "url",
                "url": "https://github.com/Cyrus2D/FoxsyCyrus2DBase/releases/latest/download/cyrus.zip",
            },
        }
    ],
}

SETTINGS = {}

def get_settings(args, config):
    # turn args to dict
    args = vars(args)
    # remove None values
    args = {k: v for k, v in args.items() if v is not None}

    # order of config loading
    # default config
    # config file
    # args

    settings_o = DEFAULT_CONFIG.copy()
    settings_o["config"] = {
        **settings_o["config"],
        **(config["config"] if "config" in config.keys() else {}),
        **args,
    }
    settings_o["base_teams"] = config["base_teams"] if "base_teams" in config.keys() else settings_o["base_teams"]
    global SETTINGS
    SETTINGS = settings_o
    return settings_o


def apply_default_args(argument, config_obj):
    if hasattr(config_obj, argument):
        return getattr(config_obj, argument)
    else:
        raise AttributeError(f"Config object has no attribute '{argument}'")


def get_config_file(args):
    if args.config == None:
        print("no config file")

    if args.config != None and os.path.exists(args.config):

        if not args.config.endswith(".yml"):
            raise ValueError("Config file must be a .yml file")

        with open(args.config, "r") as file:
            config = yaml.safe_load(file)
            return config

    return {}
