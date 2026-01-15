"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
"""

import json
import boto3
import os
from io import BytesIO
from PIL import Image
import logging

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageService')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'image-service-bucket')

table = dynamodb.Table(TABLE_NAME)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        
        # Convert to RGB if necessary (for PNG with transparency, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Save as JPEG
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        logger.info(f"Resized image from {original_size} to {img.size}")
        return output.getvalue(), img.size, 'JPEG'
    
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        raise


def extract_metadata_from_key(s3_key):
    """
    Extract user_id and image_id from S3 key.
    
    Expected format: images/user_id={user_id}/image_id={image_id}/original.jpg
    """
    try:
        parts = s3_key.split('/')
        # Extract user_id and image_id from path
        user_id = None
        image_id = None
        
        for part in parts:
            if part.startswith('user_id='):
                user_id = part.split('=')[1]
            elif part.startswith('image_id='):
                image_id = part.split('=')[1]
        
        return user_id, image_id
    except Exception as e:
        logger.error(f"Error extracting metadata from key {s3_key}: {e}")
        return None, None


def get_image_dimensions(image_data):
    """
    Get image dimensions.
    """
    try:
        img = Image.open(BytesIO(image_data))
        return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
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
    try:
        # Parse S3 event
        records = event.get('Records', [])
        
        if not records:
            logger.warning("No records in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No records in event'})
            }
        
        # Process first record (typically only one)
        record = records[0]
        bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']
        
        logger.info(f"Processing S3 object: s3://{bucket}/{s3_key}")
        
        # Only process original images
        if not s3_key.endswith('/original.jpg'):
            logger.info(f"Skipping non-original image: {s3_key}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Skipped non-original image'})
            }
        
        # Extract metadata from S3 key
        user_id, image_id = extract_metadata_from_key(s3_key)
        if not user_id or not image_id:
            logger.error(f"Could not extract user_id and image_id from {s3_key}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid S3 key format'})
            }
        
        # Download original image from S3
        try:
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            original_image_data = response['Body'].read()
            logger.info(f"Downloaded original image: {len(original_image_data)} bytes")
        except Exception as e:
            logger.error(f"Error downloading original image: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to download image: {str(e)}'})
            }
        
        # Get original image dimensions
        original_width, original_height = get_image_dimensions(original_image_data)
        logger.info(f"Original image dimensions: {original_width}x{original_height}")
        
        # Extract S3 folder from key
        s3_folder = '/'.join(s3_key.split('/')[:-1])  # Remove /original.jpg
        
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
                s3_client.put_object(
                    Bucket=bucket,
                    Key=variant_s3_key,
                    Body=resized_data,
                    ContentType='image/jpeg',
                    Metadata={
                        'user_id': user_id,
                        'image_id': image_id,
                        'variant': variant_name
                    }
                )
                
                uploaded_variants.append(variant_name)
                logger.info(f"Uploaded {variant_name} variant to {variant_s3_key} ({resized_size[0]}x{resized_size[1]})")
            
            except Exception as e:
                logger.error(f"Error creating {variant_name} variant: {e}")
                # Continue with other variants even if one fails
        
        # Calculate aspect ratio
        if original_width and original_height:
            from math import gcd
            common_divisor = gcd(original_width, original_height)
            aspect_ratio = f"{original_width//common_divisor}:{original_height//common_divisor}"
        else:
            aspect_ratio = '1:1'
        
        # Update DynamoDB with image dimensions and variants
        try:
            pk = f"USER#{user_id}"
            
            # Query to find the exact SK for this image
            response = table.query(
                KeyConditionExpression='PK = :pk',
                FilterExpression='image_id = :id',
                ExpressionAttributeValues={
                    ':pk': pk,
                    ':id': image_id
                }
            )
            
            items = response.get('Items', [])
            if not items:
                logger.error(f"Could not find image metadata for {image_id}")
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Image metadata not found'})
                }
            
            item = items[0]
            sk = item['SK']
            
            # Update item with dimensions and variants
            table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression='SET #width = :width, #height = :height, #aspect = :aspect, #variants = :variants, #status = :status',
                ExpressionAttributeNames={
                    '#width': 'width',
                    '#height': 'height',
                    '#aspect': 'aspect_ratio',
                    '#variants': 'variants',
                    '#status': 'processing_status'
                },
                ExpressionAttributeValues={
                    ':width': original_width,
                    ':height': original_height,
                    ':aspect': aspect_ratio,
                    ':variants': uploaded_variants,
                    ':status': 'completed'
                }
            )
            
            logger.info(f"Updated DynamoDB with image dimensions and variants")
        
        except Exception as e:
            logger.error(f"Error updating DynamoDB: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to update metadata: {str(e)}'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image processed successfully',
                'image_id': image_id,
                'original_dimensions': f"{original_width}x{original_height}",
                'aspect_ratio': aspect_ratio,
                'variants_created': uploaded_variants
            })
        }
    
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
