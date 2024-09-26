import requests

BASE_URL = "http://127.0.0.1:8086/"
BASE_HEADERS = {
    "Content-Type": "application/json",
    "api_key": "api-key"
}


def get(endpoint):
    return requests.get(
        f"{BASE_URL}/{endpoint}",
        headers={
            **BASE_HEADERS,
        }
    )

def post(endpoint, data):
    return requests.post(
        f"{BASE_URL}/{endpoint}",
        headers={
            **BASE_HEADERS,
        },
        json=data
    )

def put(endpoint, data):
    return requests.put(
        f"{BASE_URL}/{endpoint}",
        headers={
            **BASE_HEADERS,
        },
        json=data
    )

def delete(endpoint):
    return requests.delete(
        f"{BASE_URL}/{endpoint}",
        headers={
            **BASE_HEADERS,
        }
    )