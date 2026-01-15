"""
Author: Vivek Kuumar Goswami
Date: January 15, 2026
"""

import json
import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageService')

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    List all images with optional filters (user_id, tag).
    
    Query parameters:
    - user_id: Filter by user ID
    - tag: Filter by tag
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        tag = query_params.get('tag')
        
        images = []
        
        if user_id:
            # Query by user_id (PK)
            pk = f"USER#{user_id}"
            response = table.query(
                KeyConditionExpression=Key('PK').eq(pk),
                ScanIndexForward=False  # Latest first
            )
            images = response.get('Items', [])
        else:
            # Scan all images (not recommended for production)
            response = table.scan()
            images = response.get('Items', [])
        
        # Filter by tag if provided
        if tag:
            images = [img for img in images if tag in img.get('tags', [])]
        
        # Filter out deleted images
        images = [img for img in images if not img.get('is_deleted', False)]
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(images),
                'images': images
            })
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
