"""
Tests for List Handler
"""

import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers.list import lambda_handler


class TestListHandler:
    """Test List Handler."""
    
    def test_list_missing_user_id(self):
        """Test list without user_id parameter."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {}
        }
        context = Mock()
        response = lambda_handler(event, context)
        assert response['statusCode'] == 400
