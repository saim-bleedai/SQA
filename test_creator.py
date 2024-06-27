from fastapi.testclient import TestClient
import random
import string
import sys
import time
import json
import requests
import os

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
        "username": username,
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


def test_create_creator():  # smoke test for add creator
    setup(generate_token=True)
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    id = response.json()["id"]
    creator_payload["user_id"] = id
    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 201
    delete_all_users()


def test_create_creator_invalid_id():  # adding a creator with an invalid id
    setup()
    creator_payload["user_id"] = "id"
    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 409  # needs to be changed
    delete_all_users()


def test_add_creator_with_invalid_user_id():  # adding a creator with a deleted user id to ensure it doesnot add a creator
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    result = client.delete(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert result.status_code == 200 or result.status_code == 204

    creator_payload["user_id"] = user_id

    result = client.post(  # calling the creator function
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 409  # creator should be created.
    delete_all_users()


def test_create_creator_twice():  # adding a creator twice with the same id. Expected output is that user should not be created
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    id = response.json()["id"]

    creator_payload["user_id"] = id

    result = client.post(  # calling the creator function
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 201  # creator should be created.

    result = client.post(  # calling the function again with the same user id
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 409  # creator should not be created.
    delete_all_users()


def test_get_creator():  # smoke test of get specific creator
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    id = response.json()["id"]

    creator_payload["user_id"] = id

    result = client.post(  # calling the creator function
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 201  # creator should be created.
    creator_id = result.json()["creator_id"]
    get_result = client.get(  # getting the same creator which was created
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 200

    creator_get_id = get_result.json()["creator_id"]

    assert (
        creator_get_id == creator_id
    )  # checking if the id in the add response and get response are same
    delete_all_users()


def test_get_creator_by_creator_id():
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    user_id = response.json()["id"]

    creator_payload["user_id"] = user_id

    result = client.post(  # calling the creator function
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 201  # creator should be created.
    creator_id = result.json()["creator_id"]
    get_result = (
        client.get(  # getting the same creator which was created but by using user id
            f"/v1/creator/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )
    )
    assert get_result.status_code == 200

    creator_get_id = get_result.json()["creator_id"]

    assert (
        creator_get_id == creator_id
    )  # checking if the id in the add response and get response are same
    delete_all_users()


def test_delete_and_get_deleted_creator():  # testing the behavior of the api if we are requesting for a deleted creator. Expected output is that it returns a 404 response
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    user_id = response.json()["id"]
    creator_payload["user_id"] = user_id

    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    get_result = client.get(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 404
    assert get_result.json() == {"detail": "Creator not found"}
    delete_all_users()


def test_follow_own_creator():  # testing if user can follow own creator. Expected output is that user should not be allowed to follow their own created user
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    user_id = response.json()["id"]
    creator_payload["user_id"] = user_id
    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    follow_payload = {"user_id": user_id, "creator_id": creator_id}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_result.status_code == 400
    result_json = follow_result.json()  # Parse JSON response
    detail_message = result_json.get("detail", "")
    assert (
        detail_message == "Creator follow request failed"
    )  # checking if it returns a valid response
    delete_all_users()


def test_follow_multiple_creators():  # test case to check if it allows users to follow more than one creator
    setup()
    response_1 = client.post(  # create user 1
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response_1.status_code == 201
    user_id_1 = response_1.json()["id"]

    setup()
    response_2 = client.post(  # create user 2
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    assert response_2.status_code == 201

    user_id_2 = response_2.json()["id"]

    # create a creator with user_id_2
    creator_payload["user_id"] = user_id_2

    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    assert result.status_code == 201
    creator_id_1 = result.json()["creator_id"]

    # user_1 should be able to follow creator_id_1
    follow_payload = {"user_id": user_id_1, "creator_id": creator_id_1}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_result.status_code == 200
    result_json = follow_result.json()  # Parse JSON response
    detail_message = result_json.get("detail", "")
    assert detail_message == "Creator followed successfully"

    setup()
    response_3 = client.post(  # create user 1
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    assert response_3.status_code == 201
    user_id_3 = response_3.json()["id"]
    # create a creator with user_id_2
    creator_payload["user_id"] = user_id_3

    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    assert result.status_code == 201
    creator_id_2 = result.json()["creator_id"]

    # user_1 should be able to follow creator_id_2
    follow_payload = {"user_id": user_id_1, "creator_id": creator_id_2}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_result.status_code == 200
    result_json = follow_result.json()  # Parse JSON response
    detail_message = result_json.get("detail", "")
    assert (
        detail_message == "Creator followed successfully"  # returns a success message
    )
    delete_all_users()


def test_follow_invalid_creator_with_invalid_id():
    setup()
    response_1 = client.post(  # create user 1
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response_1.status_code == 201
    user_id_1 = response_1.json()["id"]

    setup()
    response_2 = client.post(  # create user 2
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response_2.status_code == 201

    user_id_2 = response_2.json()["id"]

    # create a creator with user_id_2
    creator_payload["user_id"] = user_id_2

    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    assert result.status_code == 201
    creator_id_1 = result.json()["creator_id"]

    result_delete = client.delete(  # delete user_1
        f"/v1/user/{user_id_1}", headers={"Authorization": f"Bearer {token}"}
    )
    assert result_delete.status_code == 200 or result_delete.status_code == 204

    follow_payload = {"user_id": user_id_1, "creator_id": creator_id_1}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert (
        follow_result.status_code == 409
    )  # need to change this, this is assertion error, also it returns a message that is creator is already followed
    delete_all_users()


def test_follow_invalid_creator():
    setup()
    response_1 = client.post(  # create user 1
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response_1.status_code == 201
    user_id_1 = response_1.json()["id"]

    setup()
    response_2 = client.post(  # create user 2
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response_2.status_code == 201

    user_id_2 = response_2.json()["id"]

    # create a creator with user_id_2
    creator_payload["user_id"] = user_id_2

    result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    assert result.status_code == 201
    creator_id_1 = result.json()["creator_id"]
    # deleting the creator
    delete_result = client.delete(
        f"/v1/creator/{creator_id_1}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200
    # following the deleted creator and asserting the response
    follow_payload = {"user_id": user_id_1, "creator_id": creator_id_1}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_result.status_code == 400
    delete_all_users()


def test_update_creator_invalid_id():  # trying to update an invalid creator that doesnot exist in db to check the response of the api
    # First, setup and create a new user and creator
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    user_id = response.json()["id"]
    creator_payload["user_id"] = user_id

    # Creating the creator with initial details
    create_result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_result.status_code == 201
    creator_id = create_result.json()["creator_id"]
    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    update_payload = {
        "name": "Updated Name",  # Changing the name for the test
        "description": "Updated Description",
        "summary": "Updated Summary",
        # Ensure to include all other necessary fields from the original creation to preserve unchanged data
    }

    # Calling the update API endpoint with the new payload
    update_result = client.put(
        f"/v1/creator/{creator_id}",  # Specific endpoint for updating a creator
        data=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Asserting that the update was not successful and api returns a valid response and error message
    assert update_result.status_code == 404
    result_json = update_result.json()  # Parse JSON response
    detail_message = result_json.get("detail", "")
    assert detail_message == "Creator not found"  # returns a success message
    delete_all_users()


def test_get_all_creators_pagination():
    # Setup: Assuming you may need a valid token and creators are already added for testing
    setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    user_id = response.json()["id"]
    creator_payload["user_id"] = user_id

    # Creating the creator with initial details
    create_result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_result.status_code == 201

    # Define test parameters
    page = 1
    limit = 2

    # Fetching a specific page with a limit
    response = client.get(
        f"/v1/creator/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": page, "limit": limit},
    )

    assert response.status_code == 200 or response.status_code == 204

    if response.status_code == 200:
        response_data = response.json()

        # Assert the basic structure of the response
        assert "creators" in response_data, "Missing 'creators' in response"
        assert "total_items" in response_data, "Missing 'total_items' in response"
        assert "page_num" in response_data, "Missing 'page_num' in response"
        assert "total_pages" in response_data, "Missing 'total_pages' in response"

        # Basic assertions about pagination
        assert (
            len(response_data["creators"]) == response_data["total_items"]
        ), "Total items does not match number of items returned on this page"
        assert (
            response_data["page_num"] == page
        ), "Page number does not match the requested page"

        # Check the number of items and page information
        if response_data["page_num"] < response_data["total_pages"]:
            assert (
                len(response_data["creators"]) == limit
            ), "Items per page does not match the 'limit' when not on the last page"
        else:
            # For the last page, items can be less than or equal to the limit
            assert (
                len(response_data["creators"]) <= limit
            ), "Items on the last page are more than the limit"

        # Assert content structure of each creator
        for creator in response_data["creators"]:
            assert all(
                key in creator
                for key in [
                    "creator_id",
                    "user_id",
                    "name",
                    "description",
                    "profile_pic",
                    "cover_pic",
                    "summary",
                    "personality",
                    "experience",
                    "habits",
                    "greeting_message",
                    "voice_preset",
                    "created_at",
                    "updated_at",
                ]
            ), "Missing expected keys in some creator entries"

    delete_all_users()


def test_unfollow_creator():
    setup()
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    time.sleep(1)

    user_id1 = response.json()["id"]

    creator_payload["user_id"] = user_id1

    result1 = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result1.status_code == 201
    creator_id1 = result1.json()["creator_id"]

    # Create second user and creator
    setup()
    response2 = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response2.status_code == 201

    user_id2 = response2.json()["id"]

    # First user follows the second user's creator
    follow_payload = {"user_id": user_id2, "creator_id": creator_id1}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_result.status_code == 200

    # now unfollow the creator
    follow_payload = json.dumps(follow_payload)

    url = "http://localhost:8000/v1/creator/unfollow/"  # Adjust the URL to where your app is hosted
    headers = {
        "Authorization": f"Bearer {token}",  # Ensure your token is correctly included
        "Content-Type": "application/json",
    }
    print("P1", follow_payload)

    # Sending a DELETE request with a JSON body
    response = requests.delete(
        url,
        headers=headers,
        data=follow_payload,
    )
    print("R1", response.json())

    assert response.status_code == 200  # needs to be worked on
    delete_all_users()


def test_get_creator_chats():  # smoke test for get creator chats
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # create another user
    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]
    chat_payload = {
        "user_id": user_id,
        "creator_id": creator_id,
    }
    time.sleep(1)
    response_chat = client.post(
        "/v1/chat/create",
        data=chat_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)

    assert response_chat.status_code == 201  # chat should be created

    # Get the chat ID
    chat_id = response_chat.json()["id"]

    # Getting a chat
    response_get_chat = client.get(
        "/v1/creator/chats/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "creator_id": creator_id,
        },
    )
    assert response_get_chat.status_code == 200 or response_get_chat.status_code == 204
    response = response_get_chat.json()

    # Pagination checks
    assert response["total_items"] >= len(response["chats"])
    assert response["page_num"] == 1
    assert response["total_pages"] >= 1

    # Chat object checks
    expected_keys_top_level = [
        "creator_id",
        "chats",
        "total_items",
        "page_num",
        "total_pages",
    ]

    # Check if all expected top-level keys are in the response
    for key in expected_keys_top_level:
        assert key in response

    # Check if 'chats' is a list and contains expected keys
    expected_keys_chat = [
        "id",
        "user_id",
        "creator_id",
        "pinned",
        "muted",
        "messages",
        "created_at",
        "updated_at",
    ]

    assert isinstance(response["chats"], list)

    for chat in response["chats"]:
        for key in expected_keys_chat:
            assert key in chat
    delete_all_users()


def test_get_chats_with_invalid_creator():  # getting a chat with a deleted creator to test if chat associated with that creator is deleted or not
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # create another user
    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]
    chat_payload = {
        "user_id": user_id,
        "creator_id": creator_id,
    }
    time.sleep(1)
    response_chat = client.post(
        "/v1/chat/create",
        data=chat_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)

    assert response_chat.status_code == 201  # chat should be created

    # Get the chat ID
    chat_id = response_chat.json()["id"]

    # deleting the creator
    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    # Getting a chat
    response_get_chat = client.get(
        "/v1/creator/chats/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "creator_id": creator_id,
        },
    )
    assert response_get_chat.status_code == 404
    delete_all_users()


def test_get_creator_reports():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    report_payload = {
        "reporter_id": user_id,
        "creator_id": creator_id,
        "description": None,
        "category": None,
    }

    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,
    )
    assert response.status_code == 201  # report created
    time.sleep(1)
    response = client.get(
        f"/v1/creator/reports/",
        params={"creator_id": creator_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    result = response.json()

    expected_keys_top_level = [
        "creator_id",
        "reports",
        "total_items",
        "page_num",
        "total_pages",
    ]

    # Pagination checks
    assert result["total_items"] >= len(
        result["reports"]
    ), "Total items count mismatch with the number of reports returned"
    assert result["page_num"] == 1, "Page number should be 1 for the first page test"
    assert result["total_pages"] >= 1, "Total pages should be at least 1"

    # Check if all expected top-level keys are in the response
    for key in expected_keys_top_level:
        assert key in result

    # Check if 'reports' is a list and contains expected keys
    expected_keys_report = [
        "id",
        "reporter_id",
        "creator_id",
        "description",
        "category",
        "created_at",
        "updated_at",
    ]

    assert isinstance(result["reports"], list), "'reports' should be a list"

    for report in result["reports"]:
        for key in expected_keys_report:
            assert key in report, f"Report missing key '{key}'"

    delete_all_users()


def test_get_invalid_creator_reports():  # getting reports of a deleted creator, report should automatically be deleted
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    report_payload = {
        "reporter_id": user_id,
        "creator_id": creator_id,
        "description": None,
        "category": None,
    }

    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,
    )
    assert response.status_code == 201  # report created
    time.sleep(1)

    # delete the creator

    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200
    time.sleep(1)

    response = client.get(
        f"/v1/creator/reports/",
        params={"creator_id": creator_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Creator not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_update_creator_with_files():
    # Setup and create a new user and creator
    setup()  # Ensure this function is properly defined to set up the environment
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    creator_payload["user_id"] = user_id

    # Creating the creator with initial details
    create_result = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_result.status_code == 201
    creator_id = create_result.json()["creator_id"]

    # Prepare file paths
    base_path = "fanbai_ss"  # Adjust base path to your file location
    profile_pic_path = os.path.join(base_path, "add1.jpg")
    cover_pic_path = os.path.join(base_path, "add1.jpg")
    voice_preset_path = os.path.join(base_path, "21.wav")

    # Ensure files exist
    assert os.path.exists(profile_pic_path), "Profile pic file does not exist"
    assert os.path.exists(cover_pic_path), "Cover pic file does not exist"
    assert os.path.exists(voice_preset_path), "Voice preset file does not exist"

    # Open files in binary mode for upload
    with open(profile_pic_path, "rb") as profile_file, open(
        cover_pic_path, "rb"
    ) as cover_file, open(voice_preset_path, "rb") as voice_file:
        files = {
            "profile_pic": ("profile_pic.jpg", profile_file, "image/jpeg"),
            "cover_pic": ("cover_pic.jpg", cover_file, "image/jpeg"),
            "voice_preset": ("voice_preset.mp3", voice_file, "audio/mpeg"),
        }
        update_payload = {
            "name": "Updated Name",
            "description": "Updated Description",
            "summary": "Updated Summary",
        }

        # Calling the update API endpoint with the new payload and files
        update_result = client.put(
            f"/v1/creator/{creator_id}",
            data=update_payload,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Asserting that the update was successful
        assert update_result.status_code == 200

        update_response_data = update_result.json()
        assert update_response_data["name"] == "Updated Name"
        assert update_response_data["description"] == "Updated Description"
        assert update_response_data["summary"] == "Updated Summary"

        # Capture URLs from the update response
        profile_pic_url = update_response_data["profile_pic"]
        cover_pic_url = update_response_data["cover_pic"]
        voice_preset_url = update_response_data["voice_preset"]

    # Optionally, retrieve the updated creator to verify changes
    get_result = client.get(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 200
    updated_creator = get_result.json()
    assert updated_creator["name"] == "Updated Name"
    assert updated_creator["description"] == "Updated Description"
    assert updated_creator["summary"] == "Updated Summary"
    assert updated_creator["profile_pic"] == profile_pic_url
    assert updated_creator["cover_pic"] == cover_pic_url
    assert updated_creator["voice_preset"] == voice_preset_url

    delete_all_users()


def test_get_creator_posts():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
        "explore_post": True,
        "images": [],
    }

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,  # Send the payload as form data
    )
    assert response.status_code == 201
    time.sleep(1)

    # getting the creator posts

    result = client.get(
        f"/v1/creator/posts/",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert result.status_code == 200
    assert result.json()["creator_id"] == creator_id
    response_data = result.json()
    # Check pagination values
    assert response_data["total_items"] == len(response_data["posts"])
    assert response_data["page_num"] >= 1
    assert response_data["total_pages"] >= 1
    delete_all_users()


def test_get_invalid_creator_posts():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
        "explore_post": True,
        "images": [],
    }

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,  # Send the payload as form data
    )
    assert response.status_code == 201
    time.sleep(1)
    # deleting the creator
    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200
    time.sleep(1)

    # getting the creator posts

    result = client.get(
        f"/v1/creator/posts/",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert result.status_code == 404
    assert result.json() == {"detail": "Creator not found"}
    delete_all_users()


def test_get_creator_posts_no_posts():  # testing the result when there are no posts to get
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    result = client.get(
        f"/v1/creator/posts/",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert result.status_code == 204
    delete_all_users()


def test_create_creator_required_field_check():
    setup()
    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]
    creator_payload["user_id"] = user_id
    creator_payload["username"] = (
        None  # sending the username which is a required field as none
    )

    result_creator = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result_creator.status_code == 422
    delete_all_users()


def test_update_creator_username():
    result = create_creator()
    assert result.status_code == 201
    username = result.json()["username"]

    # create a second creator
    creator_2 = create_creator()
    assert creator_2.status_code == 201
    creator_id = creator_2.json()["creator_id"]
    time.sleep(1)
    update_payload = {"username": username}
    update_result = client.put(
        f"/v1/creator/{creator_id}",  # Specific endpoint for updating a creator
        data=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_result.status_code == 409  # needs to be fixed


def test_create_creator_with_taken_username():
    result = create_creator()
    assert result.status_code == 201
    username = result.json()["username"]
    creator_payload["username"] = username
    response = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Creator already exists"}
    delete_all_users()



