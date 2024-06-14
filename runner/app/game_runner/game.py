import os
import logging
from utils.tools import Tools
import asyncio
from storage.storage_client import StorageClient
from data_dir import DataDir
from subprocess import PIPE
from utils.messages import *



class ServerConfig:
    def __init__(self, config: str, game_info: GameInfoMessage, data_dir: str, port: int, logger):
        self.auto_mode = True
        self.synch_mode = True
        self.game_id = game_info.game_id
        self.left_team_name = game_info.left_team_name
        self.right_team_name = game_info.right_team_name
        self.left_team_start = os.path.join(data_dir, DataDir.base_team_dir_name,
                                            game_info.left_base_team_name, 'start.sh')
        self.right_team_start = os.path.join(data_dir, DataDir.base_team_dir_name,
                                             game_info.right_base_team_name, 'start.sh')
        self.game_log_dir = os.path.join(data_dir, DataDir.game_log_dir_name, f'{self.game_id}')
        self.text_log_dir = os.path.join(self.game_log_dir)
        self.port = port
        self.coach_port = port + 1
        self.online_coach_port = port + 2
        os.makedirs(self.game_log_dir, exist_ok=True)
        self.other_config = config
        self.logger = logger

    def get_config(self):
        auto_mode = 'true' if self.auto_mode else 'false'
        synch_mode = 'true' if self.synch_mode else 'false'
        res = ""
        res += f'--server::auto_mode={auto_mode} '
        res += f'--server::synch_mode={synch_mode} '
        res += f'--server::fixed_teamname_l={self.left_team_name} '
        res += f'--server::fixed_teamname_r={self.right_team_name} '
        res += f"--server::team_l_start=\\'{self.left_team_start} -p {self.port}\\' "
        res += f"--server::team_r_start=\\'{self.right_team_start} -p {self.port}\\' "
        res += f'--server::game_log_dir={self.game_log_dir} '
        res += f'--server::text_log_dir={self.text_log_dir} '
        res += '--server::half_time=100 '
        res += '--server::nr_normal_halfs=2 '
        res += '--server::nr_extra_halfs=0 '
        res += '--server::penalty_shoot_outs=0 '
        res += '--server::port=' + str(self.port) + ' '
        res += '--server::coach_port=' + str(self.coach_port) + ' '
        res += '--server::olcoach_port=' + str(self.online_coach_port) + ' '
        res += self.other_config
        self.logger.debug(f'Server config: {res}')
        return res

    def __str__(self):
        return self.get_config()

    def __repr__(self):
        return self.__str__()


