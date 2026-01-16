"""
Author: Vivek Kuumar Goswami
Date: January 16, 2026
Response formatting - standardized API responses
"""

import json
from decimal import Decimal
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def json_response(status_code, body):
    """
    Create a properly formatted API response.
    
    Args:
        status_code: HTTP status code
        body: Response body (dict or list)
    
    Returns:
        Formatted API response
    """
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def error_response(status_code, error_message, request_id=None):
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
        request_id: Optional request ID for tracking
    
    Returns:
        Formatted error response
    """
    error = {
        'error': error_message,
        'status_code': status_code
    }
    if request_id:
        error['request_id'] = request_id
    
    logger.error(f"Error {status_code}: {error_message}")
    return json_response(status_code, error)


def success_response(status_code, data):
    """
    Create a standardized success response.
    
    Args:
        status_code: HTTP status code
        data: Response data (dict or list)
    
    Returns:
        Formatted success response
    """
    logger.info(f"Success {status_code}: Request completed")
    return json_response(status_code, data)
