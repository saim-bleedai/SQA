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


def test_update_socials():
    add_creator = create_creator()
    assert add_creator.status_code == 201
    creator_id = add_creator.json()["creator_id"]

    update_payload = {
        "instagram": "insta url",
        "snapchat": "snapchat url",
        "tiktok": "tiktok url",
    }

    response = client.put(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
        params={"creator_id": creator_id},
    )
    assert response.status_code == 200 or response.status_code == 201
    assert response.json()["creator_id"] == creator_id
    assert response.json()["instagram"] == update_payload["instagram"]
    assert response.json()["snapchat"] == update_payload["snapchat"]
    assert response.json()["tiktok"] == update_payload["tiktok"]

    # further verifying by getting the social handles

    get_result = client.get(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert get_result.status_code == 200
    assert get_result.json()["creator_id"] == creator_id
    assert get_result.json()["instagram"] == update_payload["instagram"]
    assert get_result.json()["snapchat"] == update_payload["snapchat"]
    assert get_result.json()["tiktok"] == update_payload["tiktok"]


def test_update_invalid_creator_socials():
    add_creator = create_creator()
    assert add_creator.status_code == 201
    creator_id = add_creator.json()["creator_id"]

    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    update_payload = {
        "instagram": "insta url",
        "snapchat": "snapchat url",
        "tiktok": "tiktok url",
    }

    response = client.put(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
        params={"creator_id": creator_id},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Social Handles not found"}
    # getting the invalid creators social handles
    get_result = client.get(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert get_result.status_code == 404
    assert get_result.json() == {"detail": "Social Handles not found"}

    delete_result = client.delete(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )

    assert delete_result.status_code == 404
    assert delete_result.json() == {"detail": "Social Handles not found"}


def test_update_creator_invalid_query():
    update_payload = {
        "instagram": "insta url",
        "snapchat": "snapchat url",
        "tiktok": "tiktok url",
    }
    creator_id = "one"  # sending the creator id as string

    response = client.put(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
        params={"creator_id": creator_id},
    )
    assert response.status_code == 422

    get_result = client.get(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert get_result.status_code == 422

    delete_result = client.delete(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )

    assert delete_result.status_code == 422


def test_delete_socials():
    add_creator = create_creator()
    assert add_creator.status_code == 201
    creator_id = add_creator.json()["creator_id"]

    update_payload = {
        "instagram": "insta url",
        "snapchat": "snapchat url",
        "tiktok": "tiktok url",
    }

    response = client.put(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,
        params={"creator_id": creator_id},
    )
    assert response.status_code == 200 or response.status_code == 201

    # deleting the socials
    delete_result = client.delete(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )

    assert delete_result.status_code == 200 or delete_result.status_code == 204

    # confirming if socials are deleted or not
    get_result = client.get(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert get_result.status_code == 404
    assert get_result.json() == {"detail": "Social Handles not found"}


def test_get_socials():
    add_creator = create_creator()
    assert add_creator.status_code == 201
    creator_id = add_creator.json()["creator_id"]
    get_result = client.get(
        f"/v1/social_handles/{creator_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"creator_id": creator_id},
    )
    assert (
        get_result.status_code == 200 or get_result.status_code == 201
    )  # needs to be changed
    keys_with_empty_strings = ["instagram", "snapchat", "tiktok"]

    for key in keys_with_empty_strings:
        assert key in get_result.json()
        assert get_result.json()[key] == ""
