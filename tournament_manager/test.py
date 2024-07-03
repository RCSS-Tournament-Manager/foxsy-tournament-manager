from datetime import datetime
from random import shuffle
from tkinter import N

from sqlmodel import Session, select
from manager.tournament_manager import TournamentManager
from model.game import Game, GameStatus
from model.team import Team, TeamBase
from model.tournament import Tournament


def test_creating_tournament():
    N_TEAMS = 5
    
    manager = TournamentManager()
    
    teams = []
    for i in range(N_TEAMS):
        teams.append(
            Team(team_name=f"Team {i}",
                 team_base=TeamBase.CYRUS if i % 2 == 0 else TeamBase.OXSY,
                 config="")
        )
    true_game_list = []
    for i in range(N_TEAMS):
        for j in range(i + 1, N_TEAMS):
            true_game_list.append((f'Team {i}', f'Team {j}'))
    shuffle(true_game_list)
    
    t = datetime.now()
    manager.create_tournament(
        tournament_name="Test Tournament",
        start_time=t,
        teams=teams
    )
    
    db = manager.db
    with Session(db) as session:
        statement = select(Tournament)
        tournaments = session.exec(statement).all()
        assert len(tournaments) == 1
        tournament = tournaments[0]
        assert tournament.name == "Test Tournament"
        assert tournament.start_time == t
        
        statement = select(Team)
        teams = session.exec(statement).all()
        assert len(teams) == N_TEAMS
        for i, team in enumerate(teams):
            assert team.team_name == f"Team {i}"
            assert team.team_base == TeamBase.CYRUS if i % 2 == 0 else TeamBase.OXSY
            assert team.config == ""
        
        statement = select(Game)
        games = session.exec(statement).all()
        for game in games:
            assert game.tournament_id == tournament.id
            assert game.start_time == None
            assert game.end_time == None
            assert game.status == GameStatus.WAITING
            assert game.order == 0
            
            statement = select(Team).where(Team.id == game.team_left_id)
            team_left = session.exec(statement).first()
            statement = select(Team).where(Team.id == game.team_right_id)
            team_right = session.exec(statement).first()
            assert (team_left.team_name, team_right.team_name) \
                or (team_right.team_name, team_left.team_name) in true_game_list
            true_game_list.remove((team_left.team_name, team_right.team_name))
        assert len(true_game_list) == 0
        
if __name__ == "__main__":
    test_creating_tournament()
    print("Everything passed!")