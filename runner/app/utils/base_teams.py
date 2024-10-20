import logging
from typing import Dict, Any, List


async def download_base_teams(
    game_runner_manager: Any, 
    settings: Dict[str, Any],
    use_git: bool = True,
    teams: List[str] = None
) -> bool:
    """
    Downloads base teams based on the provided settings, with fallback options.

    This function iterates through the base teams specified in the settings
    and attempts to download them using the provided download options in order.
    If one download method fails, it will try the next available option.

    Args:
        game_runner_manager (Any): The game runner manager instance.
        settings (Dict[str, Any]): The settings dictionary containing base team information.
        use_git (bool): Flag to determine if git and URL downloads should be used.
        teams (List[str]): List of specific team names to download. If None, all teams are downloaded.

    Returns:
        bool: True if all specified teams were downloaded successfully, False otherwise.

    Raises:
        Exception: If all download attempts for a team fail.
    """
    logging.info("Downloading base teams")
    base_teams = settings["base_teams"]
    
    if teams:
        base_teams = [team for team in base_teams if team["name"] in teams]
    
    i = 0
    for base_team in base_teams:
        i += 1
        logging.debug(f"Downloading base team {i}/{len(base_teams)}")
        team_name = base_team["name"]
        download_options = base_team["download"]

        if not isinstance(download_options, List):
            download_options = [download_options]

        logging.debug(
            f"Downloading base team {team_name}, {len(download_options)} options found"
        )
        success = False

        j = 0
        for option in download_options:
            j += 1
            if not use_git and option["type"] == "url":
                continue
            
            logging.debug(
                f"Attempting to download base team {team_name} using {option['type']}, option {j}/{len(download_options)}"
            )
            try:
                if option["type"] == "url" and use_git:
                    logging.info(
                        f"Attempting to download base team {team_name} from URL: {option['url']}"
                    )
                    res, error = await game_runner_manager.update_base_url(
                        base_team_name=team_name,
                        download_url=option["url"],
                    )
                elif option["type"] == "minio":
                    logging.info(
                        f"Attempting to download base team {team_name} from Minio"
                    )
                    res, error = await game_runner_manager.update_base_minio(
                        base_team_name=team_name,
                        bucket_name=option["bucket"],
                        file_name=option["object"],
                    )
                else:
                    logging.warning(
                        f"Unknown or unsupported download type for base team {team_name}: {option['type']}"
                    )
                    continue

                if res == False:
                    logging.error(
                        f"Failed to download base team {team_name}: {error}"
                    )
                    continue

                success = True
                break
            except Exception as e:
                logging.warning(
                    f"Failed to download team {team_name} using {option['type']}: {e}"
                )

        if not success:
            logging.error(f"All download attempts failed for base team {team_name}")
            return False
        
        logging.info(f"Successfully downloaded base team {team_name}")
    
    return True
