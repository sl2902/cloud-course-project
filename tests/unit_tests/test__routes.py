from fastapi import status
from fastapi.testclient import TestClient

from files_api.schemas import GeneratedFileType

from files_api.s3.read_objects import object_exists_in_s3
from tests.consts import TEST_BUCKET_NAME

TEST_FILE_PATH = "test.txt"

def test_upload_file(client: TestClient):
    prefix = "some_folder/test.txt"
    content = b"test"
    content_type = "text/plain"
    response = client.put(
        f"/v1/files/{prefix}",
        files={"file_content": (prefix, content, content_type)},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"file_path": prefix, "message": f"New file uploaded at path: /{prefix}"}

    content = b"updated"
    response = client.put(
        f"/v1/files/{prefix}",
        files={"file_content": (prefix, content, content_type)},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"file_path": prefix, "message": f"Existing file updated at path: /{prefix}"}


def test_list_files_with_pagination(client: TestClient):
    for i in range(15):
        client.put(
            f"/v1/files/file_{i}",
            files={"file_content": (f"file_{i}", b"test", "plain/text")},
        )
    response = client.get("/v1/files?page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 10
    assert "next_page_token" in data


def test_get_file_metadata(client: TestClient):
    client.put("/v1/files/file_1", files={"file_content": ("file_1", b"test", "text/plain")})
    assert object_exists_in_s3(TEST_BUCKET_NAME, "file_1")
    response = client.head("/v1/files/file_1")
    assert response.status_code == 200
    headers = response.headers
    assert headers["Content-Type"] == "text/plain"
    assert headers["Content-Length"] == str(len(b"test"))
    assert "Last-Modified" in headers


def test_get_file(client: TestClient):
    client.put("/v1/files/file_1", files={"file_content": ("file_1", b"test", "text/plain")})
    response = client.get("/v1/files/file_1")
    assert response.status_code == 200
    assert response.content == b"test"


def test_delete_file(client: TestClient):
    client.put("/v1/files/file_1", files={"file_content": ("file_1", b"test", "text/plain")})
    response = client.delete("/v1/files/file_1")
    assert response.status_code == 204

    response = client.get("/v1/files/file_1")
    assert response.status_code == 404

def test_generate_chat_text(client: TestClient):
    """Test generating text using POST method."""
    # response = client.post(
    #     url=f"/v1/files/generated/chat/completion/{TEST_FILE_PATH}",
    #     params={"prompt": "Test Prompt", "file_type": GeneratedFileType.TEXT.value},
    # )

    response = client.post(
        url=f"/v1/files/generated/chat/completion/{TEST_FILE_PATH}",
        params={"prompt": "Test Prompt"},
    )

    respone_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        respone_data["message"]
        == f"New {GeneratedFileType.TEXT.value} file generated and uploaded at path: {TEST_FILE_PATH}"
    )

    # Get the generated file
    response = client.get(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"This is a mock response from the chat completion endpoint."
    assert "text/plain" in response.headers["Content-Type"]

def test_imag_generation(client: TestClient):
    """Test generating image using POST method."""
    IMAGE_FILE_PATH = "some/nested/path/image.png"  # pylint: disable=invalid-name
    response = client.post(
        url=f"/v1/files/generated/image/generation/{IMAGE_FILE_PATH}",
        params={"prompt": "Test Prompt"},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response_data["message"]
        == f"New {GeneratedFileType.IMAGE.value} file generated and uploaded at path: {IMAGE_FILE_PATH}"
    )

    response = client.get(f"/v1/files/{IMAGE_FILE_PATH}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content is not None
    assert response.headers["Content-Type"] == "image/png"