from models.team_model import TeamModel
from models.game_model import GameModel
from models.tournament_model import TournamentModel, TournamentStatus
from utils.messages import *


class MessageConvertor:
    @staticmethod
    def convert_add_tournament_request_message_to_tournament_model(message: AddTournamentRequestMessage, user_id:int) -> TournamentModel:
        return TournamentModel(name=message.tournament_name, 
                               owner_id=user_id,
                               start_at=message.start_at,
                               start_registration_at=message.start_registration_at,
                               end_registration_at=message.end_registration_at,
                               done=False,
                               status=TournamentStatus.WAIT_FOR_REGISTRATION)

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
                           status=game.status,
                           left_team_score=game.left_score, right_team_score=game.right_score)

    @staticmethod
    def create_tournament_team_result_message(team: TeamModel, games: list[GameModel]) -> TournamentTeamResultMessage:
        tournament_team_result = TournamentTeamResultMessage(team_id=team.id, team_name=team.name,
                                                             win=0, lose=0, draw=0,
                                                             scored_goal=0, received_goal=0, goal_difference=0,
                                                             point=0, rank=-1)
        for game in games:
            if game.left_team_id == team.id:
                tournament_team_result.scored_goal += game.left_score
                tournament_team_result.received_goal += game.right_score
                if game.left_score > game.right_score:
                    tournament_team_result.win += 1
                elif game.left_score < game.right_score:
                    tournament_team_result.lose += 1
                else:
                    tournament_team_result.draw += 1
            elif game.right_team_id == team.id:
                tournament_team_result.scored_goal += game.right_score
                tournament_team_result.received_goal += game.left_score
                if game.left_score < game.right_score:
                    tournament_team_result.win += 1
                elif game.left_score > game.right_score:
                    tournament_team_result.lose += 1
                else:
                    tournament_team_result.draw += 1
        tournament_team_result.goal_difference = tournament_team_result.scored_goal - tournament_team_result.received_goal
        tournament_team_result.point = tournament_team_result.win * 3 + tournament_team_result.draw
        return tournament_team_result

    @staticmethod
    def set_tournament_rank(tournament_results: list[TournamentTeamResultMessage]) -> list[TournamentTeamResultMessage]:
        sorted_tournament_results = sorted(tournament_results, key=lambda x: (x.point, x.goal_difference, x.scored_goal), reverse=True)
        for i, team in enumerate(sorted_tournament_results):
            team.rank = i + 1
        return sorted_tournament_results

    @staticmethod
    def convert_tournament_model_to_tournament_message(tournament: TournamentModel) -> TournamentMessage:
        tournament_results: list[TournamentTeamResultMessage] = []
        for team in tournament.teams:
            tournament_results.append(MessageConvertor.create_tournament_team_result_message(team, tournament.games))
        tournament_results = MessageConvertor.set_tournament_rank(tournament_results)

        return TournamentMessage(tournament_id=tournament.id, 
                                 tournament_name=tournament.name, 
                                 start_at=tournament.start_at,
                                 start_registration_at=tournament.start_registration_at,
                                 end_registration_at=tournament.end_registration_at,
                                 done=tournament.done,
                                 status=TournamentStatus.convert_to_str(tournament.status),
                                 user_id=tournament.owner_id,
                                 teams=[MessageConvertor.convert_team_model_to_team_message(team) for team in tournament.teams],
                                 games=[MessageConvertor.convert_game_model_to_game_message(game) for game in tournament.games],
                                 results=tournament_results)
        
    @staticmethod
    def convert_tournament_model_to_tournament_summary_message(tournament: TournamentModel) -> TournamentSummaryMessage:
        return TournamentSummaryMessage(tournament_id=tournament.id, 
                                        tournament_name=tournament.name, 
                                        start_at=tournament.start_at,
                                        start_registration_at=tournament.start_registration_at,
                                        end_registration_at=tournament.end_registration_at,
                                        done=tournament.done)
