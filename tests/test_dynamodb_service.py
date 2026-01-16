"""
Tests for DynamoDB Service
"""

import pytest
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.dynamodb_service import DynamoDBService


class TestDynamoDBService:
    """Test DynamoDB Service operations."""
    
    def test_put_item_success(self):
        """Test successful item insertion."""
        mock_table = Mock()
        
        with patch('services.dynamodb_service.table', mock_table):
            item = {
                'PK': 'USER#vivek12345',
                'SK': 'IMAGE#2026-01-16T10:00:00.000000Z#img-123',
                'image_id': 'img-123',
                'user_id': 'vivek12345'
            }
            
            result = DynamoDBService.put_item(item)
            
            assert result is True
            mock_table.put_item.assert_called_once_with(Item=item)
    
    def test_put_item_failure(self):
        """Test put_item with exception."""
        mock_table = Mock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        with patch('services.dynamodb_service.table', mock_table):
            item = {'PK': 'USER#test', 'SK': 'IMAGE#test#123'}
            
            with pytest.raises(Exception):
                DynamoDBService.put_item(item)
    
    def test_get_item_success(self):
        """Test successful item retrieval."""
        mock_table = Mock()
        mock_item = {
            'PK': 'USER#vivek12345',
            'SK': 'IMAGE#2026-01-16T10:00:00.000000Z#img-123',
            'image_id': 'img-123'
        }
        mock_table.get_item.return_value = {'Item': mock_item}
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.get_item('USER#vivek12345', 'IMAGE#2026-01-16T10:00:00.000000Z#img-123')
            
            assert result == mock_item
            mock_table.get_item.assert_called_once()
    
    def test_get_item_not_found(self):
        """Test get_item when item doesn't exist."""
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.get_item('USER#vivek12345', 'IMAGE#nonexistent')
            
            assert result is None
    
    def test_query_by_pk_success(self):
        """Test successful query by partition key."""
        mock_table = Mock()
        mock_items = [
            {'image_id': 'img-1', 'created_at': '2026-01-16T10:00:00Z'},
            {'image_id': 'img-2', 'created_at': '2026-01-15T10:00:00Z'}
        ]
        mock_table.query.return_value = {'Items': mock_items}
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.query_by_pk('USER#vivek12345')
            
            assert result == mock_items
            mock_table.query.assert_called_once()
    
    def test_scan_success(self):
        """Test successful scan."""
        mock_table = Mock()
        mock_items = [
            {'image_id': 'img-1', 'user_id': 'user1'},
            {'image_id': 'img-2', 'user_id': 'user2'}
        ]
        mock_table.scan.return_value = {'Items': mock_items}
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.scan()
            
            assert result == mock_items
    
    def test_update_item_success(self):
        """Test successful item update."""
        mock_table = Mock()
        updated_item = {'image_id': 'img-123', 'width': 1024, 'height': 768}
        mock_table.update_item.return_value = {'Attributes': updated_item}
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.update_item(
                'USER#vivek12345',
                'IMAGE#2026-01-16#img-123',
                'SET #width = :width, #height = :height',
                {':width': 1024, ':height': 768},
                {'#width': 'width', '#height': 'height'}
            )
            
            assert result == updated_item
    
    def test_delete_item_success(self):
        """Test successful item deletion."""
        mock_table = Mock()
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.delete_item('USER#vivek12345', 'IMAGE#2026-01-16#img-123')
            
            assert result is True
            mock_table.delete_item.assert_called_once()
    
    def test_scan_by_attribute_success(self):
        """Test scan by attribute."""
        mock_table = Mock()
        mock_items = [{'image_id': 'img-123', 'is_deleted': False}]
        mock_table.scan.return_value = {'Items': mock_items}
        
        with patch('services.dynamodb_service.table', mock_table):
            result = DynamoDBService.scan_by_attribute('image_id', 'img-123')
            
            assert result == mock_items
            mock_table.scan.assert_called_once()
