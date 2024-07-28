from models.team_model import TeamModel
from models.tournament_model import TournamentModel
from utils.messages import AddTournamentRequestMessage, AddTournamentResponseMessage, TeamMessage, TournamentMessage, GameMessage


class MessageConvertor:
    @staticmethod
    def convert_add_tournament_request_message_to_tournament_model(message: AddTournamentRequestMessage) -> TournamentModel:
        return TournamentModel(name=message.tournament_name, user_id=message.user_id, start_at=message.start_at)

    @staticmethod
    def convert_team_message_to_team_model(team_message: TeamMessage) -> TeamModel:
        return TeamModel(name=team_message.team_name, user_id=team_message.user_id,
                         base_team=team_message.base_team_name, config=team_message.team_config_json)

    @staticmethod
    def convert_team_model_to_team_message(team: TeamModel) -> TeamMessage:
        return TeamMessage(team_id=team.id,
                           user_id=team.user_id, team_name=team.name,
                           team_config_json=team.config, base_team_name=team.base_team)

    @staticmethod
    def convert_game_model_to_game_message(game) -> GameMessage:
        return GameMessage(game_id=game.id, left_team_id=game.left_team_id, right_team_id=game.right_team_id,
                           status=game.status)
    @staticmethod
    def convert_tournament_model_to_tournament_message(tournament: TournamentModel) -> TournamentMessage:
        return TournamentMessage(tournament_id=tournament.id, tournament_name=tournament.name, start_at=tournament.start_at,
                                 user_id=tournament.user_id,
                                 teams=[MessageConvertor.convert_team_model_to_team_message(team) for team in tournament.teams],
                                    games=[MessageConvertor.convert_game_model_to_game_message(game) for game in tournament.games])
