import requests
import pytest
from src.utils import post, get, delete

def test_add_user():
    # Add a new user
    tmp_user = {"user_name": "test_user1", "user_code": "test_test"}
    response = post(f"user/add", data=tmp_user)
    assert response.status_code == 200
    assert "success" in response.json().keys()
    assert response.json()["success"] == True

    # Get all users and check if the user exists
    response = get(f"user/get_all")
    assert response.status_code == 200
    users = response.json()["users"]
    added_user = next((user for user in users if user["user_name"] == "test_user1"), None)
    assert added_user is not None
    print(added_user)

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


