import os

import boto3
import botocore
import pytest
from moto import mock_aws

# from files_api.main import S3_BUCKET_NAME as TEST_BUCKET_NAME
from tests.consts import TEST_BUCKET_NAME
from tests.utils import delete_s3_bucket


def point_away_from_aws():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture()
def mocked_aws():
    with mock_aws():
        point_away_from_aws()
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

        yield

        try:
            delete_s3_bucket(TEST_BUCKET_NAME)
        except botocore.exceptions.ClientError as err:
            if not err.response["Error"]["Code"] == "NoSuchBucket":
                raise

        # response = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME)
        # for obj in response.get("Contents", []):
        #     s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj.get("Key"))

        # s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
