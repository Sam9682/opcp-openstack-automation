"""Example demonstrating security group creation with OVH OpenStack."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openstack_sdk.auth_manager import AuthManager
from openstack_sdk.security_group_manager import SecurityGroupManager
from config.models import SecurityGroupSpec, SecurityGroupRule
from utils.logger import get_logger


def main():
    """Demonstrate security group creation."""
    logger = get_logger(__name__)
    
    # Authentication credentials (use environment variables in production)
    auth_config = {
        'auth_url': os.environ.get('OS_AUTH_URL', 'https://auth.cloud.ovh.net/v3'),
        'username': os.environ.get('OS_USERNAME', 'your-username'),
        'password': os.environ.get('OS_PASSWORD', 'your-password'),
        'tenant_name': os.environ.get('OS_TENANT_NAME', 'your-tenant'),
        'region': os.environ.get('OS_REGION_NAME', 'GRA7'),
        'project_name': os.environ.get('OS_PROJECT_NAME', 'your-project')
    }
    
    try:
        # Initialize authentication
        logger.info("Authenticating with OVH OpenStack...")
        auth_manager = AuthManager(
            auth_url=auth_config['auth_url'],
            username=auth_config['username'],
            password=auth_config['password'],
            tenant_name=auth_config['tenant_name'],
            region=auth_config['region'],
            project_name=auth_config['project_name']
        )
        
        connection = auth_manager.get_connection()
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
    sys.exit(main())
