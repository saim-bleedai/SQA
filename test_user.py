from fastapi.testclient import TestClient
import random
import string
import sys
import json
import time
import pytest
import os

sys.path.append("./app/")

from main import app

client = TestClient(app)

payload = None
token = None


def setup(generate_token=False):
    if generate_token:
        get_token()

    return get_random_payload()


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

    payload = {
        "id": id,
        "username": username,
        "name": name,
        "email": email,
        "interests": interests,
        "date_of_birth": "12-jan-1990",
    }

    return payload


def get_payload_with_required_fields():
    new_payload = get_random_payload()
    return {
        "id": new_payload["id"],
        "username": new_payload["username"],
        "email": new_payload["email"],
        "date_of_birth": new_payload["date_of_birth"],
    }


def get_payload_with_required_fields_missing():
    new_payload = get_random_payload()
    return {"interests": new_payload["interests"], "name": new_payload["name"]}


def get_payload_with_email_in_lower():
    new_payload = get_random_payload()
    return {
        "id": new_payload["id"],
        "username": new_payload["username"],
        "email": "saim@gmail.com",
        "date_of_birth": new_payload["date_of_birth"],
    }


def get_payload_with_email_in_upper():
    new_payload = get_random_payload()
    return {
        "id": new_payload["id"],
        "username": new_payload["username"],
        "email": "SAIM@GMAIL.COM",
        "date_of_birth": new_payload["date_of_birth"],
    }


def get_creator_payload():
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    creator_name = "test-creator" + random_str
    username = "test-name" + random_str
    description = "testdescription" + random_str
    summary = "test summary" + random_str
    personality = "test-personality" + random_str
    experience = "test experience" + random_str
    habits = "test habits" + random_str + "," + random_str + "," + random_str
    greeting_message = "greeting message" + random_str

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
    return creator_payload


def test_create_user():

    payload = setup(generate_token=True)

    print("P1", payload)

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    print("R1", response.json())
    assert response.status_code == 201
    delete_all_users()


