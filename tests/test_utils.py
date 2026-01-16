"""
Tests for Utils
"""

import pytest
import json
from decimal import Decimal
from unittest.mock import Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.response import DecimalEncoder, error_response, success_response
from utils.logger import get_logger


class TestDecimalEncoder:
    """Test Decimal JSON Encoder."""
    
    def test_encode_decimal_to_float(self):
        """Test encoding Decimal to float."""
        data = {
            'price': Decimal('19.99'),
            'quantity': Decimal('5')
        }
        
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        
        assert parsed['price'] == 19.99
        assert parsed['quantity'] == 5
        assert isinstance(parsed['price'], float)
    
    def test_encode_nested_decimal(self):
        """Test encoding nested Decimal values."""
        data = {
            'items': [
                {'price': Decimal('19.99')},
                {'price': Decimal('29.99')}
            ]
        }
        
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        
        assert parsed['items'][0]['price'] == 19.99
        assert parsed['items'][1]['price'] == 29.99
    
    def test_encode_mixed_types(self):
        """Test encoding mixed types with Decimal."""
        data = {
            'name': 'test',
            'count': 10,
            'price': Decimal('99.99'),
            'tags': ['a', 'b'],
            'active': True
        }
        
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        
        assert parsed['name'] == 'test'
        assert parsed['count'] == 10
        assert parsed['price'] == 99.99
        assert parsed['tags'] == ['a', 'b']
        assert parsed['active'] is True
    
    def test_encode_decimal_large_number(self):
        """Test encoding large Decimal number."""
        data = {'big_number': Decimal('999999999.99')}
        
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        
        assert parsed['big_number'] == 999999999.99


class TestResponseFunctions:
    """Test response utility functions."""
    
    def test_error_response_with_message(self):
        """Test error_response function."""
        response = error_response(400, 'Test error')
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Test error'
    
    def test_error_response_with_custom_message(self):
        """Test error_response with custom message."""
        response = error_response(500, 'Server error')
        
        assert response['statusCode'] == 500
    
    def test_success_response_with_data(self):
        """Test success_response function."""
        data = {'id': 'test-123', 'name': 'Test'}
        response = success_response(200, data)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['id'] == 'test-123'
        assert body['name'] == 'Test'
    
    def test_success_response_with_decimal_data(self):
        """Test success_response with Decimal data."""
        data = {
            'id': 'test-123',
            'price': Decimal('99.99')
        }
        response = success_response(200, data)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['price'] == 99.99
    
    def test_error_response_with_decimal_data(self):
        """Test error_response with Decimal in error dict."""
        response = error_response(400, 'Amount exceeds limit')
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


class TestLogger:
    """Test logger utility."""
    
    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger(__name__)
        
        assert logger is not None
        # Logger should have standard methods
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'critical')
    
    def test_logger_can_log_messages(self):
        """Test logger can log messages."""
        logger = get_logger(__name__)
        
        # Should not raise any exception
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')
        logger.critical('Critical message')
    
    def test_multiple_loggers_same_name(self):
        """Test getting multiple logger instances with same name."""
        logger1 = get_logger('test_logger')
        logger2 = get_logger('test_logger')
        
        # Should return the same logger instance
        assert logger1.name == logger2.name
