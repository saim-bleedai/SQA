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


def test_create_report():  # smoke test for creating report
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
    assert response.json()["reporter_id"] == user_id
    assert response.json()["creator_id"] == creator_id
    delete_all_users()


def test_create_report_with_invalid_user_id():
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

    delete_result = client.delete(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    time.sleep(1)
    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,
    )

    assert response.status_code == 404  # expected output is user not found.
    delete_all_users()


def test_report_own_creator():
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    user_id = result.json()["user_id"]
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
    assert response.status_code == 400  # report not created
    assert response.json() == {
        "detail": "Report not created"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_create_report_with_invalid_creator_id():

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

    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    time.sleep(1)
    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,
    )

    assert response.status_code == 400  # expected output is creator not found.
    assert response.json() == {
        "detail": "Report not created"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_report():  # smoke test for get specific report
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

    assert response.status_code == 201  # expected output is report is created

    report_id = response.json()["id"]

    response = client.get(
        f"/v1/report/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    assert response.json()["id"] == report_id
    assert response.json()["creator_id"] == creator_id
    delete_all_users()


def test_get_invalid_report():  # getting a report with invalid id
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

    assert response.status_code == 201  # expected output is report is created

    report_id = response.json()["id"]

    response_delete = client.delete(
        f"/v1/report/{report_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

    response = client.get(
        f"/v1/report/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Report not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_delete_report():  # smoke test for delete report
    result = create_creator()

    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    report_payload = {
        "reporter_id": user_id,
        "creator_id": creator_id,
    }
    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,
    )

    assert response.status_code == 201  # expected output is report is created

    report_id = response.json()["id"]

    response_delete = client.delete(
        f"/v1/report/{report_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204
    # further testing if an invalid report is deleted
    result_delete = client.delete(
        f"/v1/report/{report_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert result_delete.status_code == 404
    delete_all_users()


def test_get_all_reports():  # smoke test for get all reports. checks all the expected keys and pagination.
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

    assert response.status_code == 201

    response_get = client.get(
        f"/v1/report/all/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_get.status_code == 200
    response_json = response_get.json()
    expected_top_level_keys = ["reports", "total_items", "page_num", "total_pages"]

    # Check if all expected top-level keys are in the response
    for key in expected_top_level_keys:
        assert key in response_json, f"Response missing top-level key '{key}'"

    # List of expected keys within each report
    expected_report_keys = [
        "id",
        "reporter_id",
        "creator_id",
        "description",
        "category",
        "created_at",
        "updated_at",
    ]

    # Check if 'reports' is a list
    assert isinstance(response_json["reports"], list), "'reports' should be a list"

    # Check each report in the list
    for report in response_json["reports"]:
        for key in expected_report_keys:
            assert key in report, f"Report missing key '{key}'"

    # Pagination checks
    total_items = response_json["total_items"]
    reports_length = len(response_json["reports"])

    assert (
        total_items == reports_length
    ), f"Total items ({total_items}) does not match the number of reports returned ({reports_length})"
    assert (
        response_json["page_num"] >= 1
    ), f"Page number should be greater than or equal to 1, found {response_json['page_num']}"
    assert (
        response_json["total_pages"] >= 1
    ), f"Total pages should be at least 1, found {response_json['total_pages']}"
    delete_all_users()


def test_get_all_reports_invalid_query():  # giving invalid paramters to check the response of the api
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

    assert response.status_code == 201

    response_get = client.get(
        f"/v1/report/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": "-1", "limit": "-1"},
    )

    assert response_get.status_code == 400
    assert response_get.json() == {
        "detail": "Invalid page number or limit"
    }  # ensuring a valid error message is returned

    delete_all_users()


def test_get_all_reports_no_items():  # test case to check if no reports exists, what will be the response, expected output is returns a 204 no content status code
    response_get = client.get(
        f"/v1/report/all/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_get.status_code == 204


def test_update_report():

    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    # Initial report creation
    report_payload = {
        "reporter_id": user_id,
        "creator_id": creator_id,
        "description": None,
        "category": None,
    }
    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,  # Use json parameter to send the payload as JSON
    )

    assert (
        response.status_code == 201
    ), "Failed to create report"  # Confirm report is created
    report_id = response.json()["id"]

    # Now update the report
    update_payload = {
        "description": "Updated description for testing",
        "category": "Updated category for testing",
    }

    update_response = client.put(
        f"/v1/report/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,  # Use json parameter to send the payload as JSON
        params={"id": report_id},
    )

    # Assertions for the update operation
    assert (
        update_response.status_code == 200
    ), f"Failed to update report, status code: {update_response.status_code}"
    updated_report = update_response.json()

    assert (
        updated_report["id"] == report_id
    ), "Updated report ID does not match the created report ID"
    assert (
        updated_report["description"] == update_payload["description"]
    ), "Report description was not updated correctly"
    assert (
        updated_report["category"] == update_payload["category"]
    ), "Report category was not updated correctly"

    # Additional validations
    assert (
        updated_report["reporter_id"] == user_id
    ), "Reporter ID should not change in the update"
    assert (
        updated_report["creator_id"] == creator_id
    ), "Creator ID should not change in the update"

    # Check that the updated_at timestamp is greater than or equal to the created_at timestamp

    created_at = datetime.fromisoformat(updated_report["created_at"])
    updated_at = datetime.fromisoformat(updated_report["updated_at"])
    assert (
        updated_at >= created_at
    ), "Updated timestamp is not greater than or equal to created timestamp"
    delete_all_users()


def test_update_invalid_report():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    result = create_user()
    assert result.status_code == 201
    user_id = result.json()["id"]

    # Initial report creation
    report_payload = {
        "reporter_id": user_id,
        "creator_id": creator_id,
        "description": None,
        "category": None,
    }
    response = client.post(
        "/v1/report/create",
        headers={"Authorization": f"Bearer {token}"},
        data=report_payload,  # Use json parameter to send the payload as JSON
    )

    assert (
        response.status_code == 201
    ), "Failed to create report"  # Confirm report is created
    report_id = response.json()["id"]

    response_delete = client.delete(
        f"/v1/report/{report_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response_delete.status_code == 200 or response_delete.status_code == 204

    update_payload = {
        "description": "Updated description for testing",
        "category": "Updated category for testing",
    }

    update_response = client.put(
        f"/v1/report/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
        data=update_payload,  # Use json parameter to send the payload as JSON
        params={"id": report_id},
    )

    # Assertions for the update operation
    assert (
        update_response.status_code == 404
    ), f"Failed to update report, status code: {update_response.status_code}"

    assert update_response.json() == {
        "detail": "Report not found"
    }  # ensuring a valid error message is returned
    delete_all_users()
