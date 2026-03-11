"""Example demonstrating security group creation with OVH OpenStack."""

import sys
import os
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from openstack_sdk.auth_manager import AuthenticationManager, ConnectionManager
from openstack_sdk.security_group_manager import SecurityGroupManager
from config.models import SecurityGroupSpec, SecurityGroupRule, AuthCredentials
from utils.logger import get_logger, setup_logging


def example_security_group_with_application_credentials():
    """Example: Demonstrate security group creation with application credentials."""
    print("\n=== Security Group Example with Application Credentials ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Step 1: Load credentials and authenticate
    logger.info("\n1. Loading credentials from environment variables...")
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
        # Load credentials from environment (this now supports application credentials)
        credentials = auth_manager.load_credentials_from_env()
        
        # Check authentication type
        if credentials.application_credential_id:
            print("✓ Using Application Credentials authentication")
            print(f"✓ Application Credential ID: {credentials.application_credential_id}")
        else:
            print("✓ Using Traditional Username/Password authentication")
            print(f"✓ Username: {credentials.username}")
            logger.info(f"   Loaded credentials for user: {credentials.username}")
        
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        print("\nPlease set the following environment variables:")
        print("  - OS_AUTH_URL")
        print("  - OS_USERNAME (for traditional) or OS_APPLICATION_CREDENTIAL_ID (for app creds)")
        print("  - OS_PASSWORD (for traditional) or OS_APPLICATION_CREDENTIAL_SECRET (for app creds)")
        print("  - OS_TENANT_NAME (or OS_PROJECT_NAME)")
        print("  - OS_REGION_NAME")
        print("\nFor application credentials:")
        print("  export OS_AUTH_TYPE=v3applicationcredential")
        print("  export OS_APPLICATION_CREDENTIAL_ID=your-id")
        print("  export OS_APPLICATION_CREDENTIAL_SECRET=your-secret")
        return 1
    
    # Step 2: Create connection
    logger.info("\n2. Creating OpenStack connection...")
    try:
        conn_manager = ConnectionManager(credentials, logger=logger)
        connection = conn_manager.connect()
        logger.info("   Connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return 1
    
    # Initialize security group manager
    sg_manager = SecurityGroupManager(connection)
    
    # Define security group specifications
    security_groups = [
        # Web server security group
        SecurityGroupSpec(
            name="web-server-sg",
            description="Security group for web servers",
            rules=[
                # SSH access (restrict to your IP in production)
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=22,
                    port_range_max=22,
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                ),
                # HTTP access
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=80,
                    port_range_max=80,
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                ),
                # HTTPS access
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=443,
                    port_range_max=443,
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                ),
                # Allow all outbound traffic
                SecurityGroupRule(
                    direction="egress",
                    protocol="any",
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                )
            ]
        ),
        # Database security group
        SecurityGroupSpec(
            name="database-sg",
            description="Security group for database servers",
            rules=[
                # PostgreSQL access from private network only
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=5432,
                    port_range_max=5432,
                    remote_ip_prefix="192.168.1.0/24",
                    ethertype="IPv4"
                ),
                # MySQL access from private network only
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=3306,
                    port_range_max=3306,
                    remote_ip_prefix="192.168.1.0/24",
                    ethertype="IPv4"
                ),
                # Allow all outbound traffic
                SecurityGroupRule(
                    direction="egress",
                    protocol="any",
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                )
            ]
        ),
        # Application server security group
        SecurityGroupSpec(
            name="app-server-sg",
            description="Security group for application servers",
            rules=[
                # SSH access
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=22,
                    port_range_max=22,
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                ),
                # Application port range
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=8000,
                    port_range_max=8999,
                    remote_ip_prefix="192.168.1.0/24",
                    ethertype="IPv4"
                ),
                # ICMP for ping
                SecurityGroupRule(
                    direction="ingress",
                    protocol="icmp",
                    remote_ip_prefix="192.168.1.0/24",
                    ethertype="IPv4"
                ),
                # Allow all outbound traffic
                SecurityGroupRule(
                    direction="egress",
                    protocol="any",
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                )
            ]
        )
    ]
    
    # Create security groups
    logger.info(f"Creating {len(security_groups)} security groups...")
    try:
        created_groups = sg_manager.create_security_groups(security_groups)
        
        logger.info(f"Successfully created {len(created_groups)} security groups:")
        for sg in created_groups:
            logger.info(f"  - {sg.name} (ID: {sg.id})")
        
        # List all security groups
        logger.info("\nListing all security groups:")
        all_groups = sg_manager.list_security_groups()
        for sg in all_groups:
            logger.info(f"  - {sg.name} (ID: {sg.id})")
        
        # Get specific security group by name
        logger.info("\nRetrieving web-server-sg by name:")
        web_sg = sg_manager.get_security_group_by_name("web-server-sg")
        if web_sg:
            logger.info(f"  Found: {web_sg.name} (ID: {web_sg.id})")
        
        # Cleanup (optional - uncomment to delete created security groups)
        # logger.info("\nCleaning up security groups...")
        # for sg in created_groups:
        #     if sg_manager.delete_security_group(sg.id):
        #         logger.info(f"  Deleted: {sg.name}")
        
        print("✓ Security group example with application credentials completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error creating security groups: {e}", exc_info=True)
        return 1
    
    finally:
        # Close connection
        conn_manager.close()
        logger.info("\nConnection closed")


