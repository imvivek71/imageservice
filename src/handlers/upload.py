"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
Upload Handler - POST /images
"""

import json
import uuid
from datetime import datetime
from base64 import b64decode
from services.dynamodb_service import DynamoDBService
from services.s3_service import S3Service
from utils.logger import get_logger
from utils.response import error_response, success_response

logger = get_logger(__name__)

BUCKET_NAME = 'image-service-bucket'


def lambda_handler(event, context):
    """
    Upload an image (original only).
    Image resizing will be handled by a separate Lambda triggered by S3 PutObject event.
    
    Query Parameters (Required):
    - user_id: User identifier (required)
    
    Query Parameters (Optional):
    - tags: Comma-separated tags (e.g., "tag1,tag2")
    - description: Image description
    """
    logger.info("=== IMAGE UPLOAD STARTED ===")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    try:
        # Extract and validate query parameters
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        
        # Validate required parameters
        if not user_id or user_id.strip() == '':
            logger.warning("Missing or empty user_id parameter")
            return error_response(400, "user_id is required and cannot be empty")
        
        logger.info(f"User ID: {user_id}")
        
        tags = query_params.get('tags', '').split(',') if query_params.get('tags') else []
        tags = [t.strip() for t in tags if t.strip()]  # Clean tags
        description = query_params.get('description', '').strip()
        
        logger.info(f"Tags: {tags}, Description: {description}")
        
        # Parse the request body
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        logger.info(f"Body size: {len(body)} bytes, Base64 encoded: {is_base64}")
        
        if is_base64:
            body = b64decode(body)
        else:
            body = body.encode() if isinstance(body, str) else body
        
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
            logger.info(f"Uploading original image to S3: {s3_key}")
            S3Service.upload_object(
                s3_key,
                body,
                content_type='image/jpeg',
                metadata={
                    'user_id': user_id,
                    'image_id': image_id,
                    'created_at': created_at
                }
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}", exc_info=True)
            return error_response(500, f'S3 upload failed: {str(e)}')
        
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
            's3_prefix': s3_folder,
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
            'variants': ['original'],
            'processing_status': 'pending'
        }
        
        try:
            logger.info(f"Storing metadata in DynamoDB")
            DynamoDBService.put_item(item)
        except Exception as e:
            logger.error(f"DynamoDB put_item failed: {str(e)}", exc_info=True)
            # Clean up S3 if DynamoDB fails
            try:
                S3Service.delete_object(s3_key)
                logger.info("Cleaned up S3 object after DynamoDB failure")
            except:
                pass
            return error_response(500, f'Failed to store metadata: {str(e)}')
        
        response_data = {
            'message': 'Image uploaded successfully. Processing variants...',
            'image_id': image_id,
            'processing_status': 'pending',
            'metadata': {k: v for k, v in item.items() if k not in ['PK', 'SK']}
        }
        
        logger.info("=== IMAGE UPLOAD COMPLETED SUCCESSFULLY ===")
        return success_response(201, response_data)
    
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        return error_response(500, f'Upload failed: {str(e)}')
