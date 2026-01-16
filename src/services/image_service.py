"""
Author: Vivek Kuumar Goswami
Date: January 16, 2026
Image Service - Business logic combining DynamoDB and S3
"""

from services.dynamodb_service import DynamoDBService
from services.s3_service import S3Service
from utils.logger import get_logger
from boto3.dynamodb.conditions import Key

logger = get_logger(__name__)

# Image variants
VARIANTS = ['original', 'medium', 'thumbnail']


class ImageService:
    """Business logic service for image operations."""
    
    @staticmethod
    def find_by_image_id(image_id, not_deleted=True):
        """
        Find an image by image_id.
        
        Args:
            image_id: Image identifier
            not_deleted: If True, exclude deleted images
        
        Returns:
            Image item or None
        """
        logger.info(f"Finding image by ID: {image_id}")
        images = DynamoDBService.scan_by_attribute('image_id', image_id, not_deleted)
        if images:
            logger.info(f"✓ Image found")
            return images[0]
        logger.warning(f"✗ Image not found: {image_id}")
        return None
    
    @staticmethod
    def get_images_by_user(user_id, tag=None, visibility=None):
        """
        Get all images for a user with optional tag and visibility filtering.
        
        Args:
            user_id: User identifier
            tag: Optional tag to filter by
            visibility: Optional visibility to filter by (public, private, followers)
        
        Returns:
            List of image items
        """
        logger.info(f"Getting images for user: {user_id}, tag: {tag}, visibility: {visibility}")
        pk = f"USER#{user_id}"
        images = DynamoDBService.query_by_pk(pk, reverse=True)
        
        # Filter out deleted images
        images = [img for img in images if not img.get('is_deleted', False)]
        logger.info(f"Found {len(images)} non-deleted images")
        
        # Filter by tag if provided
        if tag:
            logger.info(f"Filtering by tag: {tag}")
            images = [img for img in images if tag in img.get('tags', [])]
            logger.info(f"Found {len(images)} images with tag '{tag}'")
        
        # Filter by visibility if provided
        if visibility:
            logger.info(f"Filtering by visibility: {visibility}")
            images = [img for img in images if img.get('visibility') == visibility]
            logger.info(f"Found {len(images)} images with visibility '{visibility}'")
        
        return images
    
    @staticmethod
    def delete_image_variants(s3_folder):
        """
        Delete all image variants from S3.
        
        Args:
            s3_folder: S3 folder path
        
        Returns:
            Number of variants deleted
        """
        logger.info(f"Deleting image variants from S3: {s3_folder}")
        deleted_count = 0
        
        for variant in VARIANTS:
            try:
                s3_key = f"{s3_folder}/{variant}.jpg"
                S3Service.delete_object(s3_key)
                deleted_count += 1
                logger.info(f"✓ Deleted variant: {variant}")
            except Exception as e:
                logger.error(f"✗ Failed to delete variant {variant}: {str(e)}")
        
        logger.info(f"Deleted {deleted_count}/{len(VARIANTS)} variants")
        return deleted_count
    
    @staticmethod
    def generate_download_urls(s3_folder, variants_available):
        """
        Generate presigned URLs for all available variants.
        
        Args:
            s3_folder: S3 folder path
            variants_available: List of available variants
        
        Returns:
            Dictionary of variant -> presigned URL
        """
        logger.info(f"Generating download URLs for {len(variants_available)} variants")
        urls = {}
        
        for variant in VARIANTS:
            if variant in variants_available:
                try:
                    s3_key = f"{s3_folder}/{variant}.jpg"
                    url = S3Service.generate_presigned_url(s3_key)
                    if url:
                        urls[variant] = url
                        logger.info(f"✓ Generated URL for {variant}")
                    else:
                        logger.warning(f"✗ Failed to generate URL for {variant}")
                except Exception as e:
                    logger.error(f"✗ Error generating URL for {variant}: {str(e)}")
                    urls[variant] = None
            else:
                logger.info(f"Skipping {variant} (not available)")
        
        return urls
    
    @staticmethod
    def soft_delete_image(pk, sk):
        """
        Soft delete an image (mark as deleted in DynamoDB).
        
        Args:
            pk: Partition key
            sk: Sort key
        
        Returns:
            True if successful
        """
        logger.info(f"Soft deleting image: PK={pk}, SK={sk}")
        DynamoDBService.update_item(
            pk,
            sk,
            'SET is_deleted = :deleted',
            {':deleted': True}
        )
        logger.info("✓ Image marked as deleted")
        return True
