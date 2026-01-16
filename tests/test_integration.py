"""
Integration Tests
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBasicWorkflows:
    """Test basic workflows."""
    
    def test_imports_work(self):
        """Test that all imports work correctly."""
        from handlers.upload import lambda_handler as upload_handler
        from handlers.get import lambda_handler as get_handler
        from handlers.list import lambda_handler as list_handler
        from handlers.delete import lambda_handler as delete_handler
        from services.dynamodb_service import DynamoDBService
        from services.s3_service import S3Service
        from services.image_service import ImageService
        
        assert upload_handler is not None
        assert get_handler is not None
        assert list_handler is not None
        assert delete_handler is not None
        assert DynamoDBService is not None
        assert S3Service is not None
        assert ImageService is not None
