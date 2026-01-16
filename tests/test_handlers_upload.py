"""
Tests for Upload Handler
"""

import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers.upload import lambda_handler


class TestUploadHandler:
    """Test Upload Handler."""
    
    def test_upload_missing_user_id(self):
        """Test upload without user_id parameter."""
        event = {
            'httpMethod': 'POST',
            'queryStringParameters': {},
            'body': 'image data'
        }
        context = Mock()
        response = lambda_handler(event, context)
        assert response['statusCode'] == 400
