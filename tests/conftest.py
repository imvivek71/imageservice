"""
Test configuration and fixtures
"""

import pytest
import boto3
import json
from moto import mock_aws
from unittest.mock import Mock, patch


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["TABLE_NAME"] = "image-metadata"
    os.environ["BUCKET_NAME"] = "image-service-bucket"


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create a mock DynamoDB table."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        table = dynamodb.create_table(
            TableName="image-metadata",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        
        yield table


@pytest.fixture
def s3_bucket(aws_credentials):
    """Create a mock S3 bucket."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="image-service-bucket")
        
        yield s3


@pytest.fixture
def sample_image_data():
    """Sample image binary data."""
    # Minimal JPEG header
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9'


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = Mock()
    context.function_name = "test-function"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    context.memory_limit_in_mb = 128
    context.aws_request_id = "test-request-id"
    context.log_group_name = "/aws/lambda/test-function"
    context.log_stream_name = "2026/01/16/[$LATEST]test"
    context.get_remaining_time_in_millis = Mock(return_value=30000)
    
    return context


@pytest.fixture
def upload_event():
    """Sample upload event."""
    return {
        "httpMethod": "POST",
        "path": "/images",
        "queryStringParameters": {
            "user_id": "vivek12345",
            "tags": "beach,mountain",
            "description": "Beautiful sunset"
        },
        "body": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "isBase64Encoded": True,
        "headers": {
            "Content-Type": "application/octet-stream"
        }
    }


@pytest.fixture
def list_event():
    """Sample list event."""
    return {
        "httpMethod": "GET",
        "path": "/images",
        "queryStringParameters": {
            "user_id": "vivek12345",
            "tag": "beach",
            "visibility": "public"
        },
        "headers": {}
    }


@pytest.fixture
def get_event():
    """Sample get event."""
    return {
        "httpMethod": "GET",
        "path": "/images/550e8400-e29b-41d4-a716-446655440000",
        "pathParameters": {
            "imageId": "550e8400-e29b-41d4-a716-446655440000"
        },
        "headers": {}
    }


@pytest.fixture
def delete_event():
    """Sample delete event."""
    return {
        "httpMethod": "DELETE",
        "path": "/images/550e8400-e29b-41d4-a716-446655440000",
        "pathParameters": {
            "imageId": "550e8400-e29b-41d4-a716-446655440000"
        },
        "headers": {}
    }
