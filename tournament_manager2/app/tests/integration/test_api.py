from fastapi.testclient import TestClient
from fast_api_app import FastApiApp
from managers.database_manager import DatabaseManager
from pytest import fixture
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# Use pytest fixtures to set up and tear down for each test
@fixture(scope="function")
def test_app():
    # Set up SQLite in-memory database
    database_manager = DatabaseManager('sqlite+aiosqlite:///:memory:')
    
    # Initialize the database (since TestClient is sync, we'll run this sync too)
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_manager.init_db())

    # Set up Minio client (mocked or real depending on the test case)
    minio_client = None  # Can mock this if needed

    # Instantiate the FastAPI app
    fastapi_app = FastApiApp(
        db_manager=database_manager,
        minio_client=minio_client,
        api_key="test-api-key",
        port=8000
    )
    
    # Return a TestClient for FastAPI
    with TestClient(fastapi_app.app) as client:
        yield client

def test_add_user(test_app):
    # Define a test message
    message = {
        "user_code": "12345",
        "user_name": "Test User"
    }

    # Make a POST request to add a user
    response = test_app.post("/user/add", json=message, headers={"api_key": "test-api-key"})
    assert response.status_code == 200
    json_response = response.json()

    # Assert success and check the response
    assert json_response["success"] is True
