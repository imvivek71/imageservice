"""
Tests for Image Service
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.image_service import ImageService


class TestImageService:
    """Test Image Service."""
    
    def test_image_service_exists(self):
        """Test that ImageService can be instantiated."""
        service = ImageService()
        assert service is not None