def main():
    """Demonstrate security group creation."""
    logger = get_logger(__name__)
    
    # Load credentials from environment variables
    logger.info("Loading credentials from environment variables...")
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
        credentials = auth_manager.load_credentials_from_env()
        logger.info(f"Loaded credentials for user: {credentials.username}")
        
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        logger.info("\nPlease set the following environment variables:")
        logger.info("  - OS_AUTH_URL")
        logger.info("  - OS_USERNAME")
        logger.info("  - OS_PASSWORD")
        logger.info("  - OS_TENANT_NAME (or OS_PROJECT_NAME)")
        logger.info("  - OS_REGION_NAME")
        return 1
    
    try:
        # Initialize authentication
        logger.info("Authenticating with OVH OpenStack...")
        connection = auth_manager.authenticate(credentials)
        logger.info("Authentication successful")
        
        # Initialize security group manager
        sg_manager = SecurityGroupManager(connection)
        
        # Define security group specifications
        security_groups = [
            # Web server security group
            SecurityGroupSpec(
                name="web-server-sg",
                description="Security group for web servers",
                rules=[
                    # SSH access (restrict to your IP in production)
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=22,
                        port_range_max=22,
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    ),
                    # HTTP access
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=80,
                        port_range_max=80,
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    ),
                    # HTTPS access
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=443,
                        port_range_max=443,
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    ),
                    # Allow all outbound traffic
                    SecurityGroupRule(
                        direction="egress",
                        protocol="any",
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    )
                ]
            ),
            # Database security group
            SecurityGroupSpec(
                name="database-sg",
                description="Security group for database servers",
                rules=[
                    # PostgreSQL access from private network only
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=5432,
                        port_range_max=5432,
                        remote_ip_prefix="192.168.1.0/24",
                        ethertype="IPv4"
                    ),
                    # MySQL access from private network only
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=3306,
                        port_range_max=3306,
                        remote_ip_prefix="192.168.1.0/24",
                        ethertype="IPv4"
                    ),
                    # Allow all outbound traffic
                    SecurityGroupRule(
                        direction="egress",
                        protocol="any",
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    )
                ]
            ),
            # Application server security group
            SecurityGroupSpec(
                name="app-server-sg",
                description="Security group for application servers",
                rules=[
                    # SSH access
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=22,
                        port_range_max=22,
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    ),
                    # Application port range
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=8000,
                        port_range_max=8999,
                        remote_ip_prefix="192.168.1.0/24",
                        ethertype="IPv4"
                    ),
                    # ICMP for ping
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="icmp",
                        remote_ip_prefix="192.168.1.0/24",
                        ethertype="IPv4"
                    ),
                    # Allow all outbound traffic
                    SecurityGroupRule(
                        direction="egress",
                        protocol="any",
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    )
                ]
            )
        ]
        
        # Create security groups
        logger.info(f"Creating {len(security_groups)} security groups...")
        created_groups = sg_manager.create_security_groups(security_groups)
        
        logger.info(f"Successfully created {len(created_groups)} security groups:")
        for sg in created_groups:
            logger.info(f"  - {sg.name} (ID: {sg.id})")
        
        # List all security groups
        logger.info("\nListing all security groups:")
        all_groups = sg_manager.list_security_groups()
        for sg in all_groups:
            logger.info(f"  - {sg.name} (ID: {sg.id})")
        
        # Get specific security group by name
        logger.info("\nRetrieving web-server-sg by name:")
        web_sg = sg_manager.get_security_group_by_name("web-server-sg")
        if web_sg:
            logger.info(f"  Found: {web_sg.name} (ID: {web_sg.id})")
        
        # Cleanup (optional - uncomment to delete created security groups)
        # logger.info("\nCleaning up security groups...")
        # for sg in created_groups:
        #     if sg_manager.delete_security_group(sg.id):
        #         logger.info(f"  Deleted: {sg.name}")
        
        logger.info("\nSecurity group example completed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the main example first
    result1 = main()
    
    # Then run the application credentials example
    result2 = example_security_group_with_application_credentials()
    
    sys.exit(max(result1, result2))
