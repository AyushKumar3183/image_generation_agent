"""FastAPI endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from image_generation_agent.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_example_1_text_to_image(client: TestClient, mock_backend_success, mock_s3_upload):
    response = client.post(
        "/v1/images/generate",
        json={"prompt": "Generate a luxury evening gown"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workflow"] == "text_to_image"
    assert len(data["image_urls"]) == 1
    assert data["number_of_images"] == 1
    assert "image_base64" not in data


def test_example_2_image_to_image(client: TestClient, mock_backend_success, mock_s3_upload):
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Make this dress black",
            "reference_images": ["https://cdn.example.com/dress.jpg"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workflow"] == "image_to_image"
    assert len(data["image_urls"]) == 1


def test_example_3_multi_image(client: TestClient, mock_backend_success, mock_s3_upload):
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Create a new outfit using these references",
            "reference_images": [
                "https://cdn.example.com/top.jpg",
                "https://cdn.example.com/skirt.jpg",
                "https://cdn.example.com/jacket.jpg",
            ],
            "resolution": "4K",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workflow"] == "multi_image_generation"
    assert data["resolution"] == "4K"


def test_generate_image_empty_prompt(client: TestClient):
    response = client.post(
        "/v1/images/generate",
        json={"prompt": "   "},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "EMPTY_PROMPT"


def test_generate_image_invalid_reference(client: TestClient):
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Edit this",
            "reference_images": ["https://"],
        },
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_REFERENCE_URL"


def test_legacy_generation_mode_ignored(client: TestClient, mock_backend_success, mock_s3_upload):
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Generate a luxury evening gown",
            "generation_mode": "text_to_image",
        },
    )
    assert response.status_code == 200
    assert response.json()["workflow"] == "text_to_image"


def test_legacy_reference_image_urls(client: TestClient, mock_backend_success, mock_s3_upload):
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Make this dress black",
            "reference_image_urls": ["https://cdn.example.com/dress.jpg"],
        },
    )
    assert response.status_code == 200
    assert response.json()["workflow"] == "image_to_image"


def test_generate_multiple_images(client: TestClient, mock_backend_success, mock_s3_upload):
    mock_s3_upload.side_effect = [
        f"https://vrozart-fashion-app.s3.ap-south-1.amazonaws.com/generated-images/test-{i}.jpg"
        for i in range(3)
    ]
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Generate a luxury evening gown",
            "reference_images": [],
            "resolution": "1K",
            "number_of_images": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["number_of_images"] == 3
    assert len(data["image_urls"]) == 3
    assert mock_backend_success.await_count == 3
    assert mock_s3_upload.await_count == 3


def test_number_of_images_out_of_range(client: TestClient):
    response = client.post(
        "/v1/images/generate",
        json={
            "prompt": "Generate a luxury evening gown",
            "number_of_images": 5,
        },
    )
    assert response.status_code == 422
