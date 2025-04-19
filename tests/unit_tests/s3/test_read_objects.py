"""Test cases for `s3.read_objects`."""

import boto3

from files_api.s3.read_objects import (
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from tests.consts import TEST_BUCKET_NAME

OBJECT_KEY = "test.txt"


def test_object_exists_in_s3(mocked_aws: None):  # pylint: disable=unused-argument
    """Test object exists in s3"""
    s3_client = boto3.client("s3")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key=OBJECT_KEY, Body=b"test content")
    response = object_exists_in_s3(bucket_name=TEST_BUCKET_NAME, object_key=OBJECT_KEY)
    assert response is True


def test_pagination(mocked_aws: None):  # pylint: disable=unused-argument
    """Test pagination"""
    s3_client = boto3.client("s3")
    for i in range(5):
        s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key=f"test_{i}.txt", Body=b"Test")
    # first_page = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME, MaxKeys=1)
    # next_token = first_page.get("NextContinuationToken")
    # assert next_token is not None
    objects, next_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, max_keys=2)
    assert len(objects) == 2
    assert objects[0]["Key"] == "test_0.txt"
    assert objects[1]["Key"] == "test_1.txt"

    objects, next_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, next_token)
    assert len(objects) == 3
    assert next_token is None


def test_mixed_page_sizes(mocked_aws: None):  # pylint: disable=unused-argument
    """Test mixed oage sizes"""
    s3_client = boto3.client("s3")
    for i in range(5):
        s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key=f"test_{i}.txt", Body=b"Test")
    objects, next_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, max_keys=2)
    assert objects[0]["Key"] == "test_0.txt"
    assert objects[1]["Key"] == "test_1.txt"
    assert next_token is not None

    objects, next_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, next_token, max_keys=2)
    assert len(objects) == 2
    assert objects[0]["Key"] == "test_2.txt"
    assert objects[1]["Key"] == "test_3.txt"
    assert next_token is not None

    objects, next_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, next_token)
    assert len(objects) == 1
    assert objects[0]["Key"] == "test_4.txt"
    assert next_token is None


def test_directory_queries(mocked_aws: None):  # pylint: disable=unused-argument
    """Test directory queries"""
    s3_client = boto3.client("s3")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder1/file_1.txt", Body=b"Test")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder1/file_2.txt", Body=b"Test")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder2/file_3.txt", Body=b"Test")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder2/subfolder/file_4.txt", Body=b"Test")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="file_1.txt", Body=b"Test")

    objects, next_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, "folder1/", max_keys=2)
    assert len(objects) == 2
    assert objects[0]["Key"] == "folder1/file_1.txt"
    assert objects[1]["Key"] == "folder1/file_2.txt"
    assert next_token is None

    objects, next_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, "folder2/subfolder/")
    assert len(objects) == 1
    assert objects[0]["Key"] == "folder2/subfolder/file_4.txt"
    assert next_token is None

    objects, next_token = fetch_s3_objects_metadata(
        TEST_BUCKET_NAME,
    )
    assert len(objects) == 5
    assert objects[0]["Key"] == "file_1.txt"
    assert objects[1]["Key"] == "folder1/file_1.txt"
    assert objects[2]["Key"] == "folder1/file_2.txt"
    assert objects[3]["Key"] == "folder2/file_3.txt"
    assert objects[4]["Key"] == "folder2/subfolder/file_4.txt"
    assert next_token is None