class Game:
    def __init__(self, game_info: GameInfoMessage, port: int, data_dir: str, storage_client: StorageClient):
        self.game_info: GameInfoMessage = game_info
        self.logger = logging.getLogger(f'Game{self.game_info.game_id}')
        self.server_config = ServerConfig(game_info.server_config, game_info, data_dir, port, self.logger)
        self.port = port
        self.data_dir = data_dir
        self.finished_event = None
        self.process = None
        self.storage_client = storage_client
        self.status = 'starting'

    def check_base_team(self, base_team_name: str):
        base_teams_dir = os.path.join(self.data_dir, DataDir.base_team_dir_name)
        os.makedirs(base_teams_dir, exist_ok=True)
        base_team_path = os.path.join(base_teams_dir, base_team_name)
        if not os.path.exists(base_teams_dir):
            os.makedirs(base_teams_dir, exist_ok=True)
        if not os.path.exists(base_team_path):
            if self.storage_client.check_connection():
                base_team_zip_path = os.path.join(base_teams_dir, f'{base_team_name}.zip')
                if not self.storage_client.download_file(self.storage_client.base_team_bucket_name,
                                                         f'{base_team_name}.zip', base_team_zip_path):
                    logging.error(f'Storage connection error, base team {base_team_name} not found')
                    raise FileNotFoundError(f'Base team {base_team_name} not found')
                Tools.unzip_file(base_team_zip_path, base_teams_dir)
                os.remove(base_team_zip_path)
            else:
                logging.error(f'Storage connection error, base team {base_team_name} not found')
                raise FileNotFoundError(f'Base team {base_team_name} not found')

    def check_team_config(self, team_config_id: int):
        team_configs_dir = os.path.join(self.data_dir, DataDir.team_config_dir_name)
        os.makedirs(team_configs_dir, exist_ok=True)
        team_config_dir = os.path.join(team_configs_dir, f'{team_config_id}')
        if not os.path.exists(team_configs_dir):
            os.makedirs(team_configs_dir, exist_ok=True)
        if not os.path.exists(team_config_dir):
            if self.storage_client.check_connection():
                team_config_zip_path = os.path.join(team_configs_dir, f'{team_config_id}.zip')
                self.storage_client.download_file(self.storage_client.team_config_bucket_name,
                                                  str(team_config_id), team_config_zip_path)
                Tools.unzip_file(team_config_zip_path, team_configs_dir)
                os.remove(team_config_zip_path)
            else:
                logging.error(f'Storage connection error, team config {team_config_id} not found')
                raise FileNotFoundError(f'Team config {team_config_id} not found')

    def check(self):
        self.check_base_team(self.game_info.left_base_team_name)
        self.check_base_team(self.game_info.right_base_team_name)
        if self.game_info.left_team_config_id is not None:
            self.check_team_config(self.game_info.left_team_config_id)
        if self.game_info.right_team_config_id is not None:
            self.check_team_config(self.game_info.right_team_config_id)

    async def run_game(self):
        server_path = os.path.join(self.data_dir, DataDir.server_dir_name, 'rcssserver')
        command = f'{server_path} {self.server_config.get_config()}'
        self.logger.debug(f'Run command: {command}')

        try:
            self.process = await asyncio.create_subprocess_shell(
                command,
                stdout=PIPE,
                stderr=PIPE
            )
            out, err = await self.process.communicate()
            exit_code = self.process.returncode
            await self.finished_game(out, err, exit_code)
        except Exception as e:
            self.logger.error(f'Error in run_game: {e}')

    def check_finished(self):
        # *.rcg exist in game_log_dir
        if not os.path.exists(self.server_config.game_log_dir):
            self.logger.error(f'Game log dir {self.server_config.game_log_dir} not found')
            return False
        rcg_files = [f for f in os.listdir(self.server_config.game_log_dir) if f.endswith('.rcg')]
        rcg_file = rcg_files[0] if rcg_files else ''
        if rcg_file.find('incomplete') != -1:
            self.logger.error(f'Game log file {rcg_file} is incomplete')
            return False
        return True

    def zip_game_log_dir(self):
        # zip game_log_dir
        zip_file_path = os.path.join(os.path.join(self.data_dir, DataDir.game_log_dir_name),
                                     f'{self.game_info.game_id}.zip')
        Tools.zip_directory(self.server_config.game_log_dir, zip_file_path)
        return zip_file_path

    async def finished_game(self, out: bytes, err: bytes, exit_code: int):
        self.status = 'finished'
        # TODO save game results
        self.logger.debug(f'Game finished with exit code {exit_code}')
        # self.logger.debug(out.decode())
        # self.logger.error(err.decode())

        if self.check_finished():
            zip_file_path = self.zip_game_log_dir()
            self.logger.debug(f'Game log dir zipped to {zip_file_path}')
            if self.storage_client.check_connection():
                self.storage_client.upload_file(self.storage_client.game_log_bucket_name,
                                                zip_file_path, f'{self.game_info.game_id}.zip')
            else:
                self.logger.error(f'Storage connection error, game log not uploaded')

        await self.finished_event(self)

    def to_dict(self):
        return {
            'game_info': self.game_info.to_dict(),
            'port': self.port,
        }

    async def stop(self):
        if self.process:
            Tools.kill_process_tree(self.process.pid)
            self.process.wait()  # Ensure the main process has terminated

    def to_summary(self) -> GameInfoSummary:
        return GameInfoSummary(
            game_id=self.game_info.game_id,
            status=self.status,
            port=self.port
        )
