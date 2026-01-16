"""
Author: Vivek Kuumar Goswami
Date: January 16, 2026
S3 Service Layer - All S3 operations
"""

import os
import boto3
from utils.logger import get_logger

logger = get_logger(__name__)

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'image-service-bucket')

# For LocalStack/testing: endpoint URL to use in presigned URLs
# This should be accessible from the client's perspective
S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', 'http://localhost:4566')


class S3Service:
    """Service for all S3 operations."""
    
    @staticmethod
    def upload_object(key, body, content_type='image/jpeg', metadata=None):
        """
        Upload an object to S3.
        
        Args:
            key: S3 object key
            body: Binary data
            content_type: Content type
            metadata: Optional metadata dict
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Uploading object to S3: s3://{BUCKET_NAME}/{key}")
            params = {
                'Bucket': BUCKET_NAME,
                'Key': key,
                'Body': body,
                'ContentType': content_type
            }
            if metadata:
                params['Metadata'] = metadata
            
            s3_client.put_object(**params)
            logger.info(f"✓ Object uploaded successfully ({len(body)} bytes)")
            return True
        except Exception as e:
            logger.error(f"✗ Upload failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def download_object(key):
        """
        Download an object from S3.
        
        Args:
            key: S3 object key
        
        Returns:
            Binary data
        """
        try:
            logger.info(f"Downloading object from S3: s3://{BUCKET_NAME}/{key}")
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            data = response['Body'].read()
            logger.info(f"✓ Object downloaded successfully ({len(data)} bytes)")
            return data
        except Exception as e:
            logger.error(f"✗ Download failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def delete_object(key):
        """
        Delete an object from S3.
        
        Args:
            key: S3 object key
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting object from S3: {key}")
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
            logger.info("✓ Object deleted successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Delete failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def generate_presigned_url(key, expiration=3600):
        """
        Generate a presigned URL for an object.
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            Presigned URL string
        """
        try:
            logger.info(f"Generating presigned URL for: {key} (expires in {expiration}s)")
            
            # Create a separate client with the endpoint URL for generating presigned URLs
            # This ensures URLs are accessible from the client (not internal Docker IP)
            s3_presigned_client = boto3.client(
                's3',
                endpoint_url=S3_ENDPOINT_URL
            )
            
            url = s3_presigned_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': key},
                ExpiresIn=expiration
            )
            
            # Replace internal Docker IP with localhost if it appears
            if '172.17.0.2' in url:
                logger.info("Replacing internal Docker IP with localhost in presigned URL")
                url = url.replace('172.17.0.2', 'localhost')
            
            logger.info("✓ Presigned URL generated")
            return url
        except Exception as e:
            logger.error(f"✗ Presigned URL generation failed: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def list_objects(prefix):
        """
        List objects with a given prefix.
        
        Args:
            prefix: S3 prefix
        
        Returns:
            List of object keys
        """
        try:
            logger.info(f"Listing objects with prefix: {prefix}")
            response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=prefix
            )
            contents = response.get('Contents', [])
            keys = [obj['Key'] for obj in contents]
            logger.info(f"✓ Found {len(keys)} objects")
            return keys
        except Exception as e:
            logger.error(f"✗ List objects failed: {str(e)}", exc_info=True)
            raise
