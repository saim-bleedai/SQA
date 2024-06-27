from fastapi.testclient import TestClient
import random
import string
import sys
import time
import json
import requests
from datetime import datetime

sys.path.append("./app/")

from main import app

client = TestClient(app)

payload = None
token = None


def setup(generate_token=False):
    if generate_token:
        get_token()
    get_random_payload()


def get_token():
    global token

    username = "admin"
    password = "test123"

    payload = {"grant_type": "password", "username": username, "password": password}
    response = client.post("/token", data=payload)

    token_response = response.json()
    token = token_response["access_token"]


def delete_all_users():
    response = client.get("/v1/user/all/", headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        users = response.json()["users"]
        for user in users:
            user_id = user["id"]
            client.delete(
                f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
            )


def get_random_payload():
    global payload
    global creator_payload
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    days = [str(x) for x in range(28)]
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    years = [str(x) for x in range(1970, 2010)]

    id = "test-" + random_str
    username = "user" + id
    name = "test" + username
    email = id + "@gmail.com"
    interests = ["Tech", "Motivational Speaking"]
    date_of_birth = (
        f"{random.choice(days)}-{random.choice(months)}-{random.choice(years)}"
    )
    creator_name = "test-creator" + random_str
    description = "testdescription" + random_str
    summary = "test summary" + random_str
    personality = "test-personality" + random_str
    experience = "test experience" + random_str
    habits = "test habits" + random_str + "," + random_str + "," + random_str
    greeting_message = ("greeting message" + random_str,)

    payload = {
        "id": id,
        "username": username,
        "name": name,
        "email": email,
        "interests": interests,
        "date_of_birth": "12-jan-1990",
    }

    creator_payload = {
        "user_id": None,
        "name": creator_name,
        "description": description,
        "summary": summary,
        "personality": personality,
        "experience": experience,
        "habits": habits,
        "greeting_message": greeting_message,
    }


def create_user():
    setup(generate_token=True)
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    return response


def create_creator():
    setup(generate_token=True)
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )

    id = response.json()["id"]
    creator_payload["user_id"] = id
    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return result


def create_chat():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()

    user_id = result.json()["id"]

    chat_payload = {
        "user_id": user_id,
        "creator_id": creator_id,
        "pinned": False,
        "muted": False,
    }

    response = client.post(
        "/v1/chat/create",
        headers={"Authorization": f"Bearer {token}"},
        data=chat_payload,
    )

    return response


def create_message(chat_id):
    setup()
    message_payload = {
        "chat_id": chat_id,
        "message_type": "text",
        "message": "hello how are you",
        "audio_output": False,
        "use_rag": False,
    }
    result = client.post(
        f"/v1/message/generate_chat/",
        headers={"Authorization": f"Bearer {token}"},
        data=message_payload,
    )
    return result


def test_search_recent():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    user_id = response.json()["user_id"]

    # generate a chat
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    # testing the search recent endpoint

    result = client.get(
        f"/v1/search/recent",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": user_id,
            "term": "HELLO",  # will automatically check when case sensisitive is false
        },
    )
    assert result.status_code == 200
    expected_message_text = "hello, how are you"
    data = result.json()
    # Validate the content of 'recent_messages'
    recent_messages = data["recent_messages"]
    assert isinstance(recent_messages, list)

    # Check that 'recent_messages' is not empty if that's expected
    assert len(recent_messages) > 0

    # Validate each message object in the array
    for message in recent_messages:
        # Assert the presence of all necessary keys in each message
        assert "chat_id" in message
        assert "creator_name" in message
        assert "message" in message
        assert "timestamp" in message

        # Specific assertion for the 'message' key value
        expected_message_text = "hello how are you"
        actual_message_text = message[
            "message"
        ].strip()  # Strip to avoid whitespace issues
        assert actual_message_text == expected_message_text

        #  type checking and content validation
        assert isinstance(message["chat_id"], int)
        assert isinstance(message["creator_name"], str)
        assert isinstance(message["message"], str)
    delete_all_users()


def test_search_case_sensitive_true():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    user_id = response.json()["user_id"]

    # generate a chat
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    # testing the search recent endpoint

    result = client.get(
        f"/v1/search/recent",
        headers={"Authorization": f"Bearer {token}"},
        params={"user_id": user_id, "term": "HELLO", "case_sensitive": True},
    )
    assert result.status_code == 200
    data = result.json()
    assert len(data["recent_messages"]) == 0
    delete_all_users()


def test_search_no_results():

    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    user_id = response.json()["user_id"]

    # generate a chat
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    # testing the search recent endpoint

    result = client.get(
        f"/v1/search/recent",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": user_id,
            "term": "invalidstring",
        },
    )
    assert result.status_code == 200
    data = result.json()
    assert len(data["recent_messages"]) == 0
    assert len(data["recent_messages"]) == 0
    delete_all_users()


def test_search_with_invalid_id():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]

    user_id = response.json()["user_id"]

    # generate a chat
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]
    client.delete(f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"})

    # testing the search recent endpoint

    result = client.get(
        f"/v1/search/recent",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": user_id,
            "term": "invalidstring",
        },
    )
    assert result.status_code == 200
    data = result.json()
    assert len(data["recent_messages"]) == 0
    assert len(data["recent_messages"]) == 0
    delete_all_users()


def test_search_chat_messages():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    # Perform a search in the chat with the term 'h' and case sensitivity turned off
    result = client.get(
        f"/v1/search/chat",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "chat_id": chat_id_1,
            "term": "h",
        },
    )

    assert result.status_code == 200

    # Parse the response JSON to get the messages data
    messages = result.json().get("messages", [])

    # Check that the search results are not empty
    assert len(messages) > 0

    # Check if the word 'hi' is present in any of the messages, regardless of case
    message_texts = [msg["message"] for msg in messages]
    assert any("hello" in message.lower() for message in message_texts)

    # Optionally, assert the presence and correctness of each message details
    for message in messages:
        assert "message_id" in message
        assert isinstance(message["message_id"], int)
        assert "message" in message
        assert isinstance(message["message"], str)

    delete_all_users()


def test_search_chat_messages_no_result():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    result = client.get(
        f"/v1/search/chat",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "chat_id": chat_id_1,
            "term": "xyz123",  # Using a term that is unlikely to be present in any message
            "case_sensitive": "false",
        },
    )

    assert result.status_code == 200

    # Parse the response JSON to check for messages
    messages = result.json().get("messages", [])

    # Check that the search results are indeed empty
    assert len(messages) == 0
    delete_all_users()


def test_search_recent_chat_upper_case():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]

    # Perform a search in the chat with the term 'h' and case sensitivity turned off
    result = client.get(
        f"/v1/search/chat",
        headers={"Authorization": f"Bearer {token}"},
        params={"chat_id": chat_id_1, "term": "HELLO", "case_sensitive": True},
    )

    assert result.status_code == 200

    # Parse the response JSON to get the messages data
    messages = result.json().get("messages", [])

    # Check that the search results are indeed empty
    assert len(messages) == 0
    delete_all_users()


def test_search_recent_chats_with_invalid_id():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]

    user_id = response.json()["user_id"]

    # generate a chat
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201
    message_id = message_response.json()["id"]
    client.delete(f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"})

    # testing the search recent endpoint

    result = client.get(
        f"/v1/search/chat",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "chat_id": chat_id_1,
            "term": "h",
        },
    )

    assert result.status_code == 200
    messages = result.json().get("messages", [])

    # Check that the search results are indeed empty
    assert len(messages) == 0
    delete_all_users()
