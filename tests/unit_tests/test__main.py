from email import contentmanager
from files_api.s3.read_objects import object_exists_in_s3
from files_api.s3.write_objects import upload_s3_object
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from files_api.main import create_app
# from files_api.settings import Settings
from tests.consts import TEST_BUCKET_NAME
from files_api.settings import Settings
from botocore.exceptions import ClientError


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws) -> TestClient:  # pylint: disable=unused-argument
    settings = Settings(s3_bucket_name=TEST_BUCKET_NAME)
    app = create_app(settings)
    with TestClient(app) as client:
        yield client


def test_upload_file(client: TestClient):
    prefix = "some_folder/test.txt"
    content = b"test"
    content_type = "plain/text"
    response = client.put(
        f"/files/{prefix}",
        files={"file": (prefix, content, content_type)},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "file_path": prefix,
        "message": f"New file uploaded at path: /{prefix}"
    }

    content = b"updated"
    response = client.put(
        f"/files/{prefix}",
        files={"file": (prefix, content, content_type)},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "file_path": prefix,
        "message": f"Existing file updated at path: /{prefix}"
    }


def test_list_files_with_pagination(client: TestClient):
    for i in range(15):
        client.put(
            f"/files/file_{i}",
            files={"file": (f"file_{i}", b"test", "plain/text")},
        )
    response = client.get(
        "/files?page_size=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 5
    assert "next_page_token" in data
        

def test_get_file_metadata(client: TestClient):
    client.put(
        f"/files/file_1",
        files={"file": (f"file_1", b"test", "text/plain")}
    )
    assert object_exists_in_s3(TEST_BUCKET_NAME, "file_1")
    response = client.head("/files/file_1")
    assert response.status_code == 200
    headers = response.headers
    assert headers["Content-Type"] == "text/plain"
    assert headers["Content-Length"] == str(len(b"test"))
    assert "Last-Modified" in headers



def test_get_file(client: TestClient):
    client.put(
        f"/files/file_1",
        files={"file": (f"file_1", b"test", "text/plain")}
    )
    response = client.get(
        "/files/file_1"
    )
    assert response.status_code == 200
    assert response.content == b"test"


def test_delete_file(client: TestClient):
    client.put(
        f"/files/file_1",
        files={"file": (f"file_1", b"test", "text/plain")}
    )
    response = client.delete("/files/file_1")
    response.status_code == 204

    with pytest.raises(ClientError):
        client.get("/files/file_1")