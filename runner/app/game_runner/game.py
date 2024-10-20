import os
import logging
from utils.base_teams import download_base_teams
from utils.tools import Tools
import asyncio
from storage.storage_client import StorageClient
from data_dir import DataDir
from subprocess import PIPE
from utils.messages import *
from storage.downloader import Downloader
from utils.config import config as MainConfig


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

        self.left_team_config_id_path = None
        self.right_team_config_id_path = None
        self.left_team_config_json = None
        self.right_team_config_json = None
        self.left_team_config_json_encoded = None
        self.right_team_config_json_encoded = None
        if game_info.left_team_config_id is not None:
            self.left_team_config_id_path = os.path.join(data_dir, DataDir.team_config_dir_name,
                                                        f'{game_info.left_team_config_id}')
        if game_info.right_team_config_id is not None:
            self.right_team_config_id_path = os.path.join(data_dir, DataDir.team_config_dir_name,
                                                         f'{game_info.right_team_config_id}')
        if game_info.left_team_config_json is not None:
            self.left_team_config_json = game_info.left_team_config_json
        if game_info.right_team_config_json is not None:
            self.right_team_config_json = game_info.right_team_config_json

        if game_info.left_team_config_json_encoded is not None:
            self.left_team_config_json_encoded = game_info.left_team_config_json_encoded
        if game_info.right_team_config_json_encoded is not None:
            self.right_team_config_json_encoded = game_info.right_team_config_json_encoded


    def get_config(self):
        auto_mode = 'true' if self.auto_mode else 'false'
        synch_mode = 'true' if self.synch_mode else 'false'
        res = ""
        res += f'--server::auto_mode={auto_mode} '
        res += f'--server::synch_mode={synch_mode} '

        left_team_start = f"--server::team_l_start=\\'{self.left_team_start} -p {self.port} -t {self.left_team_name}"
        if self.left_team_config_id_path:
            left_team_start += f" -c {self.left_team_config_id_path}"
        elif self.left_team_config_json and self.left_team_config_json != '{}':
            self.left_team_config_json = self.left_team_config_json.replace('\\', '')
            self.left_team_config_json = self.left_team_config_json.replace('"', '\\"')
            left_team_start += f" -j '{self.left_team_config_json}'"
        elif self.left_team_config_json_encoded:
            left_team_start += f" -j {self.left_team_config_json_encoded} -e temp"
        left_team_start += "\\' "
        res += left_team_start

        right_team_start = f"--server::team_r_start=\\'{self.right_team_start} -p {self.port} -t {self.right_team_name}"
        if self.right_team_config_id_path:
            right_team_start += f" -c {self.right_team_config_id_path}"
        elif self.right_team_config_json and self.right_team_config_json != '{}':
            self.right_team_config_json = self.right_team_config_json.replace('\\', '')
            self.right_team_config_json = self.right_team_config_json.replace('"', '\\"')
            right_team_start += f" -j '{self.right_team_config_json}'"
        elif self.right_team_config_json_encoded:
            right_team_start += f" -j {self.right_team_config_json_encoded} -e temp"
        right_team_start += "\\' "
        res += right_team_start

        res += f'--server::game_log_dir={self.game_log_dir} '
        res += f'--server::text_log_dir={self.text_log_dir} '
        res += '--server::half_time=100 '
        res += '--server::nr_normal_halfs=2 '
        res += '--server::nr_extra_halfs=0 '
        res += '--server::penalty_shoot_outs=0 '
        res += '--server::port=' + str(self.port) + ' '
        res += '--server::coach_port=' + str(self.coach_port) + ' '
        res += '--server::olcoach_port=' + str(self.online_coach_port) + ' '
        if self.other_config:
            res += self.other_config
        self.logger.debug(f'Server config: {res}')
        return res

    def __str__(self):
        return self.get_config()

    def __repr__(self):
        return self.__str__()


