"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
Get Handler - GET /images/{imageId}
"""

import json
from services.image_service import ImageService
from utils.logger import get_logger
from utils.response import error_response, success_response

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Get image metadata and generate presigned URLs for all variants.
    
    Path parameter: imageId (from /images/{imageId})
    Returns: download_urls for original, medium, and thumbnail
    """
    logger.info("=== IMAGE GET STARTED ===")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    try:
        # Extract image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('imageId') or path_params.get('image_id')
        
        logger.info(f"Path parameters: {path_params}")
        logger.info(f"Image ID: {image_id}")
        
        if not image_id or image_id.strip() == '':
            logger.warning("Missing or empty imageId parameter")
            return error_response(400, "imageId is required and cannot be empty")
        
        logger.info(f"Retrieving image: {image_id}")
        image = ImageService.find_by_image_id(image_id)
        
        if not image:
            logger.warning(f"Image not found: {image_id}")
            return error_response(404, f'Image not found: {image_id}')
        
        logger.info(f"Found image - User: {image.get('user_id')}, Status: {image.get('processing_status')}")
        
        s3_folder = image.get('s3_folder')
        variants = image.get('variants', ['original', 'medium', 'thumbnail'])
        
        logger.info(f"Generating presigned URLs for {len(variants)} variant(s)")
        presigned_urls = ImageService.generate_download_urls(s3_folder, variants)
        
        # Remove sensitive fields from metadata
        metadata = {k: v for k, v in image.items() if k not in ['PK', 'SK']}
        
        response_data = {
            'image_id': image_id,
            'metadata': metadata,
            'download_urls': presigned_urls,
            'default_url': presigned_urls.get('medium') or presigned_urls.get('original')
        }
        
        logger.info("=== IMAGE GET COMPLETED SUCCESSFULLY ===")
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error retrieving image: {str(e)}", exc_info=True)
        return error_response(500, f'Failed to retrieve image: {str(e)}')
