"""
Author: Vivek Kuumar Goswami
Date: January 16, 2026
DynamoDB Service Layer - All database operations
"""

import os
import boto3
from boto3.dynamodb.conditions import Key
from utils.logger import get_logger

logger = get_logger(__name__)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'ImageService')
table = dynamodb.Table(TABLE_NAME)


class DynamoDBService:
    """Service for all DynamoDB operations."""
    
    @staticmethod
    def put_item(item):
        """
        Insert or update an item in DynamoDB.
        
        Args:
            item: Item dictionary with PK, SK, and other attributes
        
        Raises:
            Exception: If put_item fails
        """
        try:
            logger.info(f"Storing item in DynamoDB: PK={item.get('PK')}, SK={item.get('SK')}")
            table.put_item(Item=item)
            logger.info("✓ Item stored successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to put item: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def get_item(pk, sk):
        """
        Retrieve an item from DynamoDB.
        
        Args:
            pk: Partition key
            sk: Sort key
        
        Returns:
            Item dictionary or None if not found
        """
        try:
            logger.info(f"Retrieving item from DynamoDB: PK={pk}, SK={sk}")
            response = table.get_item(Key={'PK': pk, 'SK': sk})
            item = response.get('Item')
            logger.info(f"✓ Item retrieved: {item is not None}")
            return item
        except Exception as e:
            logger.error(f"✗ Failed to get item: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def query_by_pk(pk, reverse=True):
        """
        Query items by partition key.
        
        Args:
            pk: Partition key
            reverse: If True, return latest first
        
        Returns:
            List of items
        """
        try:
            logger.info(f"Querying items by PK: {pk}")
            response = table.query(
                KeyConditionExpression=Key('PK').eq(pk),
                ScanIndexForward=not reverse
            )
            items = response.get('Items', [])
            logger.info(f"✓ Found {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"✗ Query failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def scan(filter_expression=None, expression_values=None):
        """
        Scan table with optional filtering.
        
        Args:
            filter_expression: DynamoDB filter expression
            expression_values: Expression attribute values
        
        Returns:
            List of items
        """
        try:
            logger.info("Scanning table")
            params = {}
            if filter_expression:
                params['FilterExpression'] = filter_expression
            if expression_values:
                params['ExpressionAttributeValues'] = expression_values
            
            response = table.scan(**params)
            items = response.get('Items', [])
            logger.info(f"✓ Scan found {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"✗ Scan failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def update_item(pk, sk, update_expression, expression_values, expression_names=None):
        """
        Update an item in DynamoDB.
        
        Args:
            pk: Partition key
            sk: Sort key
            update_expression: DynamoDB update expression
            expression_values: Expression attribute values
            expression_names: Optional expression attribute names
        
        Returns:
            Updated item
        """
        try:
            logger.info(f"Updating item: PK={pk}, SK={sk}")
            params = {
                'Key': {'PK': pk, 'SK': sk},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values,
                'ReturnValues': 'ALL_NEW'
            }
            if expression_names:
                params['ExpressionAttributeNames'] = expression_names
            
            response = table.update_item(**params)
            logger.info("✓ Item updated successfully")
            return response.get('Attributes')
        except Exception as e:
            logger.error(f"✗ Update failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def delete_item(pk, sk):
        """
        Delete an item from DynamoDB.
        
        Args:
            pk: Partition key
            sk: Sort key
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting item: PK={pk}, SK={sk}")
            table.delete_item(Key={'PK': pk, 'SK': sk})
            logger.info("✓ Item deleted successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Delete failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def scan_by_attribute(attribute_name, attribute_value, not_deleted=True):
        """
        Scan for items by a specific attribute.
        
        Args:
            attribute_name: Attribute to search
            attribute_value: Value to match
            not_deleted: If True, filter out deleted items
        
        Returns:
            List of matching items
        """
        try:
            logger.info(f"Scanning by attribute: {attribute_name}={attribute_value}")
            filter_expr = f"{attribute_name} = :val"
            expr_values = {':val': attribute_value}
            
            if not_deleted:
                filter_expr += " AND is_deleted = :deleted"
                expr_values[':deleted'] = False
            
            response = table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues=expr_values
            )
            items = response.get('Items', [])
            logger.info(f"✓ Found {len(items)} matching items")
            return items
        except Exception as e:
            logger.error(f"✗ Scan by attribute failed: {str(e)}", exc_info=True)
            raise
