"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
"""

import json
import boto3
import os
from boto3.dynamodb.conditions import Key

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageService')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'image-service-bucket')

table = dynamodb.Table(TABLE_NAME)

# Image variants
VARIANTS = ['original', 'medium', 'thumbnail']


def generate_presigned_urls(s3_folder, variants_available):
    """
    Generate presigned URLs for all available image variants.
    
    S3 structure: images/user_id={user_id}/image_id={image_id}/
                  ├── original.jpg
                  ├── medium.jpg
                  └── thumbnail.jpg
    """
    urls = {}
    for variant in VARIANTS:
        if variant in variants_available:
            try:
                s3_key = f"{s3_folder}/{variant}.jpg"
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': BUCKET_NAME,
                        'Key': s3_key
                    },
                    ExpiresIn=3600
                )
                urls[variant] = url
            except Exception as e:
                print(f"Error generating presigned URL for {variant}: {e}")
                urls[variant] = None
    return urls


def lambda_handler(event, context):
    """
    Get image metadata and generate presigned URLs for all variants.
    
    Path parameter: image_id
    Returns: download_urls for original, medium, and thumbnail
    """
    try:
        # Extract image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('image_id')
        
        if not image_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_id is required'})
            }
        
        # Scan for the image
        response = table.scan(
            FilterExpression='image_id = :id AND is_deleted = :deleted',
            ExpressionAttributeValues={
                ':id': image_id,
                ':deleted': False
            }
        )
        
        items = response.get('Items', [])
        
        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Image not found'})
            }
        
        image = items[0]
        s3_folder = image.get('s3_folder')
        variants = image.get('variants', VARIANTS)
        
        # Generate presigned URLs for all variants
        presigned_urls = generate_presigned_urls(s3_folder, variants)
        
        # Remove sensitive fields from metadata
        metadata = {k: v for k, v in image.items() if k not in ['PK', 'SK']}
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'image_id': image_id,
                'metadata': metadata,
                'download_urls': presigned_urls,
                'default_url': presigned_urls.get('medium') or presigned_urls.get('original')
            })
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