def test_get_user():

    new_payload = setup()

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)

    assert response.status_code == 201

    if new_payload:
        user_id = new_payload["id"]
        response = client.get(
            f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        user_data = response.json()

    else:
        assert False
    delete_all_users()


def test_update_user():

    new_payload = setup()

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)

    assert response.status_code == 201

    if new_payload:
        user_id = new_payload["id"]
        data = {"name": "Updated Name"}
        response = client.put(
            f"/v1/user/{user_id}",
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
    else:
        assert False
    delete_all_users()


def test_get_all_user_chats():

    payload = setup()
    time.sleep(2)

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)

    assert response.status_code == 201

    if payload:
        user_id = payload["id"]
        response = client.get(
            f"/v1/user/chats/",
            params={"user_id": user_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200 or response.status_code == 204
    else:
        assert False
    delete_all_users()


def test_get_all_user_reports():

    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)

    assert response.status_code == 201

    if payload:
        user_id = payload["id"]
        response = client.get(
            f"/v1/user/reports/",
            params={"user_id": user_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200 or response.status_code == 204
    else:
        assert False
    delete_all_users()


def test_remove_user_profile_pic():
    delete_all_users()
    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    print("R10", response.json())
    assert response.status_code == 201
    if payload:
        user_id = payload["id"]
        response = client.delete(
            f"/v1/user/{user_id}/profile_pic",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
    else:
        assert False
    delete_all_users()


def test_delete_user():
    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    print("R11", response.json())
    assert response.status_code == 201

    user_id = response.json()["id"]

    response = client.delete(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    delete_all_users()


def test_create_user_same_email():  # testing if it is allowing more than one users to be created with the same email. Expected output should be that user is not created and a valid error message is returned
    delete_all_users()
    payload = setup()

    response = client.post(
        "/v1/user/create",
        data=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)

    # Ensure the user is created
    assert response.status_code == 201  # user should be created as this is a new user
    created_user_email = response.json()["email"]

    # Attempt to create another user with the same email
    payload = setup()

    payload["email"] = created_user_email
    print("P10", payload)

    result = client.post(
        "/v1/user/create",
        data=payload,
        headers={"Authorization": f"Bearer {token}"},  # calling the endpoint again
    )

    # Ensure the appropriate error response is returned
    result_json = result.json()  # Parse JSON response
    detail_message = result_json.get("detail", "")
    assert result.status_code == 409
    assert detail_message == "User already exists"
    delete_all_users()


def test_create_user_required_field_check():  # Testing if data is saved when only required feilds are sent in payload.

    setup()

    new_payload = get_payload_with_required_fields()

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    print("R14", response.json())
    time.sleep(1)

    # Assert the response as per your test logic
    assert response.status_code == 201
    setup()

    new_payload = get_payload_with_required_fields_missing()
    print("P12", new_payload)

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    print("R123", response.json())
    assert response.status_code == 422

    delete_all_users()


def test_create_user_email_validation():  # Testing if email and username is saved in lowercases.
    setup()  # Initialize payload and token

    new_payload = get_payload_with_email_in_lower()
    # Generate a specific payload from initialized global payload

    print("P13", new_payload)

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R16", response.json())

    # Assert the response as per your test logic
    assert response.status_code == 201

    setup()

    new_payload = get_payload_with_email_in_upper()
    print("P14", new_payload)
    result = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R17", result.json())

    assert result.status_code == 409  # user should not be created


def test_create_user_invalid_date():  # testing to see if user is created when an invalid date is sent in payload

    new_payload = setup()

    new_payload["date_of_birth"] = "string yy mm"
    print("P15", new_payload)

    result = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},  # calling the endpoint again
    )
    time.sleep(1)
    print("R18", result.json())

    # Ensure the appropriate error response is returned
    result_json = result.json()  # Parse JSON response
    detail_message = result_json.get("detail", "")
    assert result.status_code == 400
    assert detail_message == "Incorrect data format, should be DD-MMM-YYYY"
    delete_all_users()


def test_create_user_api_falsetoken():  # testing if api will hit if wrong token or no token is provided. Expected output is that a 401 unauthorized stauscode is returned
    new_payload = setup()
    token_1 = "newtoken"  # generating a false token
    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert response.status_code == 401


def test_create_user_api_notoken():  # testing to see of api will return response of 401 unauthorized if no token is provided
    new_payload = setup()

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer "},  # not sending token
    )
    assert response.status_code == 401


def test_create_user_invalid_email_format():  # testing to see if there is field validation on email field and if it accepts incorrect emal format. Expected output should be that it throws a 422 error
    new_payload = setup()

    new_payload["email"] = "invalid email format"
    print("P18", new_payload)

    result = client.post(
        "/v1/user/create",
        data=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    print("R18", result.json())

    assert result.status_code == 422


def test_update_user_username():  # updating the username to a username that already exists in db. Expected output is that it should not create a user
    delete_all_users()
    new_payload = setup()

    print("P19", new_payload)

    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},  # creating user1
    )
    time.sleep(1)
    print("R19", response.json())
    assert response.status_code == 201
    username = response.json()["username"]

    my_payload = setup()

    print("P20", my_payload)
    result = client.post(
        "/v1/user/create",
        data=my_payload,
        headers={"Authorization": f"Bearer {token}"},  # creating  user2
    )
    time.sleep(1)
    print("R20", result.json())
    assert result.status_code == 201
    id_1 = result.json()[
        "id"
    ]  # updating user2 username with the username of user 1. Expected output is that returns a 409 error.

    if my_payload:
        user_id = id_1
        data = {"username": username}
        response = client.put(
            f"/v1/user/{user_id}",
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )

        print("R21", response.json())
        assert response.status_code == 409

    else:
        assert False
    delete_all_users()


def test_delete_user_invalid_id():
    new_payload = setup()

    print("P21", new_payload)
    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R22", response.json())
    assert response.status_code == 201
    if new_payload:
        user_id = "random id"  # ge a random id
        response = client.delete(
            f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
    else:
        assert False
    delete_all_users()


def test_get_user_invalid_id():
    new_payload = setup()

    print("P23", new_payload)
    if new_payload:
        user_id = "random id"
        response = client.get(
            f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
    else:
        assert False


def test_get_user_keys_check():
    new_payload = setup()

    print("P24", new_payload)
    response = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R23", response.json())
    assert response.status_code == 201
    id_1 = response.json()["id"]
    expected_keys = [
        "id",
        "username",
        "name",
        "email",
        "creator_id",
        "creator_status",
        "profile_pic",
        "free_credits",
        "paid_credits",
        "created_at",
        "updated_at",
    ]
    if new_payload:
        user_id = id_1
        response = client.get(
            f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )

        response_json = response.json()
        for key in expected_keys:
            assert key in response_json, f"Key '{key}' not found in the response"

        assert response.status_code == 200

    else:
        assert False
    delete_all_users()


def test_get_deleted_user():  # deleting a user and then getting its id
    payload = setup()

    print("P24", payload)
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    print("R24", response.json())
    assert response.status_code == 201

    id_1 = response.json()["id"]
    user_id = id_1
    client.delete(f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    time.sleep(1)
    result = client.get(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert result.status_code == 404


def test_get_all_test_all_keys():  # testing if all keys are returned in the user list
    delete_all_users()
    payload = setup()
    print("P30", payload)

    result = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R30", result.json())

    time.sleep(1)
    assert result.status_code == 201

    response = client.get(
        f"/v1/user/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1},
    )

    response_json = response.json()

    expected_user_keys = [
        "id",
        "username",
        "name",
        "email",
        "profile_pic",
        "free_credits",
        "paid_credits",
        "created_at",
        "updated_at",
    ]

    for user in response_json["users"]:

        for key in expected_user_keys:
            assert key in user, f"Key '{key}' not found in user: {user}"
    delete_all_users()


def test_get_all_test_page_number():
    delete_all_users()
    payload = setup()

    print("P31", payload)
    result = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R31", result.json())
    time.sleep(1)
    assert result.status_code == 201

    response = client.get(
        f"/v1/user/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "limit": 3
        },  # not giving a page number, expected output is that it automatically returns page 1
    )
    assert response.status_code == 200
    assert response.json()["page_num"] == 1
    delete_all_users()


def test_get_all_invalid_query():
    setup()
    response = client.get(
        f"/v1/user/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "page": -1,
            "limit": -1,
        },  # giving a page number in negative, expected output is that it returns a 422 error
    )

    assert response.status_code == 400
    delete_all_users()


def test_get_followed_creators():
    delete_all_users()
    payload = setup()

    # Create first user and creator
    response1 = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)
    print("R32", response1.json())
    assert response1.status_code == 201

    user_id1 = response1.json()["id"]
    creator_payload = get_creator_payload()
    creator_payload["user_id"] = user_id1

    result1 = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result1.status_code == 201
    creator_id1 = result1.json()["creator_id"]
    print("new1212", result1.json())

    # Create second user and creator
    payload = setup(generate_token=True)
    print("P33", payload)

    response2 = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R33", response2.json())
    assert response2.status_code == 201

    user_id2 = response2.json()["id"]
    setup()
    creator_payload_2 = get_creator_payload()
    creator_payload_2["user_id"] = user_id2
    print("S1", creator_payload_2)

    result2 = client.post(
        "/v1/creator/create",
        data=creator_payload_2,
        headers={"Authorization": f"Bearer {token}"},
    )
    print("mys", result2.json())
    assert result2.status_code == 201
    creator_id2 = result2.json()["creator_id"]

    # First user follows the second user's creator
    follow_payload = {"user_id": user_id1, "creator_id": creator_id2}

    follow_result = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_result.status_code == 200

    # Get followed creators for the first user
    get_followed_payload = {"user_id": user_id1, "page": 1, "limit": 10}
    get_followed_result = client.get(
        f"/v1/user/creators/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "page": 1,
            "limit": 10,
            "user_id": user_id1,
        },
    )
    assert get_followed_result.status_code == 200

    response_json = get_followed_result.json()
    followed_creators = response_json["creators"]

    # Additional assertions to verify response structure and data
    assert response_json["total_items"] == 1
    assert response_json["page_num"] == 1
    assert response_json["total_pages"] == 1

    # Verify the specific followed creator details
    followed_creator = followed_creators[0]
    assert followed_creator["creator_id"] == creator_id2
    assert followed_creator["user_id"] == user_id2
    assert followed_creator["name"] == creator_payload_2["name"]
    delete_all_users()


def test_followed_creators_pagination():
    delete_all_users()
    payload = setup()
    print("P34", payload)

    # Create a user
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R34", response.json())
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Create a new user and set up the creator payload
    payload = setup()
    print("P35", payload)
    user_create_response = client.post(
        "/v1/user/create",
        data=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    print("R35", user_create_response.json())
    assert user_create_response.status_code == 201

    creator_user_id = user_create_response.json()["id"]
    creator_payload = get_creator_payload()
    creator_payload["user_id"] = creator_user_id
    print("P35", creator_payload)

    # Create a creator
    creator_create_response = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R36", creator_create_response.json())
    assert creator_create_response.status_code == 201
    creator_id = creator_create_response.json()["creator_id"]

    # Follow the creator
    follow_payload = {"user_id": user_id, "creator_id": creator_id}
    follow_response = client.post(
        "/v1/creator/follow/",
        data=follow_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_response.status_code == 200

    # Test pagination
    page_size = 1

    # Check the first page
    get_followed_payload = {"user_id": user_id, "page": 1, "limit": page_size}
    get_followed_result = client.get(
        f"/v1/user/creators/",
        headers={"Authorization": f"Bearer {token}"},
        params=get_followed_payload,
    )
    assert get_followed_result.status_code == 200
    response_json = get_followed_result.json()

    assert len(response_json["creators"]) == page_size
    assert response_json["total_items"] == 1
    assert response_json["page_num"] == 1
    assert response_json["total_pages"] == 1

    # Check the second page (should be empty)
    get_followed_payload["page"] = 2
    get_followed_result = client.get(
        f"/v1/user/creators/",
        headers={"Authorization": f"Bearer {token}"},
        params=get_followed_payload,
    )
    assert get_followed_result.status_code == 204
    delete_all_users()


def test_get_all_the_users():
    response = client.get(
        f"/v1/user/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1000},
    )
    if response.status_code == 200:
        users = response.json()["users"]
        for user in users:
            user_id = user["id"]
            client.delete(
                f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
            )
    assert response.status_code == 200 or response.status_code == 204
    delete_all_users()


def test_get_all_followed_creator_invalid_query():
    delete_all_users()
    payload = setup()
    print("P37", payload)

    # Create a user
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R37", response.json())
    assert response.status_code == 201
    user_id = response.json()["id"]
    response = client.get(
        f"/v1/user/creators/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": user_id,
            "page": -1,
            "limit": -1,
        },  # giving a page number in negative, expected output is that it returns a 422 error
    )
    assert response.status_code == 400
    delete_all_users()


def test_get_user_chats():  # smoke test for get user chats
    delete_all_users()
    payload = setup()
    print("P38", payload)

    # Create a user
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R38", response.json())
    assert response.status_code == 201
    user_id = response.json()["id"]
    response = client.get(
        f"/v1/user/chats/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": user_id,
        },
    )
    assert response.status_code == 200 or response.status_code == 204
    delete_all_users()


def test_get_invalid_user_chat():  # trying to get a deleted user chat
    delete_all_users()
    payload = setup()
    print("P39", payload)

    # Create a user
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    print("R39", response.json())
    assert response.status_code == 201

    user_id = response.json()["id"]
    client.delete(f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    result = client.get(
        f"/v1/user/chats/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": user_id,
        },
    )

    assert result.status_code == 404
    delete_all_users()


def test_get_user_chats_keys():
    delete_all_users()
    payload = setup()
    print("P40", payload)

    # Create a user
    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )

    print("R41", response.json())

    assert response.status_code == 201
    user_id = response.json()["id"]

    new_payload = setup()
    print("P41", new_payload)
    # Create another user
    result = client.post(
        "/v1/user/create",
        data=new_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    print("R41", result)

    assert result.status_code == 201

    newuser_id = result.json()["id"]
    creator_payload = get_creator_payload()
    creator_payload["user_id"] = user_id
    print("P42", creator_payload)

    # Create a creator
    creator_create_response = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R43", creator_create_response.json())
    assert creator_create_response.status_code == 201

    # Get the creator ID
    creator_id = creator_create_response.json()["creator_id"]

    # Create a chat
    chat_payload = {
        "user_id": newuser_id,
        "creator_id": creator_id,
    }
    print("R44", chat_payload)
    response_chat = client.post(
        "/v1/chat/create",
        data=chat_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    time.sleep(1)
    print("R45", response_chat.json())

    assert response_chat.status_code == 201  # chat should be created

    # Get the chat ID
    chat_id = response_chat.json()["id"]

    # Getting a chat
    response_get_chat = client.get(
        "/v1/user/chats/",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "user_id": newuser_id,
        },
    )
    assert response_get_chat.status_code == 200

    # Accessing the required fields from the JSON response
    chat = response_get_chat.json()["chats"][0]

    # List of required keys
    required_keys = [
        "id",
        "user_id",
        "creator_id",
        "pinned",
        "muted",
        "messages",
        "created_at",
        "updated_at",
    ]

    # Checking if all required keys are present in the chat
    for key in required_keys:
        assert key in chat, f"Missing key: {key}"

    # Extracting values
    chat_2_id = chat["id"]
    user_2_id = chat["user_id"]
    creator_2_id = chat["creator_id"]

    # Assertions
    assert user_2_id == newuser_id
    assert chat_2_id == chat_id
    assert creator_2_id == creator_id

    delete_all_users()


def test_get_user_reports():
    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)

    assert response.status_code == 201

    user_id1 = response.json()["id"]
    creator_payload = get_creator_payload()
    creator_payload["user_id"] = user_id1

    result1 = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result1.status_code == 201

    creator_id = result1.json()["creator_id"]

    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)

    assert response.status_code == 201

    user_id2 = response.json()["id"]

    report_payload = {
        "reporter_id": user_id2,
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
        f"/v1/user/reports/",
        params={"user_id": user_id2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    result = response.json()

    expected_keys_top_level = [
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


def test_get_invalid_user_reports():  # getting reports of a deleted user, report should automatically be deleted
    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)

    assert response.status_code == 201

    user_id1 = response.json()["id"]
    creator_payload = get_creator_payload()
    creator_payload["user_id"] = user_id1

    result1 = client.post(
        "/v1/creator/create",
        data=creator_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result1.status_code == 201

    creator_id = result1.json()["creator_id"]

    payload = setup()

    response = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )
    time.sleep(1)

    assert response.status_code == 201

    user_id2 = response.json()["id"]

    report_payload = {
        "reporter_id": user_id2,
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

    delete_result = client.delete(
        f"/v1/user/{user_id2}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200
    time.sleep(1)

    response = client.get(
        f"/v1/user/reports/",
        params={"user_id": user_id2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "User not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_all_users_no_items():
    delete_all_users()
    time.sleep(1)
    response = client.get(
        f"/v1/user/all/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_get_all_followed_no_items():
    payload = setup()

    # Create first user and creator
    response1 = client.post(
        "/v1/user/create", data=payload, headers={"Authorization": f"Bearer {token}"}
    )

    assert response1.status_code == 201

    user_id1 = response1.json()["id"]
    response = client.get(
        f"/v1/user/creators/",
        headers={"Authorization": f"Bearer {token}"},
        params={"user_id": user_id1},
    )
    assert response.status_code == 204


def test_remove_profile_pic():

    setup()
    base_path = "fanbai_ss"  # Adjust base path to your file location
    profile_pic_path = os.path.join(base_path, "add1.jpg")
    assert os.path.exists(profile_pic_path), "Profile pic file does not exist"

    # Open the file outside the 'with' statement
    profile_file = open(profile_pic_path, "rb")
    user_files = {"profile_pic": ("profile_pic.jpg", profile_file, "image/jpeg")}

    try:
        response = client.post(
            "/v1/user/create",
            data=payload,
            headers={"Authorization": f"Bearer {token}"},
            files=user_files,
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        profile_pic = response.json()["profile_pic"]

        # Verify if profile pic URL is returned
        response_get = client.get(
            f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response_get.status_code == 200
        assert response_get.json()["profile_pic"] == profile_pic

        # Removing the profile pic
        delete_result = client.delete(
            f"/v1/user/{user_id}/profile_pic",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_result.status_code in (200, 204)
        assert delete_result.json() == {
            "detail": "User profile pic deleted successfully"
        }

        # Further verifying if profile picture is deleted or not
        response_get = client.get(
            f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response_get.status_code == 200
        assert (
            response_get.json()["profile_pic"] == ""
        )  # Should return an empty field in profile pic
    finally:
        profile_file.close()  # Ensure the file is closed even if an error occurs
    delete_all_users()
