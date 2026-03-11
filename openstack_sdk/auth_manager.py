"""Authentication and connection management for OVH OpenStack."""

import os
import time
from typing import Optional, Dict, Any
from pathlib import Path
import openstack
from openstack.connection import Connection
from openstack.exceptions import HttpException, SDKException

from config.models import AuthCredentials
from utils.logger import get_logger


class AuthenticationError(Exception):
    """Exception raised for authentication failures."""
    pass


class AuthenticationManager:
    """
    Manages authentication to OVH OpenStack API.
    
    Handles credential loading from environment variables and files,
    authentication token management, and secure credential handling.
    """
    
    def __init__(self, logger=None):
        """
        Initialize authentication manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or get_logger(__name__)
        self._credentials: Optional[AuthCredentials] = None
    
    def load_credentials_from_env(self) -> AuthCredentials:
        """
        Load authentication credentials from environment variables.
        
        Supports both traditional username/password and application credentials:
        - Traditional: OS_AUTH_URL, OS_USERNAME, OS_PASSWORD, OS_TENANT_NAME, OS_REGION_NAME
        - Application: OS_AUTH_URL, OS_APPLICATION_CREDENTIAL_ID, OS_APPLICATION_CREDENTIAL_SECRET, OS_TENANT_NAME, OS_REGION_NAME
        
        Returns:
            AuthCredentials object
            
        Raises:
            AuthenticationError: If required environment variables are missing
        """
        self.logger.info("Loading credentials from environment variables")
        
        # Get required environment variables
        auth_url = os.environ.get('OS_AUTH_URL')
        tenant_name = os.environ.get('OS_TENANT_NAME') or os.environ.get('OS_PROJECT_NAME')
        region = os.environ.get('OS_REGION_NAME')
        project_name = tenant_name  # Use same value for project_name
        
        # Check if we're using application credentials
        app_credential_id = os.environ.get('OS_APPLICATION_CREDENTIAL_ID')
        app_credential_secret = os.environ.get('OS_APPLICATION_CREDENTIAL_SECRET')
        
        # Check if we're using traditional credentials
        username = os.environ.get('OS_USERNAME')
        password = os.environ.get('OS_PASSWORD')
        
        # Validate required fields based on authentication type
        missing_vars = []
        if not auth_url:
            missing_vars.append('OS_AUTH_URL')
        if not region:
            missing_vars.append('OS_REGION_NAME')
            
        # For application credentials, tenant_name is not required as it's embedded in the credential
        # For traditional credentials, tenant_name is required
        if not app_credential_id and not app_credential_secret:
            # Traditional credentials require tenant_name
            if not tenant_name:
                missing_vars.append('OS_TENANT_NAME or OS_PROJECT_NAME')
            
        # Either traditional or application credentials must be provided
        if not app_credential_id and not app_credential_secret and not username:
            missing_vars.extend(['OS_USERNAME or OS_APPLICATION_CREDENTIAL_ID'])
        if not app_credential_secret and not password:
            missing_vars.extend(['OS_PASSWORD or OS_APPLICATION_CREDENTIAL_SECRET'])
            
        if missing_vars:
            raise AuthenticationError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        self._credentials = AuthCredentials(
            auth_url=auth_url,
            username=username or '',
            password=password or '',
            tenant_name=tenant_name,
            region=region,
            project_name=project_name,
            application_credential_id=app_credential_id,
            application_credential_secret=app_credential_secret
        )
        
        auth_type = "application credentials" if app_credential_id else "traditional credentials"
        self.logger.info(f"Loaded {auth_type} for tenant '{tenant_name}' in region '{region}'")
        return self._credentials
    
    def load_credentials_from_file(self, file_path: str) -> AuthCredentials:
        """
        Load authentication credentials from a secure file.
        
        File format (key=value pairs):
            OS_AUTH_URL=https://auth.cloud.ovh.net/v3
            OS_USERNAME=your-username
            OS_PASSWORD=your-password
            OS_TENANT_NAME=your-tenant
            OS_REGION_NAME=GRA7
        
        Args:
            file_path: Path to credentials file
            
        Returns:
            AuthCredentials object
            
        Raises:
            AuthenticationError: If file doesn't exist, has wrong permissions, or missing fields
        """
        self.logger.info(f"Loading credentials from file: {file_path}")
        
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            raise AuthenticationError(f"Credentials file not found: {file_path}")
        
        # Check file permissions (should be 600 or more restrictive)
        if os.name != 'nt':  # Skip permission check on Windows
            file_stat = path.stat()
            file_mode = file_stat.st_mode & 0o777
            if file_mode & 0o077:  # Check if group or others have any permissions
                self.logger.warning(
                    f"Credentials file has insecure permissions: {oct(file_mode)}. "
                    "Recommended: chmod 600"
                )
        
        # Read and parse file
        credentials_dict = {}
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            credentials_dict[key.strip()] = value.strip()
        except Exception as e:
            raise AuthenticationError(f"Failed to read credentials file: {e}")
        
        # Extract required fields
        auth_url = credentials_dict.get('OS_AUTH_URL')
        username = credentials_dict.get('OS_USERNAME')
        password = credentials_dict.get('OS_PASSWORD')
        tenant_name = credentials_dict.get('OS_TENANT_NAME') or credentials_dict.get('OS_PROJECT_NAME')
        region = credentials_dict.get('OS_REGION_NAME')
        project_name = tenant_name
        
        # Validate required fields
        missing_fields = []
        if not auth_url:
            missing_fields.append('OS_AUTH_URL')
        if not username:
            missing_fields.append('OS_USERNAME')
        if not password:
            missing_fields.append('OS_PASSWORD')
        if not tenant_name:
            missing_fields.append('OS_TENANT_NAME or OS_PROJECT_NAME')
        if not region:
            missing_fields.append('OS_REGION_NAME')
        
        if missing_fields:
            raise AuthenticationError(
                f"Missing required fields in credentials file: {', '.join(missing_fields)}"
            )
        
        self._credentials = AuthCredentials(
            auth_url=auth_url,
            username=username,
            password=password,
            tenant_name=tenant_name,
            region=region,
            project_name=project_name
        )
        
        self.logger.info(f"Loaded credentials for user '{username}' in region '{region}'")
        return self._credentials
    
    def get_credentials(self) -> Optional[AuthCredentials]:
        """
        Get currently loaded credentials.
        
        Returns:
            AuthCredentials object or None if not loaded
        """
        return self._credentials
    
    def authenticate(self, credentials: AuthCredentials) -> Connection:
        """
        Authenticate to OVH OpenStack and create connection.
        
        Supports both traditional username/password and application credentials.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Authenticated OpenStack connection
            
        Raises:
            AuthenticationError: If authentication fails
        """
        self.logger.info(f"Attempting authentication to {credentials.auth_url}")
        
        try:
            # Determine authentication method based on credentials provided
            if credentials.application_credential_id and credentials.application_credential_secret:
                self.logger.info("Using application credential authentication")
                # Create connection with application credentials
                conn = openstack.connect(
                    auth_url=credentials.auth_url,
                    application_credential_id=credentials.application_credential_id,
                    application_credential_secret=credentials.application_credential_secret,
                    project_name=credentials.project_name,
                    region_name=credentials.region,
                    app_name='ovh-openstack-deployment',
                    app_version='1.0'
                )
            else:
                self.logger.info("Using traditional username/password authentication")
                # Create connection with traditional credentials
                conn = openstack.connect(
                    auth_url=credentials.auth_url,
                    username=credentials.username,
                    password=credentials.password,
                    project_name=credentials.project_name,
                    user_domain_name='Default',
                    project_domain_name='Default',
                    region_name=credentials.region,
                    app_name='ovh-openstack-deployment',
                    app_version='1.0'
                )
            
            # Test authentication by making a simple API call
            # This will raise an exception if authentication fails
            conn.authorize()
            
            self.logger.info("Authentication successful")
            self._credentials = credentials
            
            return conn
            
        except HttpException as e:
            error_msg = f"Authentication failed: HTTP {e.status_code}"
            if e.status_code == 401:
                error_msg += " - Invalid credentials"
            elif e.status_code == 403:
                error_msg += " - Access forbidden"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg) from e
        
        except SDKException as e:
            error_msg = f"Authentication failed: {str(e)}"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected authentication error: {str(e)}"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg) from e


class ConnectionManager:
    """
    Manages OpenStack connection lifecycle and token refresh.
    
    Ensures authentication tokens remain valid during long-running deployments
    and handles token refresh automatically.
    """
    
    # Token refresh threshold: refresh when less than this many seconds remain
    TOKEN_REFRESH_THRESHOLD = 300  # 5 minutes
    
    def __init__(self, credentials: AuthCredentials, logger=None):
        """
        Initialize connection manager.
        
        Args:
            credentials: Authentication credentials
            logger: Optional logger instance
        """
        self.credentials = credentials
        self.logger = logger or get_logger(__name__)
        self._connection: Optional[Connection] = None
        self._auth_manager = AuthenticationManager(logger=self.logger)
        self._token_expiry: Optional[float] = None
        self._last_refresh: Optional[float] = None
    
    def connect(self) -> Connection:
        """
        Create authenticated connection to OpenStack.
        
        Returns:
            Authenticated OpenStack connection
            
        Raises:
            AuthenticationError: If connection fails
        """
        if self._connection is None:
            self.logger.info("Creating new OpenStack connection")
            self._connection = self._auth_manager.authenticate(self.credentials)
            self._update_token_expiry()
        
        return self._connection
    
    def get_connection(self) -> Connection:
        """
        Get current connection, ensuring token is valid.
        
        Automatically refreshes token if needed.
        
        Returns:
            Valid authenticated OpenStack connection
            
        Raises:
            AuthenticationError: If connection or refresh fails
        """
        if self._connection is None:
            return self.connect()
        
        # Check if token needs refresh
        if self._should_refresh_token():
            self.logger.info("Token approaching expiry, refreshing connection")
            self.refresh_connection()
        
        return self._connection
    
    def refresh_connection(self) -> Connection:
        """
        Refresh the OpenStack connection and authentication token.
        
        Returns:
            Refreshed authenticated connection
            
        Raises:
            AuthenticationError: If refresh fails
        """
        self.logger.info("Refreshing OpenStack connection")
        
        try:
            # Close existing connection if any
            if self._connection is not None:
                try:
                    self._connection.close()
                except Exception as e:
                    self.logger.warning(f"Error closing old connection: {e}")
            
            # Create new connection
            self._connection = self._auth_manager.authenticate(self.credentials)
            self._update_token_expiry()
            self._last_refresh = time.time()
            
            self.logger.info("Connection refreshed successfully")
            return self._connection
            
        except Exception as e:
            self.logger.error(f"Failed to refresh connection: {e}")
            raise
    
    def close(self):
        """Close the OpenStack connection."""
        if self._connection is not None:
            try:
                self.logger.info("Closing OpenStack connection")
                self._connection.close()
                self._connection = None
                self._token_expiry = None
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")
    
    def _should_refresh_token(self) -> bool:
        """
        Check if token should be refreshed.
        
        Returns:
            True if token should be refreshed, False otherwise
        """
        if self._token_expiry is None:
            return False
        
        time_until_expiry = self._token_expiry - time.time()
        
        if time_until_expiry <= self.TOKEN_REFRESH_THRESHOLD:
            self.logger.debug(
                f"Token expires in {time_until_expiry:.0f} seconds, "
                f"threshold is {self.TOKEN_REFRESH_THRESHOLD} seconds"
            )
            return True
        
        return False
    
    def _update_token_expiry(self):
        """Update token expiry time from connection."""
        try:
            if self._connection is not None:
                # Get auth token info
                auth = self._connection.session.auth
                if hasattr(auth, 'auth_ref') and auth.auth_ref:
                    # Token expiry is typically 1 hour from now
                    # OpenStack tokens usually expire in 3600 seconds (1 hour)
                    expires_at = auth.auth_ref.expires
                    if expires_at:
                        # Convert to timestamp
                        import datetime
                        if isinstance(expires_at, str):
                            # Parse ISO format timestamp
                            dt = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                            self._token_expiry = dt.timestamp()
                        elif isinstance(expires_at, datetime.datetime):
                            self._token_expiry = expires_at.timestamp()
                        else:
                            # Assume it's already a timestamp
                            self._token_expiry = float(expires_at)
                        
                        time_until_expiry = self._token_expiry - time.time()
                        self.logger.debug(f"Token expires in {time_until_expiry:.0f} seconds")
                        return
                
                # If we can't get expiry, assume 1 hour from now
                self._token_expiry = time.time() + 3600
                self.logger.debug("Could not determine token expiry, assuming 1 hour")
        
        except Exception as e:
            self.logger.warning(f"Error updating token expiry: {e}")
            # Assume 1 hour from now as fallback
            self._token_expiry = time.time() + 3600
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_connection()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
