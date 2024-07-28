from datetime import datetime
from utils.messages import *
from models import TournamentModel, TeamModel, GameModel
from models.game_model import GameSatus
from managers.database_manager import DataBaseManager
from models.message_convertor import MessageConvertor
from sqlalchemy.orm import joinedload
import asyncio
from sqlalchemy.sql import exists
from utils.rmq_message_sender import RmqMessageSender
import logging


def create_game_info_message(game: GameModel, left_team: TeamModel, right_team: TeamModel) -> GameInfoMessage:
    game_info_message = GameInfoMessage(
        game_id=game.id,
        left_team_name=game.left_team.name,
        right_team_name=game.right_team.name,
        left_team_config_json=left_team.config,
        right_team_config_json=right_team.config,
        left_base_team_name=left_team.base_team,
        right_base_team_name=right_team.base_team,
        server_config=""
    )
    game_info_message.fix_json()
    return game_info_message


class TournamentManager:
    def __init__(self, database_manager: DataBaseManager, rmq_message_sender: RmqMessageSender):
        self.logger = logging.getLogger(__name__)
        self.logger.info('TournamentManager created')
        self.database_manager = database_manager
        self.rmq_message_sender = rmq_message_sender

    async def add_tournament(self, message: AddTournamentRequestMessage) -> AddTournamentResponseMessage:
        self.logger.info(f"add_tournament: {message}")
        session = self.database_manager.get_session()
        new_tournament = MessageConvertor.convert_add_tournament_request_message_to_tournament_model(message)
        session.add(new_tournament)

        if len(message.teams) < 2:
            session.close()
            return AddTournamentResponseMessage(tournament_id=None, success=False, error="At least 2 teams are required")

        if len(message.teams) != len(set([team.team_name for team in message.teams])):
            session.close()
            return AddTournamentResponseMessage(tournament_id=None, success=False, error="Teams are not unique")

        if any([len(team.team_name) == 0 or len(team.base_team_name) == 0 for team in message.teams]):
            session.close()
            return AddTournamentResponseMessage(tournament_id=None, success=False, error="Team name and base team name are required")

        session.commit()
        new_tournament_id = new_tournament.id
        self.logger.debug(f"Added tournament with id: {new_tournament_id} {new_tournament}")

        new_teams = []
        for team in message.teams:
            team_model = MessageConvertor.convert_team_message_to_team_model(team)
            team_model.tournament = new_tournament
            new_teams.append(team_model)
            self.logger.debug(f"Adding team: {team_model}")

        session.add_all(new_teams)
        session.commit()

        new_games = []
        for t1 in range(len(new_teams)):
            for t2 in range(t1 + 1, len(new_teams)):
                team1 = new_teams[t1]
                team2 = new_teams[t2]
                new_game = GameModel(left_team=team1, right_team=team2)
                new_game.tournament = new_tournament
                new_games.append(new_game)
                self.logger.debug(f"Adding game: {new_game}")

        session.add_all(new_games)
        session.commit()

        session.close()

        self.logger.info(f"Added tournament, games, teams with tournament id: {new_tournament_id}")
        return AddTournamentResponseMessage(tournament_id=new_tournament_id, success=True, error=None)

    async def get_tournament(self, tournament_id: int) -> TournamentMessage:
        self.logger.info(f"get_tournament: {tournament_id}")
        session = self.database_manager.get_session()
        tournament = (session.query(TournamentModel)
                        .options(joinedload(TournamentModel.teams), joinedload(TournamentModel.games))
                        .filter_by(id=tournament_id).first())
        session.close()
        if not tournament:
            return None
        tournament_message = MessageConvertor.convert_tournament_model_to_tournament_message(tournament)
        self.logger.info(f"get_tournament: {tournament_message}")
        return tournament_message

    async def get_tournaments(self) -> [TournamentMessage]:
        self.logger.info(f"get_tournaments")
        session = self.database_manager.get_session()
        tournaments = (session.query(TournamentModel)
                        .options(joinedload(TournamentModel.teams), joinedload(TournamentModel.games))
                        .all())
        session.close()
        tournament_messages = [MessageConvertor.convert_tournament_model_to_tournament_message(tournament) for tournament in tournaments]
        self.logger.info(f"get_tournaments: {tournament_messages}")
        return tournament_messages

    async def run_smart_contract(self):
        self.logger.info("Running smart contract")
        while True:
            self.logger.info("Sending request to smart contract")
            await asyncio.sleep(60)

    async def run_game_sender(self):
        self.logger.info("Running game sender")
        while True:
            session = self.database_manager.get_session()
            current_time = datetime.now()
            tournaments = (session.query(TournamentModel)
                           .options(joinedload(TournamentModel.teams), joinedload(TournamentModel.games))
                           .filter(
                TournamentModel.done == False,
                TournamentModel.start_at < current_time,
                exists().where(
                    (GameModel.tournament_id == TournamentModel.id) &
                    (GameModel.status == 'pending')
                )
            ).all())

            for tournament in tournaments:
                self.logger.info(f"Starting tournament: {tournament.name}")
                teams = tournament.teams
                games = tournament.games
                for game in games:
                    if game.status != GameSatus.PENDING:
                        continue
                    left_team = game.left_team
                    right_team = game.right_team
                    self.logger.info(f"Sending game: {left_team.name} vs {right_team.name} to runner")
                    game_info_message = create_game_info_message(game, left_team, right_team)
                    await self.rmq_message_sender.send_message(game_info_message.dict())
                    game.status = GameSatus.IN_QUEUE

                session.commit()
            session.close()
            await asyncio.sleep(10)

    async def handle_game_started(self, json: AddGameResponse):
        self.logger.info(f"game_started: {json}")
        session = self.database_manager.get_session()
        game = (session.query(GameModel)
                .filter_by(id=json.game_id).first())
        if not game:
            return
        if not json.success:
            return

        game.status = GameSatus.IN_PROGRESS
        session.commit()

    async def handle_game_finished(self, json: GameInfoSummary):
        self.logger.info(f"game_finished: {json}")
        session = self.database_manager.get_session()
        game = (session.query(GameModel)
                .options(joinedload(GameModel.tournament))
                .filter_by(id=json.game_id).first())
        if not game:
            return
        game.status = GameSatus.FINISHED
        game.left_score = json.left_score
        game.right_score = json.right_score

        tournament = game.tournament
        if all([g.status == GameSatus.FINISHED for g in tournament.games]):
            tournament.done = True

        session.commit()

