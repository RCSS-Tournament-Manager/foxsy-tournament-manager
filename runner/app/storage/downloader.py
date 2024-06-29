import requests
import os
from utils.tools import Tools
import logging


SERVER_LINK = {'path': 'https://github.com/CLSFramework/rcssserver/releases',
               'type': 'releases',
               'file_type': 'appimage',
               'file_name':'rcssserver-x86_64-19.0.0.AppImage',
               'target_name': 'rcssserver'}

CYRUS_LINK = {
    'path': 'https://github.com/Cyrus2D/FoxsyCyrus2DBase/releases',
    'type': 'releases',
    'file_type': 'zip',
    'file_name': 'cyrus.zip',
    'target_name': 'cyrus.zip'
}

class Downloader:
    @staticmethod
    def download_latest_release(repo_url, file_name, target_name, output_dir):

        try:
            # Extract the user and repo from the URL
            parts = repo_url.rstrip('/').split('/')
            user = parts[-3]
            repo = parts[-2]

            # GitHub API URL for latest release
            api_url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
            logging.debug(f"Getting latest release info from {api_url}")

            # Get the latest release info
            response = requests.get(api_url)
            response.raise_for_status()
            release_info = response.json()

            # Find the asset with the specified file name
            asset_url = None
            for asset in release_info['assets']:
                if asset['name'] == file_name:
                    asset_url = asset['browser_download_url']
                    break

            if asset_url is None:
                raise ValueError(f"File {file_name} not found in the latest release")

            # Download the file
            logging.debug(f"Downloading {file_name} from {asset_url}")
            response = requests.get(asset_url, stream=True)
            response.raise_for_status()

            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Save the file
            logging.debug(f"Saving {file_name} to {output_dir}")
            target_path = os.path.join(output_dir, target_name)
            logging.debug(f"Target path: {target_path}")
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"Downloaded {file_name} to {target_path}")

            # check if the file is downloaded
            if os.path.exists(target_path):
                # change permission to 777
                logging.debug(f"Setting permissions for {target_path} to 777")
                Tools.set_permissions_recursive(target_path, 0o777)
                return True
            return False
        except Exception as e:
            print(f"Failed to download {file_name}: {e}")
            return False

    @staticmethod
    def download_server(output_dir: str):
        if SERVER_LINK['type'] == 'releases' and SERVER_LINK['file_type'] == 'appimage':
            Downloader.download_latest_release(SERVER_LINK['path'], SERVER_LINK['file_name'], SERVER_LINK['target_name'], output_dir)

    @staticmethod
    def download_base_team(output_dir: str, base_team_name: str):
        if base_team_name == 'cyrus':
            return Downloader.download_cyrus(output_dir)
        return False
    @staticmethod
    def download_cyrus(output_dir: str):
        if CYRUS_LINK['type'] == 'releases' and CYRUS_LINK['file_type'] == 'zip':
            return Downloader.download_latest_release(CYRUS_LINK['path'], CYRUS_LINK['file_name'], CYRUS_LINK['target_name'], output_dir)
        return False

# output_dir = os.path.join(os.getcwd())
# Downloader.download_cyrus(output_dir)