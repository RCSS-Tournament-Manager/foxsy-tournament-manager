from datetime import datetime, timedelta
from random import shuffle
from tkinter import N

from sqlmodel import Session, select
from manager.tournament_manager import TournamentManager
from model.game import Game, GameStatus
from model.team import Team, TeamBase
from model.tournament import Tournament


def test_creating_tournament():
    N_TEAMS = 10
    
    manager = TournamentManager()
    
    teams = []
    for i in range(N_TEAMS):
        team_name = f"Team {i}"
        teams.append(
            Team(team_name=team_name,
                 team_base=TeamBase.CYRUS if i % 2 == 0 else TeamBase.OXSY,
                 config="")
        )
    
    tournament_time = datetime.now() + timedelta(hours=1)
    tournament = manager.create_tournament(
        Tournament(name="Test Tournament",start_time=tournament_time)
    )
    
    for team in teams:
        manager.add_team_to_tournament(tournament.id, team)
    
    t = manager.get_tournament(tournament.id)
    assert t.name == "Test Tournament"
    assert t.start_time == tournament_time
    tmp_teams = list(teams)
    all_teams = manager.get_teams(tournament.id)
    for i, team in enumerate(all_teams):
        tmp_teams.remove(team)
    assert len(tmp_teams) == 0
    
    true_game_list = []
    for i in range(N_TEAMS):
        for j in range(i + 1, N_TEAMS):
            true_game_list.append((all_teams[i].id, all_teams[j].id))
    shuffle(true_game_list)
    
    manager.edit_tournament(tournament.id, Tournament(name=tournament.name, start_time=tournament.start_time + timedelta(hours=1)))
    
    t = manager.get_tournament(tournament.id)
    assert t.start_time == tournament_time + timedelta(hours=1)
    assert t.name == tournament.name
    
    manager.commit_tournament(tournament.id)
    
    t = manager.get_tournament(tournament.id)
    assert t.start_time == tournament_time + timedelta(hours=1)
    assert t.name == tournament.name
    assert t.commited == True
    
    games = manager.get_games(tournament.id)
    tmp_games = list(true_game_list)
    for game in games:
        if (game.team_left_id, game.team_right_id) in tmp_games:
            tmp_games.remove((game.team_left_id, game.team_right_id))
        elif (game.team_right_id, game.team_left_id) in tmp_games:
            tmp_games.remove((game.team_right_id, game.team_left_id))
    assert len(tmp_games) == 0
    
    manager.edit_tournament(tournament.id, Tournament(name=tournament.name, start_time=tournament.start_time + timedelta(hours=1)))
     
    t = manager.get_tournament(tournament.id)
    assert t.start_time == tournament_time + timedelta(hours=1)
    assert t.name == tournament.name
    
    manager.uncommit_tournament(tournament.id)
    
    t = manager.get_tournament(tournament.id)
    assert t.start_time == tournament_time + timedelta(hours=1)
    assert t.name == tournament.name
    assert t.commited == False
    
    games = manager.get_games(tournament.id)
    assert len(games) == 0
    
    manager.edit_tournament(tournament.id, Tournament(name=tournament.name, start_time=t.start_time + timedelta(hours=1)))
    
    t = manager.get_tournament(tournament.id)
    assert t.start_time == tournament_time + timedelta(hours=2)
    assert t.name == tournament.name
    assert t.commited == False
    
    manager.commit_tournament(tournament.id)
    
    t = manager.get_tournament(tournament.id)
    assert t.start_time == tournament_time + timedelta(hours=2)
    assert t.name == tournament.name
    assert t.commited == True
    
    games = manager.get_games(tournament.id)
    tmp_games = list(true_game_list)
    for game in games:
        if (game.team_left_id, game.team_right_id) in tmp_games:
            tmp_games.remove((game.team_left_id, game.team_right_id))
        elif (game.team_right_id, game.team_left_id) in tmp_games:
            tmp_games.remove((game.team_right_id, game.team_left_id))
    assert len(tmp_games) == 0
        
if __name__ == "__main__":
    test_creating_tournament()
    print("Everything passed!")