class Game:
    def __init__(
            self, 
            game_info: GameInfoMessage, 
            port: int, 
            data_dir: str, 
            storage_client: StorageClient,
            base_teams_config: dict,
            runner_manager,
    ):
        self.logger = logging.getLogger(f'Game{game_info.game_id}')
        self.logger.info(f'Game created: {game_info}')
        self.game_info: GameInfoMessage = game_info
        self.server_config = ServerConfig(game_info.server_config, game_info, data_dir, port, self.logger)
        self.port = port
        self.data_dir = data_dir
        self.finished_event = None
        self.process = None
        self.storage_client = storage_client
        self.status = 'starting'
        self.game_result = [-1, -1, -1, -1]
        self.base_teams_config = base_teams_config
        self.runner_manager = runner_manager

    async def check_base_team(self, base_team_name: str):
        base_teams_dir = os.path.join(self.data_dir, DataDir.base_team_dir_name)
        base_team_path = os.path.join(base_teams_dir, base_team_name)
        self.logger.debug(f'Check base team {base_team_name}, path: {base_team_path}, dir: {base_teams_dir}')

        if os.path.exists(base_team_path):
            self.logger.debug(f'Base team {base_team_name} already exists')
            # if start.sh exists
            if os.path.exists(os.path.join(base_team_path, 'start.sh')):
                self.logger.debug(f'Base team {base_team_name} start.sh exists')
                return True
            else:
                self.logger.error(f'Base team {base_team_name} start.sh not found')
                Tools.remove_dir(base_team_path)
        if os.path.isfile(base_teams_dir):
            self.logger.error(f'Base teams dir {base_teams_dir} is a file')
            raise FileNotFoundError(f'Base teams dir {base_teams_dir} is a file')


        # check if the base team exists in the base_teams_config
        exists = False
        base_team_config = None
        for base_team in self.base_teams_config:
            if base_team['name'] == base_team_name:
                exists = True
                base_team_config = base_team
                break
        if not exists:
            self.logger.error(f'Base team {base_team_name} not found in base_teams_config')
            raise FileNotFoundError(f'Base team {base_team_name} not found in base_teams_config')
        

        try :
            res = await download_base_teams(self.runner_manager, {"base_teams":base_team_config})
            if not res:
                raise Exception(f'Failed to download base team {base_team_name}')
        except Exception as e:
            self.logger.error(f'Failed to download base team {base_team_name}: {e}')
            raise FileNotFoundError(f'Failed to download base team {base_team_name}: {e}')
            

    def check_team_config(self, team_config_id: int):
        team_configs_dir = os.path.join(self.data_dir, DataDir.team_config_dir_name)
        os.makedirs(team_configs_dir, exist_ok=True)
        team_config_dir = os.path.join(team_configs_dir, f'{team_config_id}')
        if not os.path.exists(team_configs_dir):
            os.makedirs(team_configs_dir, exist_ok=True)
        if not os.path.exists(team_config_dir):
            if self.storage_client is not None and self.storage_client.check_connection():
                team_config_zip_path = os.path.join(team_configs_dir, f'{team_config_id}.zip')
                self.storage_client.download_file(self.storage_client.team_config_bucket_name,
                                                  str(team_config_id), team_config_zip_path)
                Tools.unzip_file(team_config_zip_path, team_configs_dir)
                os.remove(team_config_zip_path)
            else:
                self.logger.error(f'Storage connection error, team config {team_config_id} not found')
                raise FileNotFoundError(f'Team config {team_config_id} not found')

    async def check(self):
        await self.check_base_team(self.game_info.left_base_team_name)
        await self.check_base_team(self.game_info.right_base_team_name)
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

    def check_server_output(self):
        out_file = os.path.join(self.server_config.game_log_dir, 'out.txt')
        # check if out.txt exists
        if not os.path.exists(out_file):
            self.logger.error(f'Out file {out_file} not found')
            return False
        with open(out_file, 'r') as f:
            lines = f.readlines()
            count = Tools.count_matching_lines(lines, rf'A new \(v\d+\) player \({self.game_info.left_team_name} \d+\) connected\.')
            if count != 11:
                self.logger.error(f'Out file {out_file} not contain 11 lines')
                return False

            count = Tools.count_matching_lines(lines, rf'A new \(v\d+\) player \({self.game_info.right_team_name} \d+\) connected\.')
            if count != 11:
                self.logger.error(f'Out file {out_file} not contain 11 lines')
                return False

            count = Tools.count_matching_lines(lines, rf'A player disconnected : \({self.game_info.left_team_name} \d+\)')
            if count != 11:
                self.logger.warning(f'Out file {out_file} contain disconnect lines')

            count = Tools.count_matching_lines(lines, rf'A player disconnected : \({self.game_info.right_team_name} \d+\)')
            if count != 11:
                self.logger.warning(f'Out file {out_file} contain disconnect lines')

        return True
    def check_finished(self):
        # *.rcg exist in game_log_dir
        if not os.path.exists(self.server_config.game_log_dir):
            self.logger.error(f'Game log dir {self.server_config.game_log_dir} not found')
            return False
        rcg_files = [f for f in os.listdir(self.server_config.game_log_dir) if f.endswith('.rcg')]
        rcg_file = rcg_files[0] if rcg_files else None
        if not rcg_file:
            self.logger.error(f'Game log file not found')
            return False
        if rcg_file.find('incomplete') != -1:
            self.logger.error(f'Game log file {rcg_file} is incomplete')
            return False
        if rcg_file.find(self.game_info.left_team_name) == -1:
            self.logger.error(f'Game log file {rcg_file}, team [{self.game_info.left_team_name}] not found')
            return False
        if rcg_file.find(self.game_info.right_team_name) == -1:
            self.logger.error(f'Game log file {rcg_file}, team [{self.game_info.right_team_name}] not found')
            return False
        self.game_result = Tools.find_game_result_from_rcg_file_name(rcg_file)
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
        out_file = os.path.join(self.server_config.game_log_dir, 'out.txt')
        err_file = os.path.join(self.server_config.game_log_dir, 'err.txt')
        with open(out_file, 'wb') as f:
            f.write(out)
        with open(err_file, 'wb') as f:
            f.write(err)

        valid = self.check_finished()
        if valid:
            zip_file_path = self.zip_game_log_dir()
            self.logger.debug(f'Game log dir zipped to {zip_file_path}')
            if self.storage_client is not None and self.storage_client.check_connection():
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

    def to_game_finished_message(self) -> GameFinishedMessage:
        return GameFinishedMessage(
            game_id=self.game_info.game_id,
            status=self.status,
            port=self.port,
            left_score=self.game_result[0],
            right_score=self.game_result[1],
            left_penalty=self.game_result[2],
            right_penalty=self.game_result[3]
        )
