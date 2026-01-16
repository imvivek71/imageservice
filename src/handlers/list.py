"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
List Handler - GET /images
"""

import json
from services.image_service import ImageService
from utils.logger import get_logger
from utils.response import error_response, success_response

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    List all images with optional filters (user_id, tag).
    
    Query parameters:
    - user_id: Filter by user ID (REQUIRED)
    - tag: Filter by tag (optional)
    
    Returns: Array of image metadata
    """
    logger.info("=== IMAGE LIST STARTED ===")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    try:
        query_params = event.get('queryStringParameters') or {}
        logger.info(f"Raw query params: {query_params}")
        
        user_id = query_params.get('user_id', '').strip() if query_params.get('user_id') else None
        tag = query_params.get('tag', '').strip() if query_params.get('tag') else None
        
        logger.info(f"Parsed - User ID: '{user_id}', Tag: '{tag}'")
        
        if not user_id:
            logger.warning("Missing user_id parameter")
            return error_response(400, "user_id is required. Usage: /images?user_id=<your_user_id>&tag=<optional_tag>")
        
        logger.info(f"Fetching images for user: {user_id}")
        images = ImageService.get_images_by_user(user_id, tag)
        logger.info(f"Found {len(images)} image(s)")
        
        # Log each image for debugging
        for img in images:
            logger.info(f"  - Image: {img.get('image_id')}, Status: {img.get('processing_status')}")
        
        response_data = {
            'count': len(images),
            'user_id': user_id,
            'tag_filter': tag,
            'images': images
        }
        
        logger.info(f"=== IMAGE LIST COMPLETED - {len(images)} images ===")
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}", exc_info=True)
        return error_response(500, f'Failed to list images: {str(e)}')
