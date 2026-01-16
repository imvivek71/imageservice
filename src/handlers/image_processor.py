"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
Image Processor Handler - Processes S3 events to create image variants
"""

import json
from io import BytesIO
from PIL import Image
from math import gcd
from services.s3_service import S3Service
from services.dynamodb_service import DynamoDBService
from utils.logger import get_logger
from utils.response import json_response

logger = get_logger(__name__)

# Image size variants to create
IMAGE_VARIANTS = {
    'medium': {'max_size': (1024, 1024)},
    'thumbnail': {'max_size': (200, 200)}
}


def resize_image(image_data, max_size):
    """
    Resize image to specified dimensions while maintaining aspect ratio.
    
    Args:
        image_data: Binary image data
        max_size: Tuple (width, height)
    
    Returns:
        Tuple (resized_image_bytes, (width, height), format)
    """
    try:
        img = Image.open(BytesIO(image_data))
        original_size = img.size
        
        # Resize maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Save as JPEG
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        logger.info(f"✓ Resized image from {original_size} to {img.size}")
        return output.getvalue(), img.size, 'JPEG'
    
    except Exception as e:
        logger.error(f"✗ Error resizing image: {str(e)}", exc_info=True)
        raise


def extract_metadata_from_key(s3_key):
    """
    Extract user_id and image_id from S3 key.
    
    Expected format: images/user_id={user_id}/image_id={image_id}/original.jpg
    """
    try:
        parts = s3_key.split('/')
        user_id = None
        image_id = None
        
        for part in parts:
            if part.startswith('user_id='):
                user_id = part.split('=')[1]
            elif part.startswith('image_id='):
                image_id = part.split('=')[1]
        
        logger.info(f"Extracted from S3 key - User: {user_id}, Image: {image_id}")
        return user_id, image_id
    except Exception as e:
        logger.error(f"✗ Error extracting metadata from key {s3_key}: {str(e)}")
        return None, None


def get_image_dimensions(image_data):
    """Get image dimensions from binary data."""
    try:
        img = Image.open(BytesIO(image_data))
        return img.size
    except Exception as e:
        logger.error(f"✗ Error getting image dimensions: {str(e)}")
        return (0, 0)


def lambda_handler(event, context):
    """
    Process S3 PutObject event and create image variants.
    
    Triggered by: S3 PutObject event for images/user_id=*/image_id=*/original.jpg
    
    Process:
    1. Read original.jpg from S3
    2. Create medium.jpg (1024x1024)
    3. Create thumbnail.jpg (200x200)
    4. Upload variants to same S3 folder
    5. Update DynamoDB with image dimensions and variants
    """
    logger.info("=== IMAGE PROCESSOR STARTED ===")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    try:
        # Parse S3 event
        records = event.get('Records', [])
        
        if not records:
            logger.warning("✗ No records in event")
            return json_response(400, {'error': 'No records in event'})
        
        # Process first record (typically only one)
        record = records[0]
        bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']
        
        logger.info(f"Processing S3 object: s3://{bucket}/{s3_key}")
        
        # Only process original images
        if not s3_key.endswith('/original.jpg'):
            logger.info(f"Skipping non-original image: {s3_key}")
            return json_response(200, {'message': 'Skipped non-original image'})
        
        # Extract metadata from S3 key
        user_id, image_id = extract_metadata_from_key(s3_key)
        if not user_id or not image_id:
            logger.error(f"✗ Could not extract metadata from {s3_key}")
            return json_response(400, {'error': 'Invalid S3 key format'})
        
        # Download original image from S3
        try:
            logger.info(f"Downloading original image...")
            original_image_data = S3Service.download_object(s3_key)
        except Exception as e:
            logger.error(f"✗ Error downloading original image: {str(e)}")
            return json_response(500, {'error': f'Failed to download image: {str(e)}'})
        
        # Get original image dimensions
        original_width, original_height = get_image_dimensions(original_image_data)
        logger.info(f"Original image dimensions: {original_width}x{original_height}")
        
        # Extract S3 folder from key
        s3_folder = '/'.join(s3_key.split('/')[:-1])
        
        # Create and upload variants
        uploaded_variants = ['original']
        
        for variant_name, config in IMAGE_VARIANTS.items():
            try:
                logger.info(f"Creating {variant_name} variant...")
                
                # Resize image
                resized_data, resized_size, img_format = resize_image(
                    original_image_data,
                    config['max_size']
                )
                
                # Upload to S3
                variant_s3_key = f"{s3_folder}/{variant_name}.jpg"
                S3Service.upload_object(
                    variant_s3_key,
                    resized_data,
                    content_type='image/jpeg',
                    metadata={
                        'user_id': user_id,
                        'image_id': image_id,
                        'variant': variant_name
                    }
                )
                
                uploaded_variants.append(variant_name)
                logger.info(f"✓ Uploaded {variant_name} variant ({resized_size[0]}x{resized_size[1]})")
            
            except Exception as e:
                logger.error(f"✗ Error creating {variant_name} variant: {str(e)}")
        
        # Calculate aspect ratio
        if original_width and original_height:
            common_divisor = gcd(original_width, original_height)
            aspect_ratio = f"{original_width//common_divisor}:{original_height//common_divisor}"
        else:
            aspect_ratio = '1:1'
        
        logger.info(f"Aspect ratio: {aspect_ratio}")
        
        # Update DynamoDB with image dimensions and variants
        try:
            pk = f"USER#{user_id}"
            
            # Query to find the exact SK for this image
            logger.info(f"Finding image in DynamoDB...")
            items = DynamoDBService.query_by_pk(pk, reverse=False)  # All items, we'll filter
            
            matching_items = [item for item in items if item.get('image_id') == image_id]
            
            if not matching_items:
                logger.error(f"✗ Could not find image metadata for {image_id}")
                return json_response(404, {'error': 'Image metadata not found'})
            
            item = matching_items[0]
            sk = item['SK']
            
            logger.info(f"Updating image metadata...")
            # Update item with dimensions and variants
            DynamoDBService.update_item(
                pk,
                sk,
                'SET #width = :width, #height = :height, #aspect = :aspect, #variants = :variants, #status = :status',
                {
                    ':width': original_width,
                    ':height': original_height,
                    ':aspect': aspect_ratio,
                    ':variants': uploaded_variants,
                    ':status': 'completed'
                },
                {
                    '#width': 'width',
                    '#height': 'height',
                    '#aspect': 'aspect_ratio',
                    '#variants': 'variants',
                    '#status': 'processing_status'
                }
            )
            
            logger.info(f"✓ Updated DynamoDB with image dimensions and variants")
        
        except Exception as e:
            logger.error(f"✗ Error updating DynamoDB: {str(e)}", exc_info=True)
            return json_response(500, {'error': f'Failed to update metadata: {str(e)}'})
        
        response_data = {
            'message': 'Image processed successfully',
            'image_id': image_id,
            'original_dimensions': f"{original_width}x{original_height}",
            'aspect_ratio': aspect_ratio,
            'variants_created': uploaded_variants
        }
        
        logger.info("=== IMAGE PROCESSOR COMPLETED SUCCESSFULLY ===")
        return json_response(200, response_data)
    
    except Exception as e:
        logger.error(f"✗ Unexpected error processing image: {str(e)}", exc_info=True)
        return json_response(500, {'error': str(e)})
