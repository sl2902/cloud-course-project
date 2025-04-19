import boto3

BUCKET = "cloud-bucket-sl"

session = boto3.Session(profile_name="cloud-course")
s3_client = session.client("s3")
s3_client.put_object(Bucket=BUCKET, Key="test/hello.txt", Body=b"Hello, World!", ContentType="text/plain")
