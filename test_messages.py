from fastapi.testclient import TestClient
import random
import string
import sys
import time
import json
import requests
from datetime import datetime
import os
import validators

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


def test_add_message():  # smoke test for add message
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]
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

    assert result.status_code == 201
    message_id = result.json()["id"]

    assert result.json()["chat_id"] == chat_id
    assert result.json()["starred"] == False  # should be false by default

    # additional check, getting the chat and seeing if message list contains the messgae

    get_chat_response = client.get(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    chat_details = get_chat_response.json()
    assert get_chat_response.status_code == 200
    # Check if the messages list contains the newly added message
    messages = get_chat_response.json()["messages"]
    assert len(messages) > 0, "No messages found in the chat"

    # Additional checks to verify if message is present in the chat array
    assert (
        message_id == messages[1]["id"]
    )  # this line needs to be changed when talha fixes the error
    assert get_chat_response.json()["id"] == chat_id
    delete_all_users()


def test_create_message_with_invalid_id():
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)
    response_delete = client.delete(
        f"/v1/chat/{chat_id_1}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204
    time.sleep(1)

    message_response = create_message(chat_id_1)
    assert message_response.status_code == 404
    assert message_response.json() == {
        "detail": "Chat not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_create_message_with_different_payload():
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]
    message_payload = {
        "chat_id": chat_id,
        "message_type": "text",
        "message": "hello how are you",
        "audio_output": True,
        "use_rag": True,
    }
    result = client.post(
        f"/v1/message/generate_chat/",
        headers={"Authorization": f"Bearer {token}"},
        data=message_payload,
    )

    assert result.status_code == 201

    assert result.json()["chat_id"] == chat_id

    generated_message = result.json()
    expected_keys = ["id", "chat_id", "message", "starred", "reaction", "audio_file"]

    for key in expected_keys:
        assert (
            key in generated_message
        ), f"Generated message response is missing key '{key}'"
    delete_all_users()


def test_create_message_with_unrequired_fields():
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]
    message_payload = {
        "chat_id": chat_id,
        "message_type": "text",
        "message": "hello how are you",
        # "audio_output": False,
        "use_rag": False,
    }
    result = client.post(
        f"/v1/message/generate_chat/",
        headers={"Authorization": f"Bearer {token}"},
        data=message_payload,
    )

    assert result.status_code == 422  # expected output should be a 422 error
    delete_all_users()


