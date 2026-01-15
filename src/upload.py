"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
"""

import json
import boto3
import os
import uuid
from datetime import datetime
from io import BytesIO
from base64 import b64decode

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageService')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'image-service-bucket')

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Upload an image (original only).
    Image resizing will be handled by a separate Lambda triggered by S3 PutObject event.
    
    S3 structure: images/user_id={user_id}/image_id={image_id}/
                  └── original.jpg  (will trigger resize Lambda)
    """
    try:
        # Parse the request body
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        if is_base64:
            body = b64decode(body)
        else:
            body = body.encode() if isinstance(body, str) else body
        
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id') or 'unknown_user'
        tags = query_params.get('tags', '').split(',') if query_params.get('tags') else []
        description = query_params.get('description', '')
        
        # Generate unique IDs
        image_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + 'Z'
        
        # S3 folder structure: images/user_id=123/image_id=img_789/
        s3_folder = f"images/user_id={user_id}/image_id={image_id}"
        s3_key = f"{s3_folder}/original.jpg"
        
        # For demo: use test image data if body is empty
        if not body or body == b'':
            # Create a simple test image without Pillow
            test_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPEG header
            body = test_data
        
        # Upload original image to S3
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=body,
                ContentType='image/jpeg',
                Metadata={
                    'user_id': user_id,
                    'image_id': image_id,
                    'created_at': created_at
                }
            )
            print(f"Uploaded original image to {s3_key}")
        except Exception as e:
            print(f"S3 upload error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'S3 upload failed: {str(e)}'})
            }
        
        # Store metadata in DynamoDB
        pk = f"USER#{user_id}"
        sk = f"IMAGE#{created_at}#{image_id}"
        
        item = {
            'PK': pk,
            'SK': sk,
            'image_id': image_id,
            'user_id': user_id,
            's3_bucket': BUCKET_NAME,
            's3_folder': s3_folder,
            's3_prefix': f"images/user_id={user_id}/image_id={image_id}",
            'content_type': 'image/jpeg',
            'size_bytes': len(body),
            'width': 0,
            'height': 0,
            'aspect_ratio': '1:1',
            'visibility': 'public',
            'tags': tags,
            'description': description,
            'created_at': created_at,
            'likes_count': 0,
            'comments_count': 0,
            'is_deleted': False,
            'variants': ['original'],  # Medium and thumbnail will be added by image processor
            'processing_status': 'pending'  # Will be updated by image processor Lambda
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Image uploaded successfully. Processing variants...',
                'image_id': image_id,
                'processing_status': 'pending',
                'metadata': {k: v for k, v in item.items() if k not in ['PK', 'SK']}
            })
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
