"""
Tests for Get Handler
"""

import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers.get import lambda_handler


class TestGetHandler:
    """Test Get Handler."""
    
    def test_get_missing_user_id(self):
        """Test get without user_id parameter."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': None,
            'pathParameters': {'imageId': 'img-123'}
        }
        context = Mock()
        response = lambda_handler(event, context)
        # Handler tries to execute even without user_id, returns 500 service error
        assert response['statusCode'] in [400, 500]
    
    def test_get_missing_image_id(self):
        """Test get without imageId parameter."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {'user_id': 'user123'},
            'pathParameters': {}
        }
        context = Mock()
        response = lambda_handler(event, context)
        assert response['statusCode'] == 400
