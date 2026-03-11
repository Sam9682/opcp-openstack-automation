"""Example usage of application credentials authentication."""

import os
import sys
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from openstack_sdk.auth_manager import AuthenticationManager, ConnectionManager
from config.models import AuthCredentials
from utils.logger import setup_logging


def example_app_cred_from_env():
    """Example: Load application credentials from environment variables."""
    print("\n=== Example: Load application credentials from environment variables ===")
    
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


def example_app_cred_with_connection_manager():
    """Example: Use ConnectionManager with application credentials."""
    print("\n=== Example: Use ConnectionManager with application credentials ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Create credentials (this would typically come from environment variables)
    # For demonstration, we'll create them manually
    credentials = AuthCredentials(
        auth_url=os.environ.get('OS_AUTH_URL', 'https://auth.cloud.ovh.net/v3'),
        username='',  # Not used with application credentials
        password='',  # Not used with application credentials
        #tenant_name=os.environ.get('OS_TENANT_NAME', 'your-tenant'),
        region=os.environ.get('OS_REGION_NAME', 'GRA7'),
        #project_name=os.environ.get('OS_TENANT_NAME', 'your-tenant'),
        application_credential_id=os.environ.get('OS_APPLICATION_CREDENTIAL_ID'),
        application_credential_secret=os.environ.get('OS_APPLICATION_CREDENTIAL_SECRET')
    )
    
    try:
        # Create connection manager
        conn_manager = ConnectionManager(credentials, logger=logger)
        
        # Get connection (automatically handles token refresh)
        connection = conn_manager.get_connection()
        print("✓ Connection established")
        
        # Use connection for operations
        projects = list(connection.identity.projects())
        print(f"✓ Found {len(projects)} projects")
        
        # Close connection when done
        conn_manager.close()
        print("✓ Connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run application credential examples."""
    print("=" * 70)
    print("Application Credentials Examples")
    print("=" * 70)
    
    # Check if application credential environment variables are set
    # For application credentials, OS_TENANT_NAME is not required as it's embedded in the credential
    required_vars = ['OS_AUTH_URL', 'OS_APPLICATION_CREDENTIAL_ID', 'OS_APPLICATION_CREDENTIAL_SECRET', 'OS_REGION_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("\n⚠ Warning: The following environment variables are not set:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nTo run with application credentials, set these variables:")
        print("  export OS_AUTH_TYPE=v3applicationcredential")
        print("  export OS_AUTH_URL=https://keystone.demo.bmp.ovhgoldorack.ovh/v3")
        print("  export OS_IDENTITY_API_VERSION=3")
        print("  export OS_REGION_NAME=\"demo\"")
        print("  export OS_INTERFACE=public")
        print("  export OS_APPLICATION_CREDENTIAL_ID=your_id_here")
        print("  export OS_APPLICATION_CREDENTIAL_SECRET=your_credentials_here")
        print("\nRunning examples with placeholder credentials (will fail authentication)...")
    
    # Run examples
    example_app_cred_from_env()
    example_app_cred_with_connection_manager()
    
    print("\n" + "=" * 70)
    print("Application credential examples completed!")
    print("=" * 70)


if __name__ == '__main__':
    main()