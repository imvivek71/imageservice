"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
Delete Handler - DELETE /images/{imageId}
"""

import json
from services.dynamodb_service import DynamoDBService
from services.image_service import ImageService
from utils.logger import get_logger
from utils.response import error_response, success_response

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Delete an image (soft delete in DynamoDB, hard delete from S3).
    
    Path parameter: imageId (from /images/{imageId})
    """
    logger.info("=== IMAGE DELETE STARTED ===")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    try:
        # Extract image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('imageId') or path_params.get('image_id')
        
        logger.info(f"Path parameters: {path_params}")
        logger.info(f"Image ID to delete: {image_id}")
        
        if not image_id or image_id.strip() == '':
            logger.warning("Missing or empty imageId parameter")
            return error_response(400, "imageId is required and cannot be empty")
        
        logger.info(f"Finding image: {image_id}")
        image = ImageService.find_by_image_id(image_id)
        
        if not image:
            logger.warning(f"Image not found or already deleted: {image_id}")
            return error_response(404, f'Image not found: {image_id}')
        
        pk = image['PK']
        sk = image['SK']
        s3_folder = image.get('s3_folder')
        user_id = image.get('user_id')
        
        logger.info(f"Found image for user: {user_id}, S3 folder: {s3_folder}")
        
        # Soft delete in DynamoDB
        logger.info(f"Marking image as deleted")
        ImageService.soft_delete_image(pk, sk)
        
        # Hard delete from S3
        deleted_count = 0
        if s3_folder:
            logger.info(f"Deleting S3 variants")
            deleted_count = ImageService.delete_image_variants(s3_folder)
        else:
            logger.warning("No S3 folder found for this image")
        
        response_data = {
            'message': 'Image deleted successfully',
            'image_id': image_id,
            's3_variants_deleted': deleted_count
        }
        
        logger.info("=== IMAGE DELETE COMPLETED SUCCESSFULLY ===")
        return success_response(204, response_data)
    
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        return error_response(500, f'Failed to delete image: {str(e)}')
