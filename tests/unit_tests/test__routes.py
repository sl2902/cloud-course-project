from fastapi import status
from fastapi.testclient import TestClient

from files_api.s3.read_objects import object_exists_in_s3
from tests.consts import TEST_BUCKET_NAME


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
