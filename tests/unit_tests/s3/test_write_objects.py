import boto3
from moto import mock_aws

from files_api.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME


@mock_aws
def test_upload_s3_object(mocked_aws):  # pylint: disable=unused-argument
    """Test upload s3 object"""
    # point_away_from_aws()
    # s3_client = boto3.client('s3')
    # s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

    object_name = "test_file.txt"
    file_content = b"this is a test"
    content_type = "text/plain"

    upload_s3_object(TEST_BUCKET_NAME, object_name, file_content, content_type)
    s3_client = boto3.client("s3")
    resp = s3_client.get_object(Bucket=TEST_BUCKET_NAME, Key=object_name)
    assert resp.get("ContentType") == content_type
    assert resp.get("Body").read() == file_content

    # object = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME, Prefix=object_name)
    # for obj in object.get('Contents', []):
    #     s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj.get('Key'))
    # s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
