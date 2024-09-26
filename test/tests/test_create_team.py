import requests
import pytest
from src.utils import post, get, delete

def test_add_team():
    tmp_user = {"user_name": "test_user3", "user_code": "test_test3"}
    tmp_team_name = "test_team3"
    # Add a new user
    response = post(f"user/add", data=tmp_user)
    assert response.status_code == 200
    assert "success" in response.json().keys()
    assert response.json()["success"] == True

    # Get all users and check if the user exists
    response = get(f"user/get_all")
    assert response.status_code == 200
    users = response.json()["users"]
    added_user = next((user for user in users if user["user_name"] == tmp_user['user_name']), None)
    assert added_user is not None
    print(added_user)







    # Add a new team
    tmp_team = {"user_code": tmp_user["user_code"], "team_name": tmp_team_name}
    response = post(f"team/add", data=tmp_team)
    assert response.status_code == 200
    print(response.json())
    assert "team_id" in response.json().keys()
    team_id = response.json()["team_id"]

    # Use /team/get endpoint to verify the added team
    get_team_data = {"user_code": tmp_user["user_code"], "team_id": team_id, "team_name": tmp_team_name}
    response = post(f"team/get", data=get_team_data)
    assert response.status_code == 200
    added_team = response.json()
    assert added_team is not None and added_team["team_name"] == tmp_team_name
    print(added_team)
    
    # Remove the team
    remove_data = {"user_code": tmp_user["user_code"], "team_id": team_id}
    response = post(f"team/remove", data=remove_data)
    assert response.status_code == 200
    assert "success" in response.json().keys() and response.json()["success"] == True

    # Verify the team has been removed
    response = get(f"team/get_all")
    assert response.status_code == 200
    assert "teams" in response.json().keys()
    teams = response.json()["teams"]
    removed_team = next((team for team in teams if team["team_name"] == tmp_team_name), None)
    assert removed_team is None






    # Remove the user
    user_id = added_user["user_id"]
    remove_data = {"user_code": "test_test", "user_id": user_id}
    response = delete(f"user/{added_user['user_id']}")
    assert response.status_code == 200
    assert "success" in response.json().keys() and response.json()["success"] == True

    # Verify the user has been removed
    response = get(f"user/get_all")
    assert response.status_code == 200
    users = response.json()["users"]
    removed_user = next((user for user in users if user["user_name"] == "test_user1"), None)
    assert removed_user is None