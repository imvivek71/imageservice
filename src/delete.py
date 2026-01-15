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


def delete_image_variants(s3_folder):
    """
    Delete all image variants from S3.
    
    Deletes: images/user_id={user_id}/image_id={image_id}/
             ├── original.jpg
             ├── medium.jpg
             └── thumbnail.jpg
    """
    deleted_count = 0
    for variant in VARIANTS:
        try:
            s3_key = f"{s3_folder}/{variant}.jpg"
            s3_client.delete_object(
                Bucket=BUCKET_NAME,
                Key=s3_key
            )
            deleted_count += 1
            print(f"Deleted S3 object: {s3_key}")
        except Exception as e:
            print(f"Error deleting {variant} variant from S3: {e}")
    return deleted_count


def lambda_handler(event, context):
    """
    Delete an image (soft delete in DynamoDB, hard delete from S3).
    
    Path parameter: image_id
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
        
        # Find the image
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
        pk = image['PK']
        sk = image['SK']
        s3_folder = image.get('s3_folder')
        user_id = image.get('user_id')
        
        # Soft delete in DynamoDB: mark as deleted
        table.update_item(
            Key={'PK': pk, 'SK': sk},
            UpdateExpression='SET is_deleted = :deleted',
            ExpressionAttributeValues={':deleted': True}
        )
        print(f"Marked image as deleted in DynamoDB: {image_id}")
        
        # Hard delete from S3: remove all variants
        deleted_count = 0
        if s3_folder:
            deleted_count = delete_image_variants(s3_folder)
        
        return {
            'statusCode': 204,
            'body': json.dumps({
                'message': 'Image deleted successfully',
                'image_id': image_id,
                's3_variants_deleted': deleted_count
            })
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
