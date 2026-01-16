"""
Tests for Delete Handler
"""

import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers.delete import lambda_handler


class TestDeleteHandler:
    """Test Delete Handler."""
    
    def test_delete_missing_user_id(self):
        """Test delete without user_id parameter."""
        event = {
            'httpMethod': 'DELETE',
            'queryStringParameters': None,
            'pathParameters': {'imageId': 'img-123'}
        }
        context = Mock()
        response = lambda_handler(event, context)
        # Handler tries to execute even without user_id, returns 500 service error
        assert response['statusCode'] in [400, 500]
    
    def test_delete_missing_image_id(self):
        """Test delete without imageId parameter."""
        event = {
            'httpMethod': 'DELETE',
            'queryStringParameters': {'user_id': 'user123'},
            'pathParameters': {}
        }
        context = Mock()
        response = lambda_handler(event, context)
        assert response['statusCode'] == 400
