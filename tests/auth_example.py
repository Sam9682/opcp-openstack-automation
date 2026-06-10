"""Example usage of authentication and connection management."""

import os
import sys
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from openstack_sdk.auth_manager import AuthenticationManager, ConnectionManager
from config.models import AuthCredentials
from utils.logger import setup_logging


def example_load_from_env():
    """Example: Load credentials from environment variables."""
    print("\n=== Example 1: Load credentials from environment variables ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Create authentication manager
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
        # Load credentials from environment
        credentials = auth_manager.load_credentials_from_env()
        print(f"✓ Loaded credentials for user: {credentials.username}")
        print(f"✓ Region: {credentials.region}")
        print(f"✓ Auth URL: {credentials.auth_url}")
        
        # Check authentication type
        if credentials.application_credential_id:
            print("✓ Using Application Credentials authentication")
            print(f"✓ Application Credential ID: {credentials.application_credential_id}")
        else:
            print("✓ Using Traditional Username/Password authentication")
        
        # Authenticate and create connection
        connection = auth_manager.authenticate(credentials)
        print("✓ Authentication successful!")
        
        # Test connection by listing projects
        projects = list(connection.identity.projects())
        print(f"✓ Found {len(projects)} projects")
        
        connection.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_load_from_file():
    """Example: Load credentials from file."""
    print("\n=== Example 2: Load credentials from file ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Create authentication manager
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
        # Load credentials from file
        credentials = auth_manager.load_credentials_from_file('examples/credentials.txt')
        print(f"✓ Loaded credentials for user: {credentials.username}")
        
        # Check authentication type
        if credentials.application_credential_id:
            print("✓ Using Application Credentials authentication")
            print(f"✓ Application Credential ID: {credentials.application_credential_id}")
        else:
            print("✓ Using Traditional Username/Password authentication")
        
        # Authenticate
        connection = auth_manager.authenticate(credentials)
        print("✓ Authentication successful!")
        
        connection.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_connection_manager():
    """Example: Use ConnectionManager for automatic token refresh."""
    print("\n=== Example 3: Use ConnectionManager with automatic token refresh ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Create credentials
    credentials = AuthCredentials(
        auth_url=os.environ.get('OS_AUTH_URL', 'https://keystone.demo.com/v3'),
        region=os.environ.get('OS_REGION_NAME', 'RegionOne'),
        application_credential_id=os.environ.get('OS_APPLICATION_CREDENTIAL_ID'),
        application_credential_secret=os.environ.get('OS_APPLICATION_CREDENTIAL_SECRET'),
        auth_type=os.environ.get('OS_AUTH_TYPE', 'v3applicationcredential'),
        interface=os.environ.get('OS_INTERFACE', 'public'),
    )
    
    try:
        # Create connection manager
        conn_manager = ConnectionManager(credentials, logger=logger)
        
        # Get connection (automatically handles token refresh)
        connection = conn_manager.get_connection()
        print("✓ Connection established")
        
        # Use connection for operations
        # The connection manager will automatically refresh the token if needed
        projects = list(connection.identity.projects())
        print(f"✓ Found {len(projects)} projects")
        
        # Close connection when done
        conn_manager.close()
        print("✓ Connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_context_manager():
    """Example: Use ConnectionManager as context manager."""
    print("\n=== Example 4: Use ConnectionManager as context manager ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Create credentials
    credentials = AuthCredentials(
        auth_url=os.environ.get('OS_AUTH_URL', 'https://keystone.demo.com/v3'),
        region=os.environ.get('OS_REGION_NAME', 'RegionOne'),
        application_credential_id=os.environ.get('OS_APPLICATION_CREDENTIAL_ID'),
        application_credential_secret=os.environ.get('OS_APPLICATION_CREDENTIAL_SECRET'),
        auth_type=os.environ.get('OS_AUTH_TYPE', 'v3applicationcredential'),
        interface=os.environ.get('OS_INTERFACE', 'public'),
    )
    
    try:
        # Use as context manager - connection is automatically closed
        conn_manager = ConnectionManager(credentials, logger=logger)
        
        with conn_manager as connection:
            print("✓ Connection established")
            
            # Use connection
            projects = list(connection.identity.projects())
            print(f"✓ Found {len(projects)} projects")
        
        print("✓ Connection automatically closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_application_credentials():
    """Example: Demonstrate application credentials usage."""
    print("\n=== Example 5: Application Credentials Usage ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Create authentication manager
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
        # Load credentials from environment (this now supports application credentials)
        credentials = auth_manager.load_credentials_from_env()
        print(f"✓ Loaded credentials")
        print(f"✓ Auth URL: {credentials.auth_url}")
        print(f"✓ Region: {credentials.region}")
        print(f"✓ Tenant: {credentials.tenant_name}")
        
        # Check if application credentials are being used
        if credentials.application_credential_id:
            print("✓ Using Application Credentials authentication")
            print(f"✓ Application Credential ID: {credentials.application_credential_id}")
        else:
            print("✓ Using Traditional Username/Password authentication")
            print(f"✓ Username: {credentials.username}")
        
        # Authenticate and create connection
        connection = auth_manager.authenticate(credentials)
        print("✓ Authentication successful!")
        
        # Test connection by listing projects
        projects = list(connection.identity.projects())
        print(f"✓ Found {len(projects)} projects")
        
        connection.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples."""
    print("=" * 70)
    print("Authentication and Connection Management Examples")
    print("=" * 70)
    
    # Check if environment variables are set
    required_vars = ['OS_AUTH_TYPE', 'OS_AUTH_URL', 'OS_IDENTITY_API_VERSION', 'OS_REGION_NAME', 'OS_INTERFACE', 'OS_APPLICATION_CREDENTIAL_ID', 'OS_APPLICATION_CREDENTIAL_SECRET']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("\n⚠ Warning: The following environment variables are not set:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nSet these variables to run the examples with real credentials.")
        print("\nRequired variables:")
        print("  export OS_AUTH_TYPE=v3applicationcredential")
        print("  export OS_AUTH_URL=https://keystone.demo.com/v3")
        print("  export OS_IDENTITY_API_VERSION=3")
        print("  export OS_REGION_NAME=RegionOne")
        print("  export OS_INTERFACE=public")
        print("  export OS_APPLICATION_CREDENTIAL_ID=your-credential-id")
        print("  export OS_APPLICATION_CREDENTIAL_SECRET=your-credential-secret")
        print("\nRunning examples with placeholder credentials (will fail authentication)...")
    
    # Run examples
    # Note: These will fail if credentials are not properly set
    example_load_from_env()
    example_load_from_file()
    example_connection_manager()
    example_context_manager()
    example_application_credentials()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
    print("\nNote: Uncomment the example function calls in main() to run them.")
    print("Make sure to set your OpenStack credentials first.")


if __name__ == '__main__':
    main()
