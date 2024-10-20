import logging
from typing import Dict, Any, List


async def download_base_teams(
    game_runner_manager: Any, settings: Dict[str, Any]
) -> None:
    """
    Downloads base teams based on the provided settings, with fallback options.

    This function iterates through the base teams specified in the settings
    and attempts to download them using the provided download options in order.
    If one download method fails, it will try the next available option.

    Args:
        game_runner_manager (Any): The game runner manager instance.
        settings (Dict[str, Any]): The settings dictionary containing base team information.

    Returns:
        None

    Raises:
        Exception: If all download attempts for a team fail.
    """
    logging.info("Downloading base teams")
    for base_team in settings["base_teams"]:
        team_name = base_team["name"]
        download_options = base_team["download"]

        if not isinstance(download_options, List):
            download_options = [download_options]

        logging.debug(
            f"Downloading base team {team_name}, {len(download_options)} options found"
        )
        success = False
        counter = 0
        for option in download_options:
            counter += 1
            logging.debug(
                f"Attempting to download base team {team_name} using {option['type']}, {counter}/{len(download_options)}"
            )
            try:
                if option["type"] == "url":
                    logging.info(
                        f"Attempting to download base team {team_name} from URL: {option['url']}"
                    )
                    res, error = await game_runner_manager.update_base_url(
                        base_team_name=team_name,
                        download_url=option["url"],
                    )

                    if res == False:
                        logging.error(
                            f"Failed to download base team {team_name} from URL: {error}"
                        )
                        continue

                    success = True
                    break
                elif option["type"] == "minio":
                    logging.info(
                        f"Attempting to download base team {team_name} from Minio"
                    )
                    res,error = await game_runner_manager.update_base_minio(
                        base_team_name=team_name,
                        bucket_name=option["bucket"],
                        file_name=option["object"],
                    )

                    if res == False:
                        logging.error(
                            f"Failed to download base team {team_name} from Minio: {error}"
                        )
                        continue

                    success = True
                    break
                else:
                    logging.warning(
                        f"Unknown download type for base team {team_name}: {option['type']}"
                    )
            except Exception as e:
                logging.warning(
                    f"Failed to download team {team_name} using {option['type']}: {e}"
                )

        if success:
            logging.info(f"Successfully downloaded base team {team_name}")
        else:
            logging.error(f"All download attempts failed for base team {team_name}")
            raise Exception(f"Failed to download base team {team_name}")
