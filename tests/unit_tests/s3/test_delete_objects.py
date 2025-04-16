"""Test cases for `s3.delete_objects`."""

from src.files_api.s3.delete_objects import (
    delete_s3_object,
)
from src.files_api.s3.read_objects import object_exists_in_s3
from src.files_api.s3.write_objects import upload_s3_object
import boto3
from tests.consts import TEST_BUCKET_NAME


def test_delete_existing_s3_object(mocked_aws: None):
    s3_client = boto3.client("s3")
    object_key = "file_to_delete.txt"
    upload_s3_object(
        TEST_BUCKET_NAME,
        object_key,
        b"Test"
    )
    delete_s3_object(TEST_BUCKET_NAME, object_key)
    assert object_exists_in_s3(TEST_BUCKET_NAME, object_key) is False


def test_delete_nonexistent_s3_object(mocked_aws: None):
    s3_client = boto3.client("s3")
    object_key = "file_to_delete.txt"
    upload_s3_object(
        TEST_BUCKET_NAME,
        object_key,
        b"Test"
    )
    delete_s3_object(TEST_BUCKET_NAME, object_key)
    delete_s3_object(TEST_BUCKET_NAME, object_key)
    assert object_exists_in_s3(TEST_BUCKET_NAME, object_key) is False