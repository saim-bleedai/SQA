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


def create_post():
    result = create_creator()

    creator_id = result.json()["creator_id"]
    post_payload = {
        "creator_id": creator_id,
        "description": "This is a test post",
    }
    response = client.post(
        "/v1/post/create",
        headers={"Authorization": f"Bearer {token}"},
        data=post_payload,  # Send the payload as form data
    )
    return response


def test_add_images():
    response = create_post()
    assert response.status_code == 201
    post_id = response.json()["id"]

    # testing the add image endpoint
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
            "post_id": post_id,  # Ensure all data are strings for multipart
        }

        # Send the POST request to add a post
        response = client.post(
            f"/v1/posts_images/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,  # Non-file data
            files=files,  # Files to be uploaded
        )

        # Assertions for the add post operation
        assert response.status_code == 201
        image_response = response.json()
        added_image_ids = [img["id"] for img in image_response["image_ids"]]

    finally:
        # Close all opened files
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][
                    1
                ].close()  # Close the file handle which is the second element in the tuple

    get_post_response = client.get(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert (
        get_post_response.status_code == 200
    ), "Failed to retrieve post, status code: {}".format(get_post_response.status_code)
    post_data = get_post_response.json()

    # Extract image IDs from the get post response
    retrieved_image_ids = [img["image_id"] for img in post_data["images"]]

    retrieved_image_ids = sorted([img["image_id"] for img in post_data["images"]])

    # Verify that both lists are exactly equal
    assert (
        added_image_ids == retrieved_image_ids
    ), "Image IDs from the add operation do not match those retrieved from the post"

    delete_all_users()


def test_add_image_required_fields_validation():
    setup()
    files = []
    post_id = ""

    data = {
        "post_id": post_id,  # Ensure all data are strings for multipart
    }

    # Send the POST request to add a post
    response = client.post(
        f"/v1/posts_images/create",
        headers={"Authorization": f"Bearer {token}"},
        data=data,  # Non-file data
        files=files,  # Files to be uploaded
    )

    # Assertions for the add post operation
    assert response.status_code == 422


def test_add_image_with_invalid_post():
    response = create_post()
    assert response.status_code == 201
    post_id = response.json()["id"]

    # deleting the post

    delete_post = client.delete(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_post.status_code == 200 or delete_post.status_code == 204

    # testing the add image endpoint
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
            "post_id": post_id,  # Ensure all data are strings for multipart
        }

        # Send the POST request to add a post
        response = client.post(
            f"/v1/posts_images/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,  # Non-file data
            files=files,  # Files to be uploaded
        )

        # Assertions for the add post operation
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Post not found"
        }  # ensuring a valid error message is returned

    finally:
        # Close all opened files
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][
                    1
                ].close()  # Close the file handle which is the second element in the tuple
    delete_all_users()


