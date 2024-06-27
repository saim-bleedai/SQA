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


token = None


def setup(generate_token=False):
    if generate_token:
        get_token()


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


def test_text_to_speech():
    setup(generate_token=True)

    # List of voice presets to test
    voice_presets = [
        "default",
        "Trump",
        "Obama",
        "Joe Rogan",
        "Pewdiepie",
        "Mr Whose The Boss",
    ]
    text_to_convert = "Hello, how are you?"

    for voice in voice_presets:
        # Send POST request to the text to speech endpoint
        response = client.post(
            "/v1/audio/text_to_speech",
            headers={"Authorization": f"Bearer {token}"},
            data={"text": text_to_convert, "voice_preset": voice},
        )

        # Check if the response is successful
        assert response.status_code == 200, f"Failed for voice preset: {voice}"


def test_text_to_speech_empty_string():
    setup(generate_token=True)
    text_to_convert = "  "
    response = client.post(
        "/v1/audio/text_to_speech",
        headers={"Authorization": f"Bearer {token}"},
        data={"text": text_to_convert, "voice_preset": "default"},
    )
    assert (
        response.status_code == 400
    )  # should throw a bad request error. needs to be fixed. currently throws 500 error


def test_text_to_speech_field_validation():
    setup()
    response = client.post(
        "/v1/audio/text_to_speech",
        headers={"Authorization": f"Bearer {token}"},
        data={"text": "", "voice_preset": ""},
    )
    assert (
        response.status_code == 422
    )  # should throw a unprocessable entity error. needs to be fixed


def test_speech_to_text():
    setup(generate_token=True)
    base_path = "fanbai_ss"  # Adjust base path to your file location
    voice_preset_path = os.path.join(base_path, "hello.wav")
    assert os.path.exists(voice_preset_path), "Voice preset file does not exist"

    # Open the audio file in binary read mode
    with open(voice_preset_path, "rb") as voice_file:
        files = {"audio_file": ("voice_preset.mp3", voice_file, "audio/mpeg")}
        # Send the POST request with the audio file
        response = client.post(
            "/v1/audio/speech_to_text",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Check if the response is successful
    assert response.status_code == 200, "Speech to text conversion failed"
    data = response.json()

    message = data["message"]

    # Check the presence of 'text' and 'chunks' in 'message'
    assert "text" in message
    assert "chunks" in message

    # Validate the content of the 'text'
    expected_text = "Hello."
    assert message["text"].strip() == expected_text

    # Assert the structure and content of 'chunks'
    chunks = message["chunks"]
    assert isinstance(chunks, list)
    assert len(chunks) > 0

    # Validate each chunk
    for chunk in chunks:
        assert "timestamp" in chunk
        assert "text" in chunk
        assert len(chunk["timestamp"]) == 2
        assert chunk["text"].strip() == expected_text
        # Further validate the timestamps
        start_time, end_time = chunk["timestamp"]
        assert start_time >= 0, "Start time should be non-negative"
        assert (
            end_time >= start_time
        ), "End time should be greater than or equal to start time"


def test_speech_to_text_invalid_file():
    setup(generate_token=True)
    base_path = "fanbai_ss"  # Adjust base path to your file location
    voice_preset_path = os.path.join(base_path, "img1.jpg")
    assert os.path.exists(voice_preset_path), "Voice preset file does not exist"

    # Open the audio file in binary read mode
    with open(voice_preset_path, "rb") as voice_file:
        files = {"audio_file": ("voice_preset.mp3", voice_file, "image/jpeg")}
        # Send the POST request with the image file
        response = client.post(
            "/v1/audio/speech_to_text",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Response should not be successful
    assert response.status_code == 400  # needs fix
