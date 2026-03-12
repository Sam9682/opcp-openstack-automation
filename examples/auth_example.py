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
        auth_url=os.environ.get('OS_AUTH_URL', 'https://auth.cloud.ovh.net/v3'),
        username=os.environ.get('OS_USERNAME', 'your-username'),
        password=os.environ.get('OS_PASSWORD', 'your-password'),
        tenant_name=os.environ.get('OS_TENANT_NAME', 'your-tenant'),
        region=os.environ.get('OS_REGION_NAME', 'GRA7'),
        project_name=os.environ.get('OS_TENANT_NAME', 'your-tenant')
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
        auth_url=os.environ.get('OS_AUTH_URL', 'https://auth.cloud.ovh.net/v3'),
        username=os.environ.get('OS_USERNAME', 'your-username'),
        password=os.environ.get('OS_PASSWORD', 'your-password'),
        tenant_name=os.environ.get('OS_TENANT_NAME', 'your-tenant'),
        region=os.environ.get('OS_REGION_NAME', 'GRA7'),
        project_name=os.environ.get('OS_TENANT_NAME', 'your-tenant')
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
    required_vars = ['OS_AUTH_URL', 'OS_USERNAME', 'OS_PASSWORD', 'OS_TENANT_NAME', 'OS_REGION_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("\n⚠ Warning: The following environment variables are not set:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nSet these variables to run the examples with real credentials.")
        print("\nFor traditional credentials:")
        print("  export OS_AUTH_URL=https://auth.cloud.ovh.net/v3")
        print("  export OS_USERNAME=your-username")
        print("  export OS_PASSWORD=your-password")
        print("  export OS_TENANT_NAME=your-tenant")
        print("  export OS_REGION_NAME=GRA7")
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
