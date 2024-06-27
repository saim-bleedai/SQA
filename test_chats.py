from fastapi.testclient import TestClient
import random
import string
import sys
import time
import json
import requests
from datetime import datetime
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


def test_create_chat():  # smoke test for create chat
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created
    # verfiying responses
    assert response.json()["user_id"] == user_id
    assert response.json()["creator_id"] == creator_id
    assert response.json()["pinned"] == chat_payload["pinned"]
    assert response.json()["muted"] == chat_payload["muted"]

    delete_all_users()


def test_create_chat_with_own_creator():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    user_id = result.json()["user_id"]
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
    assert response.status_code == 400  # chat not created
    assert response.json() == {
        "detail": "Chat not created. Invalid User ID or Creator ID provided."
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_create_chat_with_invalid_user():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    response_delete = client.delete(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

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
    assert response.status_code == 400  # chat not created. THIS NEEDS FIXING

    delete_all_users()


def test_create_chat_with_invalid_creator_id():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    response_delete = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

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
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Chat not created. Invalid User ID or Creator ID provided."
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_add_creator_with_required_fields():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    chat_payload = {  # only sending required fields in payload
        "user_id": user_id,
        "creator_id": creator_id,
    }

    response = client.post(
        "/v1/chat/create",
        headers={"Authorization": f"Bearer {token}"},
        data=chat_payload,
    )
    assert response.status_code == 201  # chat created
    # verfiying responses
    assert response.json()["user_id"] == user_id
    assert response.json()["creator_id"] == creator_id
    assert (
        response.json()["pinned"] == False
    )  # should be false by default unless sent true in payload
    assert response.json()["muted"] == False

    delete_all_users()


def test_add_chat_with_unrequired_fields():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    chat_payload = {  # removing 1 required field
        "creator_id": creator_id,
        "pinned": False,
        "muted": False,
    }

    response = client.post(
        "/v1/chat/create",
        headers={"Authorization": f"Bearer {token}"},
        data=chat_payload,
    )

    assert response.status_code == 422  # chat not created, throws a validation error

    # trying again with missing creator id
    chat_payload = {  # removing 1 required field
        "user_id": user_id,
        "pinned": False,
        "muted": False,
    }

    response = client.post(
        "/v1/chat/create",
        headers={"Authorization": f"Bearer {token}"},
        data=chat_payload,
    )

    assert response.status_code == 422  # chat not created, throws a validation error
    delete_all_users()


def test_get_all_chats_no_chats():  # testing if a valid response is returned if there are no chats
    delete_all_users()
    setup()
    response = client.get(
        f"/v1/chat/all/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204  # should return a no content 204 status code


def test_get_all_chats():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created

    response_get = client.get(
        f"/v1/chat/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": "3"},
    )
    assert response_get.status_code == 200
    response = response_get.json()
    # List of expected top-level keys
    expected_top_level_keys = ["chats", "total_items", "page_num", "total_pages"]

    # Check if all expected top-level keys are in the response
    for key in expected_top_level_keys:
        assert key in response, f"Response missing top-level key '{key}'"

    # List of expected keys within each chat
    expected_chat_keys = [
        "id",
        "user_id",
        "creator_id",
        "pinned",
        "muted",
        "messages",
        "created_at",
        "updated_at",
    ]

    # Check if 'chats' is a list
    assert isinstance(response["chats"], list), "'chats' should be a list"

    # Check the length of the 'chats' list matches 'total_items'
    assert (
        len(response["chats"]) == response["total_items"]
    ), f"Total items on current page ({response['total_items']}) does not match the number of chats returned ({len(response['chats'])})"

    # Check each chat in the list
    for chat in response["chats"]:
        for key in expected_chat_keys:
            assert key in chat, f"Chat missing key '{key}'"

        # Check that 'pinned' and 'muted' are booleans
        assert isinstance(chat["pinned"], bool), f"Chat 'pinned' should be a boolean"
        assert isinstance(chat["muted"], bool), f"Chat 'muted' should be a boolean"

        # Validate the messages field
        assert isinstance(chat["messages"], list), "'messages' should be a list"

    # Pagination checks
    current_page_items = response["total_items"]
    page_num = response["page_num"]
    total_pages = response["total_pages"]

    assert (
        page_num >= 1
    ), f"Page number should be greater than or equal to 1, found {page_num}"
    assert total_pages >= 1, f"Total pages should be at least 1, found {total_pages}"
    assert (
        page_num <= total_pages
    ), f"Page number ({page_num}) exceeds total pages ({total_pages})"

    # If we are not on the last page, 'total_items' should match 'items_per_page'
    items_per_page = 3  # Replace with your actual items per page limit if known

    if page_num < total_pages:
        assert current_page_items == items_per_page
    else:
        # On the last page, 'total_items' can be less than or equal to 'items_per_page'
        assert (
            current_page_items <= items_per_page
        ), f"Number of items on the last page ({current_page_items}) exceeds the expected page limit ({items_per_page})"

    delete_all_users()


def test_get_all_chats_invalid_query():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created

    response_get = client.get(
        f"/v1/chat/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": "-1", "page": "-1"},
    )
    assert response_get.status_code == 400
    delete_all_users()


def test_delete_chat():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created
    chat_id = response.json()["id"]
    time.sleep(1)

    response_delete = client.delete(
        f"/v1/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204
    time.sleep(1)

    # getting the chat
    response = client.get(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204  # does it need to be 404 not found


def test_get_chat():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created
    chat_id = response.json()["id"]
    time.sleep(1)

    get_response = client.get(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == chat_id
    assert get_response.json()["creator_id"] == chat_payload["creator_id"]
    assert get_response.json()["user_id"] == chat_payload["user_id"]
    assert response.json()["pinned"] == chat_payload["pinned"]
    assert response.json()["muted"] == chat_payload["muted"]

    response = get_response.json()
    # List of expected keys
    expected_keys = [
        "id",
        "user_id",
        "creator_id",
        "pinned",
        "muted",
        "messages",
        "created_at",
        "updated_at",
    ]

    # Check if all expected keys are in the response
    for key in expected_keys:
        assert key in response


def test_update_chat():
    # Step 1: Create a creator
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Step 2: Create a user
    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    # Step 3: Create a chat
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
    assert response.status_code == 201  # Chat created successfully
    chat_id = response.json()["id"]
    time.sleep(1)

    # Step 4: Update the chat
    update_payload = {
        "pinned": "true",  # Convert boolean to string
        "muted": "true",  # Convert boolean to string
    }

    update_response = client.put(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,  # Send as URL-encoded form data
    )
    assert (
        update_response.status_code == 201 or update_response.status_code == 200
    )  # Chat updated successfully

    updated_chat = update_response.json()

    # Assertions for updated values
    assert (
        updated_chat["id"] == chat_id
    ), "Updated chat ID does not match the original chat ID"
    assert (
        updated_chat["pinned"] == True
    ), "Chat 'pinned' status was not updated correctly"
    assert (
        updated_chat["muted"] == True
    ), "Chat 'muted' status was not updated correctly"

    # Ensure unchanged fields remain the same
    assert (
        updated_chat["creator_id"] == chat_payload["creator_id"]
    ), "Creator ID should not change"
    assert (
        updated_chat["user_id"] == chat_payload["user_id"]
    ), "User ID should not change"

    # List of expected keys to check
    expected_keys = [
        "id",
        "user_id",
        "creator_id",
        "pinned",
        "muted",
        "created_at",
        "updated_at",
    ]

    # Check if all expected keys are in the response
    for key in expected_keys:
        assert key in updated_chat, f"Updated chat response is missing key '{key}'"
    # verifying the update
    # Step 5: Get the updated chat to verify the changes
    get_response = client.get(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    update_response = client.put(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,  # Send as URL-encoded form data
    )
    assert (
        update_response.status_code == 200 or update_response.status_code == 201
    )  # Chat updated successfully

    updated_chat = update_response.json()

    # Assertions for updated values
    assert (
        updated_chat["id"] == chat_id
    ), "Updated chat ID does not match the original chat ID"
    assert (
        updated_chat["pinned"] == True
    ), "Chat 'pinned' status was not updated correctly"
    assert (
        updated_chat["muted"] == True
    ), "Chat 'muted' status was not updated correctly"

    # Ensure unchanged fields remain the same
    assert (
        updated_chat["creator_id"] == chat_payload["creator_id"]
    ), "Creator ID should not change"
    assert (
        updated_chat["user_id"] == chat_payload["user_id"]
    ), "User ID should not change"

    # List of expected keys to check
    expected_keys = [
        "id",
        "user_id",
        "creator_id",
        "pinned",
        "muted",
        "created_at",
        "updated_at",
    ]

    # Check if all expected keys are in the response
    for key in expected_keys:
        assert key in updated_chat, f"Updated chat response is missing key '{key}'"


def test_update_invalid_chat():
    # Step 1: Create a creator
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Step 2: Create a user
    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    # Step 3: Create a chat
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
    assert response.status_code == 201  # Chat created successfully
    chat_id = response.json()["id"]
    time.sleep(1)

    response_delete = client.delete(
        f"/v1/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

    # Step 4: Update the chat
    update_payload = {
        "pinned": "true",  # Convert boolean to string
        "muted": "true",  # Convert boolean to string
    }

    update_response = client.put(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,  # Send as URL-encoded form data
    )
    assert update_response.status_code == 404
    assert update_response.json() == {
        "detail": "Chat not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_update_post_null_value():  # trying to update post with null value
    setup()
    chat_id = None
    update_payload = {
        "pinned": "true",  # Convert boolean to string
        "muted": "true",  # Convert boolean to string
    }

    update_response = client.put(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,  # Send as URL-encoded form data
    )
    assert update_response.status_code == 422  # throws a unprocessable entity error


def test_create_chat_twice():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201
    user_id1 = response.json()["user_id"]
    chat_id = response.json()["id"]
    creator_id1 = response.json()["creator_id"]

    response = client.post(
        "/v1/chat/create",
        headers={"Authorization": f"Bearer {token}"},
        data=chat_payload,
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == user_id1
    assert response.json()["id"] == chat_id
    assert response.json()["creator_id"] == creator_id1


def test_get_chat_history():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created
    chat_id1 = response.json()["id"]
    time.sleep(1)

    message = create_message(chat_id1)
    assert message.status_code == 201
    chat_id = message.json()["chat_id"]

    result = client.get(
        f"/v1/chat/history/",
        headers={"Authorization": f"Bearer {token}"},
        params={"chat_id": chat_id},
    )
    assert result.status_code == 200
    assert (
        result.json()["id"] == chat_id
    )  # asserting if the retrieved chat has the same id
    chat_history = result.json()
    # Assert the structure of the response
    assert "messages" in chat_history
    messages = chat_history["messages"]
    assert len(messages) == chat_history["total_messages"]

    # Pagination checks
    expected_total_messages = len(messages)
    messages_per_page = expected_total_messages
    expected_total_pages = (
        chat_history["total_messages"] + messages_per_page - 1
    ) // messages_per_page
    assert chat_history["total_pages"] == expected_total_pages

    # Check each message for audio_url if message_type is 'audio'
    for message in messages:
        if message["message_type"] == "audio":
            assert (
                "audio_url" in message
            ), "Audio URL should be present for audio messages"
            # Optional: validate the format of the URL
            assert validators.url(message["audio_url"])


def test_get_invalid_chat_history():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created
    chat_id1 = response.json()["id"]
    time.sleep(1)

    message = create_message(chat_id1)
    assert message.status_code == 201
    chat_id = message.json()["chat_id"]

    response_delete = client.delete(
        f"/v1/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

    result = client.get(
        f"/v1/chat/history/",
        headers={"Authorization": f"Bearer {token}"},
        params={"chat_id": chat_id},
    )
    assert result.status_code == 204  # no content found


def test_get_empty_chat_history():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
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
    assert response.status_code == 201  # chat created
    chat_id = response.json()["id"]
    time.sleep(1)
    result = client.get(
        f"/v1/chat/history/",
        headers={"Authorization": f"Bearer {token}"},
        params={"chat_id": chat_id},
    )
    assert result.status_code == 204
    delete_all_users()


def test_create_chat_with_different_payload():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    chat_payload = {
        "user_id": user_id,
        "creator_id": creator_id,
        "pinned": "true",
        "muted": "true",
    }

    response = client.post(
        "/v1/chat/create",
        headers={"Authorization": f"Bearer {token}"},
        data=chat_payload,
    )
    assert response.status_code == 201  # chat created
    chat_id = response.json()["id"]
    assert response.json()["pinned"] == True
    assert response.json()["muted"] == True
    #verifying if the details were added correctly
    get_response = client.get(
        f"/v1/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert response.json()["pinned"] == True
    assert response.json()["muted"] == True
