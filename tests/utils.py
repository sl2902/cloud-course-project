import boto3


def delete_s3_bucket(bucket_name: str) -> None:
    s3_delete = boto3.resource("s3")
    bucket = s3_delete.Bucket(bucket_name)
    bucket.objects.all().delete()
    bucket.delete()
