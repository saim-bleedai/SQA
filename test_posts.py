from fastapi.testclient import TestClient
import random
import string
import sys
import time
import json
import requests
from datetime import datetime
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


def test_add_post():

    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
        "explore_post": True,
        "images": [],
    }
    print("P1", post_payload)

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,  # Send the payload as form data
    )

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"
    print("R4", response.json())
    post = response.json()
    print("R3", post)

    # Validate the returned post data
    assert "id" in post, "Response missing 'id' key"
    assert "creator_id" in post, "Response missing 'creator_id' key"
    assert "description" in post, "Response missing 'description' key"
    assert "explore_post" in post, "Response missing 'explore_post' key"
    assert "images" in post, "Response missing 'images' key"
    assert "created_at" in post, "Response missing 'created_at' key"
    assert "updated_at" in post, "Response missing 'updated_at' key"

    # Check that the post data matches the input
    assert (
        post["creator_id"] == creator_id
    ), "Post 'creator_id' does not match the input"
    assert (
        post["description"] == post_payload["description"]
    ), "Post 'description' does not match the input"
    assert (
        post["explore_post"] == post_payload["explore_post"]
    ), "Post 'explore_post' does not match the input"
    assert (
        post["images"] == post_payload["images"]
    ), "Post 'images' list does not match the input"

    # Additional checks for timestamp validity (ensure created_at and updated_at are present and correct format)

    created_at = datetime.fromisoformat(post["created_at"])
    updated_at = datetime.fromisoformat(post["updated_at"])
    assert (
        updated_at >= created_at
    ), "Updated timestamp is not greater than or equal to created timestamp"
    delete_all_users()


def test_create_post_with_deleted_creator():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    time.sleep(1)

    delete_result = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200
    time.sleep(1)

    # Now, prepare the payload for adding a post
    post_payload = {
        "creator_id": creator_id,  # Ensure the creator_id is sent as a string
        "description": "This is a test post",
        "explore_post": True,
    }
    print("R1", post_payload)

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,
    )

    # Assertions for the add post operation
    assert (
        response.status_code
        == 400  # needs to be fixed, currently throws 500 internal server error
    )
    delete_all_users()


def test_add_post_with_deleted_user():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    time.sleep(1)
    user_id = result.json()["user_id"]
    delete_result = client.delete(
        f"/v1/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_result.status_code == 204 or delete_result.status_code == 200

    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
    }
    print("R2", post_payload)

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,
    )
    print("SAIMM", response)

    # Assertions for the add post operation
    assert (
        response.status_code
        == 400  # needs to be fixed, currently throws 500 internal server error
    )
    delete_all_users()