def test_get_message():  # smoke test for get message
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    # testing the get messgae route

    get_message = client.get(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 200
    assert get_message.json()["id"] == message_id
    assert get_message.json()["chat_id"] == chat_id_1
    delete_all_users()


def test_get_message_with_invalid_id():
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)

    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204
    time.sleep(1)

    get_message = client.get(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 404
    assert get_message.json() == {
        "detail": "Message not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_message_invalid_input():
    message_id = "one"  # giving a string input to message id which is an integer field

    get_message = client.get(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 422


def test_delete_message():  # smoke test for delete message
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)

    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204
    time.sleep(1)

    get_message = client.get(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 404
    assert get_message.json() == {
        "detail": "Message not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_delete_message_with_invalid_id():
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)

    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204
    time.sleep(1)

    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 404
    assert response_delete.json() == {
        "detail": "Message not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_delete_message_invalid_input():
    message_id = "one"  # giving a string input to message id which is an integer field
    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 422  # throws unprocessable entity error


def test_update_message():  # smoke test for update message
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]
    message_id = message_id - 1
    time.sleep(1)

    update_payload = {
        "message": "good morning",
        "starred": True,
        "reaction": "random emoji",
    }

    update_result = client.put(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
        params={"message_id": message_id},
    )

    assert update_result.status_code == 201 or update_result.status_code == 200
    assert update_result.json()["id"] == message_id
    assert update_result.json()["chat_id"] == chat_id_1
    assert update_result.json()["message"] == update_payload["message"]
    assert update_result.json()["reaction"] == update_payload["reaction"]
    assert update_result.json()["starred"] == update_payload["starred"]

    # getting the message and verifying the responses
    get_message = client.get(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert (
        get_message.status_code == 201 or get_message.status_code == 200
    )  # need to ask why return 201 on a put req
    assert get_message.json()["id"] == message_id
    assert get_message.json()["chat_id"] == chat_id_1
    assert get_message.json()["message"] == update_payload["message"]
    assert get_message.json()["reaction"] == update_payload["reaction"]
    assert get_message.json()["starred"] == update_payload["starred"]
    delete_all_users()


def test_update_field_validation():
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    update_payload = {"message": "", "starred": "falser", "reaction": ""}

    update_result = client.put(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
    )

    assert update_result.status_code == 422
    delete_all_users()


def test_update_message_invalid_id():
    chat_result = create_chat()

    assert chat_result.status_code == 201
    chat_id_1 = chat_result.json()["id"]
    time.sleep(1)
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

    update_payload = {"message": "", "starred": "", "reaction": ""}

    update_result = client.put(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
    )

    assert update_result.status_code == 404
    assert update_result.json() == {
        "detail": "Message not found"
    }  # ensuring a valid error message is returned

    delete_all_users()


def test_get_message_audio():  # testing if the retrieved message contains the audio url
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]

    # Define the path to the audio file
    base_path = "fanbai_ss"
    audio_file_path = os.path.join(base_path, "hello.wav")
    assert os.path.exists(audio_file_path)

    # Open the audio file in binary mode
    with open(audio_file_path, "rb") as audio_file:
        message_payload = {
            "chat_id": chat_id,
            "message_type": "audio",
            "message": "hi",  # This can be a short description or empty
            "audio_output": False,
            "use_rag": False,
        }
        files = {"audio_file": ("hello.wav", audio_file, "audio/wav")}

        # Send the POST request to add an audio message
        result = client.post(
            f"/v1/message/generate_chat/",
            headers={"Authorization": f"Bearer {token}"},
            data=message_payload,
            files=files,
        )

        # Assertions for the add message operation
        assert result.status_code == 201
        message_id = result.json()["id"]

        # getting the created message to verify if the audio url is returned in the response

        get_message = client.get(
            f"/v1/message/{message_id}/audio",
            headers={"Authorization": f"Bearer {token}"},
            params={"message_id": message_id},
        )
        assert get_message.status_code == 200
        assert get_message.json()["id"] == message_id
        assert get_message.json()["chat_id"] == chat_id

        message_details = get_message.json()

        # Asserting all necessary fields are present
        expected_fields = [
            "id",
            "chat_id",
            "audio_url",
        ]
        for field in expected_fields:
            assert field in message_details
        # Validate the audio URL format
        assert validators.url(message_details["audio_url"])
        delete_all_users()


def test_add_message_audio_with_text():  # sending the audiofile when message type is string
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]

    # Define the path to the audio file
    base_path = "fanbai_ss"
    audio_file_path = os.path.join(base_path, "hello.wav")
    assert os.path.exists(audio_file_path)

    # Open the audio file in binary mode
    with open(audio_file_path, "rb") as audio_file:
        message_payload = {
            "chat_id": chat_id,
            "message_type": "text",
            "message": "hi",
            "audio_output": False,
            "use_rag": False,
        }
        files = {"audio_file": ("hello.wav", audio_file, "audio/wav")}

        # Send the POST request to add an audio message
        result = client.post(
            f"/v1/message/generate_chat/",
            headers={"Authorization": f"Bearer {token}"},
            data=message_payload,
            files=files,
        )

        # Assertions for the add message operation
        assert result.status_code == 201
        delete_all_users()


def test_get_string_message_audio():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    # getting the audio of the string message
    get_message = client.get(
        f"/v1/message/{message_id}/audio",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 200
    assert get_message.json()["id"] == message_id
    assert get_message.json()["chat_id"] == chat_id_1

    message_details = get_message.json()

    # Asserting all necessary fields are present
    expected_fields = [
        "id",
        "chat_id",
        "audio_url",
    ]
    for field in expected_fields:
        assert field in message_details
    # Validate the audio URL format
    assert validators.url(message_details["audio_url"])
    delete_all_users()


def test_get_invalid_message_audio():
    response = create_chat()
    assert response.status_code == 201
    chat_id_1 = response.json()["id"]
    message_response = create_message(chat_id_1)
    assert message_response.status_code == 201  # message created
    message_id = message_response.json()["id"]

    response_delete = client.delete(
        f"/v1/message/{message_id}",
        headers={"Authorization": f"Bearer {token}"},  # deleting the created message
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

    # getting the audio of the deleted message
    get_message = client.get(
        f"/v1/message/{message_id}/audio",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 404
    assert get_message.json() == {
        "detail": "Message not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_message_audio_validation_check():
    setup()
    message_id = "one"  # sending the message id as string
    get_message = client.get(
        f"/v1/message/{message_id}/audio",
        headers={"Authorization": f"Bearer {token}"},
        params={"message_id": message_id},
    )
    assert get_message.status_code == 422  # throws unprocessable entity error


def test_add_message_validation_check():
    setup()
    message_response = create_message("one")  # sending the message_id as string
    assert message_response.status_code == 422


def test_add_message_string_with_audio():  # sending string when messagetype is audio and not providing the audio
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]
    message_payload = {
        "chat_id": chat_id,
        "message_type": "audio",
        "message": "hello how are you",
        "audio_output": False,
        "use_rag": False,
    }
    result = client.post(
        f"/v1/message/generate_chat/",
        headers={"Authorization": f"Bearer {token}"},
        data=message_payload,
    )

    assert result.status_code == 400
    assert result.json() == {
        "detail": "No audio file provided"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_create_message_with_audio_output_true():
    response = create_chat()
    assert response.status_code == 201
    chat_id = response.json()["id"]
    message_payload = {
        "chat_id": chat_id,
        "message_type": "text",
        "message": "hello how are you",
        "audio_output": "true",
        "use_rag": False,
    }
    result = client.post(
        f"/v1/message/generate_chat/",
        headers={"Authorization": f"Bearer {token}"},
        data=message_payload,
    )

    assert result.status_code == 201

    assert result.json()["chat_id"] == chat_id

    generated_message = result.json()
    expected_keys = ["id", "chat_id", "message", "starred", "reaction", "audio_file"]

    for key in expected_keys:
        assert (
            key in generated_message
        ), f"Generated message response is missing key '{key}'"
    assert validators.url(generated_message["audio_file"])

    delete_all_users()