def test_get_images():
    response = create_post()
    assert response.status_code == 201
    post_id = response.json()["id"]

    # testing the add image endpoint
    base_path = "fanbai_ss"
    image_paths = ["img1.jpg"]
    files = []
    try:
        # Open image files in binary mode and prepare them for sending
        for image_path in image_paths:
            full_path = os.path.join(base_path, image_path)
            image_file = open(full_path, "rb")
            files.append(("images", (image_path, image_file, "image/jpeg")))

        # Prepare the other payload data
        data = {
            "post_id": post_id,  # Ensure all data are strings for multipart
        }

        # Send the POST request to add a post
        response = client.post(
            f"/v1/posts_images/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,  # Non-file data
            files=files,  # Files to be uploaded
        )

        # Assertions for the add post operation
        assert response.status_code == 201
        image_response = response.json()
        added_image_ids = [img["id"] for img in image_response["image_ids"]]
        image_id = added_image_ids[0]

    finally:
        # Close all opened files
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][
                    1
                ].close()  # Close the file handle which is the second element in the tuple

    get_response = client.get(
        f"/v1/posts_images/{image_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"image_id": image_id},
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == image_id
    delete_all_users()


def test_get_invalid_post_images():
    response = create_post()
    assert response.status_code == 201
    post_id = response.json()["id"]

    # testing the add image endpoint
    base_path = "fanbai_ss"
    image_paths = ["img1.jpg"]
    files = []
    try:
        # Open image files in binary mode and prepare them for sending
        for image_path in image_paths:
            full_path = os.path.join(base_path, image_path)
            image_file = open(full_path, "rb")
            files.append(("images", (image_path, image_file, "image/jpeg")))

        # Prepare the other payload data
        data = {
            "post_id": post_id,  # Ensure all data are strings for multipart
        }

        # Send the POST request to add a post
        response = client.post(
            f"/v1/posts_images/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,  # Non-file data
            files=files,  # Files to be uploaded
        )

        # Assertions for the add post operation
        assert response.status_code == 201
        image_response = response.json()

        added_image_ids = [img["id"] for img in image_response["image_ids"]]
        image_id = added_image_ids[0]

    finally:
        # Close all opened files
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][
                    1
                ].close()  # Close the file handle which is the second element in the tuple

    delete_post = client.delete(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_post.status_code == 200 or delete_post.status_code == 204

    get_response = client.get(
        f"/v1/posts_images/{image_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Image not found"
    }  # ensuring a valid error message is returned
    delete_all_users()


def test_get_image_field_validation():
    setup()
    image_id = "str"
    get_response = client.get(
        f"/v1/posts_images/{image_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 422
    delete_all_users()


def test_update_image():

    response = create_post()
    assert response.status_code == 201
    post_id = response.json()["id"]

    # Base path for images
    base_path = "fanbai_ss"
    image_paths = ["img1.jpg"]
    files = []

    try:
        # Open image files in binary mode and prepare them for sending
        for image_path in image_paths:
            full_path = os.path.join(base_path, image_path)
            image_file = open(full_path, "rb")
            files.append(("images", (image_path, image_file, "image/jpeg")))

        # Prepare the other payload data
        data = {"post_id": post_id}

        # Send the POST request to add images to the post
        response = client.post(
            "/v1/posts_images/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            files=files,
        )

        assert response.status_code == 201, "Failed to add images"
        image_response = response.json()
        added_image_ids = [img["id"] for img in image_response["image_ids"]]
        image_id = added_image_ids[0]

    finally:
        # Ensure files are closed after the operation
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][1].close()
    # Updating the image
    update_image_path = os.path.join(base_path, "img2.jpg")
    assert os.path.exists(update_image_path)

    update_image_file = open(update_image_path, "rb")
    try:
        update_files = {"image": ("img2.jpg", update_image_file, "image/jpeg")}

        # Send the PUT request to update the image
        update_response = client.put(
            f"/v1/posts_images/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
            data={"post_id": post_id},
            files=update_files,
        )

        assert update_response.status_code == 200  # need to change this

    finally:
        update_image_file.close()

    delete_all_users()


def test_update_image_with_invalid_post():
    response = create_post()
    assert response.status_code == 201
    post_id = response.json()["id"]

    # Base path for images
    base_path = "fanbai_ss"
    image_paths = ["img1.jpg"]
    files = []

    try:
        # Open image files in binary mode and prepare them for sending
        for image_path in image_paths:
            full_path = os.path.join(base_path, image_path)
            image_file = open(full_path, "rb")
            files.append(("images", (image_path, image_file, "image/jpeg")))

        # Prepare the other payload data
        data = {"post_id": post_id}

        # Send the POST request to add images to the post
        response = client.post(
            "/v1/posts_images/create",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            files=files,
        )

        assert response.status_code == 201, "Failed to add images"
        image_response = response.json()
        added_image_ids = [img["id"] for img in image_response["image_ids"]]
        image_id = added_image_ids[0]

    finally:
        # Ensure files are closed after the operation
        for file_info in files:
            if isinstance(file_info[1], tuple) and len(file_info[1]) > 1:
                file_info[1][1].close()

    delete_post = client.delete(
        f"/v1/post/{post_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_post.status_code == 200 or delete_post.status_code == 204

    # Updating the image
    update_image_path = os.path.join(base_path, "img2.jpg")
    assert os.path.exists(update_image_path)

    update_image_file = open(update_image_path, "rb")
    try:
        update_files = {"image": ("img2.jpg", update_image_file, "image/jpeg")}

        # Send the PUT request to update the image
        update_response = client.put(
            f"/v1/posts_images/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
            data={"post_id": post_id},
            files=update_files,
        )

        assert update_response.status_code == 404
        assert update_response.json() == {
            "detail": "Post or Image not found"
        }  # ensuring a valid error message is returned

    finally:
        update_image_file.close()
    delete_all_users()


def test_update_image_validation():
    setup()
    base_path = "fanbai_ss"
    update_image_path = os.path.join(base_path, "img2.jpg")
    assert os.path.exists(update_image_path)
    image_id = "str"
    post_id = "str"

    update_image_file = open(update_image_path, "rb")
    try:
        update_files = {"image": ("img2.jpg", update_image_file, "image/jpeg")}

        # Send the PUT request to update the image
        update_response = client.put(
            f"/v1/posts_images/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
            data={"post_id": post_id},
            files=update_files,
        )

        assert update_response.status_code == 422
    finally:
        update_image_file.close()
    delete_all_users()