def test_get_specific_post():  # smoke test for get specific post
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
        "explore_post": True,
        "images": [],
    }
    print("P1", post_payload)

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,  # Send the payload as form data
    )

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"
    print("R4", response.json())
    post_id = response.json()["id"]
    print(post_id)

    get_result = client.get(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 200
    assert get_result.json()["id"] == post_id
    post = get_result.json()
    assert "id" in post, "Response missing 'id' key"
    assert "creator_id" in post, "Response missing 'creator_id' key"
    assert "description" in post, "Response missing 'description' key"
    assert "explore_post" in post, "Response missing 'explore_post' key"
    assert "images" in post, "Response missing 'images' key"
    assert "created_at" in post, "Response missing 'created_at' key"
    assert "updated_at" in post, "Response missing 'updated_at' key"

    # Check that the post data matches the input
    assert (
        post["creator_id"] == creator_id
    ), "Post 'creator_id' does not match the input"
    assert (
        post["description"] == post_payload["description"]
    ), "Post 'description' does not match the input"
    assert (
        post["explore_post"] == post_payload["explore_post"]
    ), "Post 'explore_post' does not match the input"
    assert (
        post["images"] == post_payload["images"]
    ), "Post 'images' list does not match the input"
    delete_all_users()


def test_get_invalid_post():  # testing to get a deleted post
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"

    post_id = response.json()["id"]
    delete_post = client.delete(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_post.status_code == 200 or delete_post.status_code == 204

    get_result = client.get(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 404

    assert get_result.json() == {
        "detail": "Post not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_deleted_user_post():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    user_id = result.json()["user_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"

    post_id = response.json()["id"]
    delete_user = client.delete(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_user.status_code == 200 or delete_user.status_code == 204

    get_result = client.get(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 404

    assert get_result.json() == {
        "detail": "Post not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_invalid_creator_post():  # trying to get a post from a deleted user
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"

    post_id = response.json()["id"]
    delete_creator = client.delete(
        f"/v1/creator/{creator_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_creator.status_code == 200 or delete_creator.status_code == 204

    get_result = client.get(
        f"/v1/post/{post_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert get_result.status_code == 404

    assert get_result.json() == {
        "detail": "Post not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_all_posts():  # smoke test for get all creators
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"

    get_result = client.get(
        f"/v1/post/all/", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 200

    result = get_result.json()
    # List of expected top-level keys
    expected_top_level_keys = ["posts", "total_items", "page_num", "total_pages"]

    # Check if all expected top-level keys are in the response
    for key in expected_top_level_keys:
        assert key in result, f"Response missing top-level key '{key}'"

    # List of expected keys within each post
    expected_post_keys = [
        "id",
        "creator_id",
        "description",
        "explore_post",
        "images",
        "created_at",
        "updated_at",
    ]

    # Check if 'posts' is a list
    assert isinstance(result["posts"], list), "'posts' should be a list"

    # Check each post in the list
    for post in result["posts"]:
        for key in expected_post_keys:
            assert key in post, f"Post missing key '{key}'"

        # Check that 'explore_post' is a boolean
        assert isinstance(
            post["explore_post"], bool
        ), f"Post 'explore_post' should be a boolean"

        # Validate the images field
        assert isinstance(post["images"], list), "'images' should be a list"

    # Pagination checks
    total_items = result["total_items"]
    posts_length = len(result["posts"])

    assert (
        total_items == posts_length
    ), f"Total items ({total_items}) do not match the number of posts returned ({posts_length})"
    assert result["page_num"] >= 1
    assert result["total_pages"] >= 1

    # Additional Pagination Validation
    delete_all_users()


def test_get_all_invalid_query():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert response.status_code == 201

    get_result = client.get(
        f"/v1/post/all/",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": "-1", "limit": "-1"},
    )
    assert get_result.status_code == 400
    delete_all_users()


def test_update_post():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert response.status_code == 201
    post_id = response.json()["id"]
    update_payload = {"description": "updated description", "explore_post": False}

    response_update = client.put(
        f"/v1/post/{post_id},",
        headers={"Authorization": f"Bearer {token}"},
        params={"id": post_id},
        data=update_payload,
    )
    assert response_update.status_code == 200
    assert response_update.json()["id"] == post_id
    assert response_update.json()["description"] == "updated description"
    assert response_update.json()["explore_post"] == False

    # verfication of update by getting the post
    get_result = client.get(
        f"/v1/post/{post_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert get_result.status_code == 200
    assert get_result.json()["id"] == post_id
    assert get_result.json()["description"] == "updated description"
    assert get_result.json()["explore_post"] == False
    delete_all_users()


def test_update_invalid_post():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert response.status_code == 201
    post_id = response.json()["id"]

    delete_post = client.delete(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_post.status_code == 200 or delete_post.status_code == 204
    update_payload = {"description": "updated description", "explore_post": False}

    response_update = client.put(
        f"/v1/post/{post_id},",
        headers={"Authorization": f"Bearer {token}"},
        params={"id": post_id},
        data=update_payload,
    )
    assert response_update.status_code == 404
    assert response_update.json() == {
        "detail": "Post not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_update_deleted_user_post():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]
    user_id = result.json()["user_id"]

    # Now, prepare the payload for adding a post
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

    # Assertions for the add post operation
    assert response.status_code == 201
    post_id = response.json()["id"]

    delete_user = client.delete(
        f"/v1/user/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_user.status_code == 200 or delete_user.status_code == 204
    update_payload = {"description": "updated description", "explore_post": False}

    response_update = client.put(
        f"/v1/post/{post_id},",
        headers={"Authorization": f"Bearer {token}"},
        params={"id": post_id},
        data=update_payload,
    )
    assert response_update.status_code == 404
    assert response_update.json() == {
        "detail": "Post not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_create_post_with_images():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Prepare the file payloads
    base_path = "fanbai_ss"
    image_paths = ["img1.jpg", "img2.jpg"]
    files = []
    try:
        # Open image files in binary mode and prepare them for sending
        for image_path in image_paths:
            full_path = os.path.join(base_path, image_path)
            image_file = open(full_path, "rb")
            files.append(("images", (image_path, image_file, "image/jpeg")))

        # Prepare the other payload data
        data = {
            "creator_id": creator_id,  # Ensure all data are strings for multipart
            "description": "This is a test post",
        }

        # Send the POST request to add a post
        response = client.post(
            "/v1/post/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,  # Non-file data
            files=files,  # Files to be uploaded
        )

        # Assertions for the add post operation
        assert (
            response.status_code == 201
        ), f"Failed to add post, status code: {response.status_code}"
        post = response.json()

        # Validate the returned post data
        assert "id" in post, "Response missing 'id' key"
        assert (
            post["creator_id"] == creator_id
        ), "Post 'creator_id' does not match the input"
        assert (
            post["description"] == "This is a test post"
        ), "Post 'description' does not match the input"

        assert len(post["images"]) == len(
            image_paths
        ), "Number of images does not match the input"

    finally:
        # Close all opened files
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][
                    1
                ].close()  # Close the file handle which is the second element in the tuple
    delete_all_users()


def test_add_post_with_different_payload():
    result = create_creator()
    assert result.status_code == 201
    creator_id = result.json()["creator_id"]

    # Now, prepare the payload for adding a post
    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
        "explore_post": "false",
        "images": [],
    }

    # Send the POST request to add a post
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,  # Send the payload as form data
    )

    # Assertions for the add post operation
    assert (
        response.status_code == 201
    ), f"Failed to add post, status code: {response.status_code}"

    post = response.json()
    post_id = response.json()["id"]

    # Validate the returned post data
    assert "id" in post, "Response missing 'id' key"
    assert "creator_id" in post, "Response missing 'creator_id' key"
    assert "description" in post, "Response missing 'description' key"
    assert "explore_post" in post, "Response missing 'explore_post' key"
    assert "images" in post, "Response missing 'images' key"
    assert "created_at" in post, "Response missing 'created_at' key"
    assert "updated_at" in post, "Response missing 'updated_at' key"

    # Check that the post data matches the input
    assert (
        post["creator_id"] == creator_id
    ), "Post 'creator_id' does not match the input"
    assert (
        post["description"] == post_payload["description"]
    ), "Post 'description' does not match the input"
    assert post["explore_post"] == False
    assert post["images"] == post_payload["images"]
    get_result = client.get(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_result.status_code == 200
    assert get_result.json()["id"] == post_id
    post = get_result.json()
    assert "id" in post, "Response missing 'id' key"
    assert "creator_id" in post, "Response missing 'creator_id' key"
    assert "description" in post, "Response missing 'description' key"
    assert "explore_post" in post, "Response missing 'explore_post' key"
    assert "images" in post, "Response missing 'images' key"
    assert "created_at" in post, "Response missing 'created_at' key"
    assert "updated_at" in post, "Response missing 'updated_at' key"

    # Check that the post data matches the input
    assert (
        post["creator_id"] == creator_id
    ), "Post 'creator_id' does not match the input"
    assert (
        post["description"] == post_payload["description"]
    ), "Post 'description' does not match the input"
    assert post["explore_post"] == False
    assert (
        post["images"] == post_payload["images"]
    ), "Post 'images' list does not match the input"
    delete_all_users()
