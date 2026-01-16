"""
Tests for S3 Service
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.s3_service import S3Service


class TestS3Service:
    """Test S3 Service operations."""
    
    def test_upload_object_success(self):
        """Test successful object upload."""
        mock_client = Mock()
        body = b'test image data'
        
        with patch('services.s3_service.s3_client', mock_client):
            result = S3Service.upload_object(
                'images/user123/img-123/original.jpg',
                body,
                content_type='image/jpeg',
                metadata={'user_id': 'user123'}
            )
            
            assert result is True
            mock_client.put_object.assert_called_once()
    
    def test_upload_object_failure(self):
        """Test upload_object with exception."""
        mock_client = Mock()
        mock_client.put_object.side_effect = Exception("S3 error")
        
        with patch('services.s3_service.s3_client', mock_client):
            with pytest.raises(Exception):
                S3Service.upload_object('images/user123/img-123/original.jpg', b'data')
    
    def test_download_object_success(self):
        """Test successful object download."""
        mock_client = Mock()
        mock_body = Mock()
        mock_body.read.return_value = b'test image data'
        mock_client.get_object.return_value = {'Body': mock_body}
        
        with patch('services.s3_service.s3_client', mock_client):
            result = S3Service.download_object('images/user123/img-123/original.jpg')
            
            assert result == b'test image data'
            mock_client.get_object.assert_called_once()
    
    def test_download_object_failure(self):
        """Test download_object with exception."""
        mock_client = Mock()
        mock_client.get_object.side_effect = Exception("S3 error")
        
        with patch('services.s3_service.s3_client', mock_client):
            with pytest.raises(Exception):
                S3Service.download_object('images/user123/img-123/original.jpg')
    
    def test_delete_object_success(self):
        """Test successful object deletion."""
        mock_client = Mock()
        
        with patch('services.s3_service.s3_client', mock_client):
            result = S3Service.delete_object('images/user123/img-123/original.jpg')
            
            assert result is True
            mock_client.delete_object.assert_called_once()
    
    def test_generate_presigned_url_success(self):
        """Test successful presigned URL generation."""
        mock_client = Mock()
        expected_url = 'http://localhost:4566/image-service-bucket/images/user123/img-123/original.jpg?AWSAccessKeyId=test'
        mock_client.generate_presigned_url.return_value = expected_url
        
        with patch('services.s3_service.s3_client', mock_client):
            with patch('services.s3_service.boto3.client', return_value=mock_client):
                result = S3Service.generate_presigned_url('images/user123/img-123/original.jpg')
                
                assert 'original.jpg' in result or result == expected_url
    
    def test_generate_presigned_url_with_internal_ip_replacement(self):
        """Test presigned URL generation with internal IP replacement."""
        mock_client = Mock()
        url_with_internal_ip = 'http://172.17.0.2:4566/image-service-bucket/images/user123/img-123/original.jpg?token=test'
        mock_client.generate_presigned_url.return_value = url_with_internal_ip
        
        with patch('services.s3_service.boto3.client', return_value=mock_client):
            result = S3Service.generate_presigned_url('images/user123/img-123/original.jpg')
            
            # Should replace 172.17.0.2 with localhost
            assert 'localhost' in result
    
    def test_list_objects_success(self):
        """Test successful object listing."""
        mock_client = Mock()
        mock_contents = [
            {'Key': 'images/user123/img-123/original.jpg'},
            {'Key': 'images/user123/img-123/medium.jpg'}
        ]
        mock_client.list_objects_v2.return_value = {'Contents': mock_contents}
        
        with patch('services.s3_service.s3_client', mock_client):
            result = S3Service.list_objects('images/user123/img-123/')
            
            assert len(result) == 2
            assert 'images/user123/img-123/original.jpg' in result
    
    def test_list_objects_empty(self):
        """Test list_objects with no contents."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {}
        
        with patch('services.s3_service.s3_client', mock_client):
            result = S3Service.list_objects('images/nonexistent/')
            
            assert result == []
