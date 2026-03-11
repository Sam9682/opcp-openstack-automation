"""Unit tests for authentication and connection management."""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from openstack_sdk.auth_manager import (
    AuthenticationManager,
    ConnectionManager,
    AuthenticationError
)
from config.models import AuthCredentials


class TestAuthenticationManager:
    """Test cases for AuthenticationManager."""
    
    def test_load_credentials_from_env_success(self):
        """Test successful credential loading from environment variables."""
        # Set up environment variables
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_USERNAME': 'test-user',
            'OS_PASSWORD': 'test-password',
            'OS_TENANT_NAME': 'test-tenant',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            auth_manager = AuthenticationManager()
            credentials = auth_manager.load_credentials_from_env()
            
            assert credentials.auth_url == 'https://auth.cloud.ovh.net/v3'
            assert credentials.username == 'test-user'
            assert credentials.password == 'test-password'
            assert credentials.tenant_name == 'test-tenant'
            assert credentials.region == 'GRA7'
            assert credentials.project_name == 'test-tenant'
    
    def test_load_credentials_from_env_with_project_name(self):
        """Test credential loading using OS_PROJECT_NAME instead of OS_TENANT_NAME."""
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_USERNAME': 'test-user',
            'OS_PASSWORD': 'test-password',
            'OS_PROJECT_NAME': 'test-project',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            auth_manager = AuthenticationManager()
            credentials = auth_manager.load_credentials_from_env()
            
            assert credentials.tenant_name == 'test-project'
            assert credentials.project_name == 'test-project'
    
    def test_load_credentials_from_env_missing_auth_url(self):
        """Test error when OS_AUTH_URL is missing."""
        env_vars = {
            'OS_USERNAME': 'test-user',
            'OS_PASSWORD': 'test-password',
            'OS_TENANT_NAME': 'test-tenant',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            auth_manager = AuthenticationManager()
            
            with pytest.raises(AuthenticationError) as exc_info:
                auth_manager.load_credentials_from_env()
            
            assert 'OS_AUTH_URL' in str(exc_info.value)
    
    def test_load_credentials_from_env_missing_username(self):
        """Test error when OS_USERNAME is missing."""
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_PASSWORD': 'test-password',
            'OS_TENANT_NAME': 'test-tenant',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            auth_manager = AuthenticationManager()
            
            with pytest.raises(AuthenticationError) as exc_info:
                auth_manager.load_credentials_from_env()
            
            assert 'OS_USERNAME' in str(exc_info.value)
    
    def test_load_credentials_from_env_missing_password(self):
        """Test error when OS_PASSWORD is missing."""
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_USERNAME': 'test-user',
            'OS_TENANT_NAME': 'test-tenant',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            auth_manager = AuthenticationManager()
            
            with pytest.raises(AuthenticationError) as exc_info:
                auth_manager.load_credentials_from_env()
            
            assert 'OS_PASSWORD' in str(exc_info.value)
    
    def test_load_credentials_from_env_missing_tenant(self):
        """Test error when both OS_TENANT_NAME and OS_PROJECT_NAME are missing."""
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_USERNAME': 'test-user',
            'OS_PASSWORD': 'test-password',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            auth_manager = AuthenticationManager()
            
            with pytest.raises(AuthenticationError) as exc_info:
                auth_manager.load_credentials_from_env()
            
            assert 'OS_TENANT_NAME or OS_PROJECT_NAME' in str(exc_info.value)
    
    def test_load_credentials_from_env_missing_region(self):
        """Test error when OS_REGION_NAME is missing."""
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_USERNAME': 'test-user',
            'OS_PASSWORD': 'test-password',
            'OS_TENANT_NAME': 'test-tenant'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            auth_manager = AuthenticationManager()
            
            with pytest.raises(AuthenticationError) as exc_info:
                auth_manager.load_credentials_from_env()
            
            assert 'OS_REGION_NAME' in str(exc_info.value)
    
    def test_load_credentials_from_file_success(self):
        """Test successful credential loading from file."""
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("OS_AUTH_URL=https://auth.cloud.ovh.net/v3\n")
            f.write("OS_USERNAME=test-user\n")
            f.write("OS_PASSWORD=test-password\n")
            f.write("OS_TENANT_NAME=test-tenant\n")
            f.write("OS_REGION_NAME=GRA7\n")
            temp_file = f.name
        
        try:
            auth_manager = AuthenticationManager()
            credentials = auth_manager.load_credentials_from_file(temp_file)
            
            assert credentials.auth_url == 'https://auth.cloud.ovh.net/v3'
            assert credentials.username == 'test-user'
            assert credentials.password == 'test-password'
            assert credentials.tenant_name == 'test-tenant'
            assert credentials.region == 'GRA7'
        finally:
            os.unlink(temp_file)
    
    def test_load_credentials_from_file_with_comments(self):
        """Test credential loading from file with comments."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("# This is a comment\n")
            f.write("OS_AUTH_URL=https://auth.cloud.ovh.net/v3\n")
            f.write("# Another comment\n")
            f.write("OS_USERNAME=test-user\n")
            f.write("OS_PASSWORD=test-password\n")
            f.write("OS_TENANT_NAME=test-tenant\n")
            f.write("OS_REGION_NAME=GRA7\n")
            temp_file = f.name
        
        try:
            auth_manager = AuthenticationManager()
            credentials = auth_manager.load_credentials_from_file(temp_file)
            
            assert credentials.username == 'test-user'
        finally:
            os.unlink(temp_file)
    
    def test_load_credentials_from_file_not_found(self):
        """Test error when credentials file doesn't exist."""
        auth_manager = AuthenticationManager()
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.load_credentials_from_file('/nonexistent/file.txt')
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_load_credentials_from_file_missing_fields(self):
        """Test error when credentials file is missing required fields."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("OS_AUTH_URL=https://auth.cloud.ovh.net/v3\n")
            f.write("OS_USERNAME=test-user\n")
            # Missing password, tenant, and region
            temp_file = f.name
        
        try:
            auth_manager = AuthenticationManager()
            
            with pytest.raises(AuthenticationError) as exc_info:
                auth_manager.load_credentials_from_file(temp_file)
            
            assert 'Missing required fields' in str(exc_info.value)
        finally:
            os.unlink(temp_file)
    
    def test_get_credentials_returns_none_initially(self):
        """Test that get_credentials returns None before loading."""
        auth_manager = AuthenticationManager()
        assert auth_manager.get_credentials() is None
    
    def test_get_credentials_returns_loaded_credentials(self):
        """Test that get_credentials returns loaded credentials."""
        env_vars = {
            'OS_AUTH_URL': 'https://auth.cloud.ovh.net/v3',
            'OS_USERNAME': 'test-user',
            'OS_PASSWORD': 'test-password',
            'OS_TENANT_NAME': 'test-tenant',
            'OS_REGION_NAME': 'GRA7'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            auth_manager = AuthenticationManager()
            loaded_creds = auth_manager.load_credentials_from_env()
            retrieved_creds = auth_manager.get_credentials()
            
            assert retrieved_creds == loaded_creds
    
    @patch('openstack.connect')
    def test_authenticate_success(self, mock_connect):
        """Test successful authentication."""
        # Mock connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        auth_manager = AuthenticationManager()
        conn = auth_manager.authenticate(credentials)
        
        assert conn == mock_conn
        mock_connect.assert_called_once()
        mock_conn.authorize.assert_called_once()
    
    @patch('openstack.connect')
    def test_authenticate_invalid_credentials(self, mock_connect):
        """Test authentication failure with invalid credentials."""
        from openstack.exceptions import HttpException
        
        # Mock connection that raises 401 error
        mock_conn = MagicMock()
        mock_conn.authorize.side_effect = HttpException(message="Unauthorized", http_status=401)
        mock_connect.return_value = mock_conn
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='bad-user',
            password='bad-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        auth_manager = AuthenticationManager()
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.authenticate(credentials)
        
        assert 'Invalid credentials' in str(exc_info.value)
    
    @patch('openstack.connect')
    def test_authenticate_connection_error(self, mock_connect):
        """Test authentication failure due to connection error."""
        from openstack.exceptions import SDKException
        
        # Mock connection that raises SDK exception
        mock_connect.side_effect = SDKException("Connection failed")
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        auth_manager = AuthenticationManager()
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.authenticate(credentials)
        
        assert 'Connection failed' in str(exc_info.value)


class TestConnectionManager:
    """Test cases for ConnectionManager."""
    
    @patch('openstack_sdk.auth_manager.AuthenticationManager.authenticate')
    def test_connect_creates_new_connection(self, mock_authenticate):
        """Test that connect creates a new connection."""
        mock_conn = MagicMock()
        mock_authenticate.return_value = mock_conn
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        conn = conn_manager.connect()
        
        assert conn == mock_conn
        mock_authenticate.assert_called_once()
    
    @patch('openstack_sdk.auth_manager.AuthenticationManager.authenticate')
    @patch('time.time')
    def test_get_connection_returns_existing_connection(self, mock_time, mock_authenticate):
        """Test that get_connection returns existing connection without re-authenticating."""
        mock_conn = MagicMock()
        mock_authenticate.return_value = mock_conn
        
        # Set time to ensure token doesn't need refresh
        mock_time.return_value = 1000.0
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        
        # First call creates connection
        conn1 = conn_manager.get_connection()
        
        # Set token expiry after first connection to prevent refresh
        conn_manager._token_expiry = 5000.0  # Token expires far in the future
        
        # Second call should reuse connection
        conn2 = conn_manager.get_connection()
        
        assert conn1 == conn2
        # Should only authenticate once (during first get_connection call)
        assert mock_authenticate.call_count == 1
    
    @patch('openstack_sdk.auth_manager.AuthenticationManager.authenticate')
    @patch('time.time')
    def test_get_connection_refreshes_expiring_token(self, mock_time, mock_authenticate):
        """Test that get_connection refreshes token when approaching expiry."""
        mock_conn = MagicMock()
        mock_authenticate.return_value = mock_conn
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        # First call: current time = 1000
        mock_time.return_value = 1000.0
        
        conn_manager = ConnectionManager(credentials)
        conn_manager._token_expiry = 1200.0  # Expires in 200 seconds
        conn_manager._connection = mock_conn
        
        # Token is within refresh threshold (300 seconds), should refresh
        conn = conn_manager.get_connection()
        
        # Should have called authenticate to refresh
        assert mock_authenticate.call_count >= 1
    
    @patch('openstack_sdk.auth_manager.AuthenticationManager.authenticate')
    def test_refresh_connection_creates_new_connection(self, mock_authenticate):
        """Test that refresh_connection creates a new connection."""
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()
        mock_authenticate.side_effect = [mock_conn1, mock_conn2]
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        conn1 = conn_manager.connect()
        conn2 = conn_manager.refresh_connection()
        
        assert conn1 == mock_conn1
        assert conn2 == mock_conn2
        assert mock_authenticate.call_count == 2
        mock_conn1.close.assert_called_once()
    
    @patch('openstack_sdk.auth_manager.AuthenticationManager.authenticate')
    def test_close_closes_connection(self, mock_authenticate):
        """Test that close properly closes the connection."""
        mock_conn = MagicMock()
        mock_authenticate.return_value = mock_conn
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        conn_manager.connect()
        conn_manager.close()
        
        mock_conn.close.assert_called_once()
        assert conn_manager._connection is None
    
    @patch('openstack_sdk.auth_manager.AuthenticationManager.authenticate')
    def test_context_manager(self, mock_authenticate):
        """Test ConnectionManager as context manager."""
        mock_conn = MagicMock()
        mock_authenticate.return_value = mock_conn
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        
        with conn_manager as conn:
            assert conn == mock_conn
        
        # Connection should be closed after exiting context
        mock_conn.close.assert_called_once()
    
    @patch('time.time')
    def test_should_refresh_token_returns_false_for_valid_token(self, mock_time):
        """Test that _should_refresh_token returns False for valid token."""
        mock_time.return_value = 1000.0
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        conn_manager._token_expiry = 2000.0  # Expires in 1000 seconds
        
        assert not conn_manager._should_refresh_token()
    
    @patch('time.time')
    def test_should_refresh_token_returns_true_for_expiring_token(self, mock_time):
        """Test that _should_refresh_token returns True for expiring token."""
        mock_time.return_value = 1000.0
        
        credentials = AuthCredentials(
            auth_url='https://auth.cloud.ovh.net/v3',
            username='test-user',
            password='test-password',
            tenant_name='test-tenant',
            region='GRA7',
            project_name='test-tenant'
        )
        
        conn_manager = ConnectionManager(credentials)
        conn_manager._token_expiry = 1200.0  # Expires in 200 seconds (< 300 threshold)
        
        assert conn_manager._should_refresh_token()
