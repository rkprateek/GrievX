import boto3
from botocore.client import BaseClient


def create_storage_client(
    endpoint_url: str, access_key_id: str, secret_access_key: str, region_name: str
) -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region_name,
    )


def check_storage_connection(client: BaseClient, bucket: str) -> None:
    client.head_bucket(Bucket=bucket)


def upload_bytes(client: BaseClient, bucket: str, object_key: str, data: bytes, content_type: str) -> None:
    client.put_object(Bucket=bucket, Key=object_key, Body=data, ContentType=content_type)


def delete_object(client: BaseClient, bucket: str, object_key: str) -> None:
    client.delete_object(Bucket=bucket, Key=object_key)


def create_presigned_get_url(client: BaseClient, bucket: str, object_key: str, expires_in: int = 900) -> str:
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_in,
    )
