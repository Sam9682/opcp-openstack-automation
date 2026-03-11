"""Example usage of compute instance manager."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openstack_sdk.auth_manager import AuthenticationManager, ConnectionManager
from openstack_sdk.compute_manager import ComputeManager, ComputeError
from config.models import InstanceSpec
from utils.logger import get_logger


def main():
    """Demonstrate compute instance creation."""
    logger = get_logger(__name__)
    
    try:
        # Step 1: Load credentials and authenticate
        logger.info("=== Step 1: Authentication ===")
        auth_manager = AuthenticationManager()
        
        # Try to load from environment variables first
        try:
            credentials = auth_manager.load_credentials_from_env()
            logger.info("Loaded credentials from environment variables")
        except Exception as e:
            logger.info(f"Could not load from environment: {e}")
            logger.info("Trying to load from credentials file...")
            credentials = auth_manager.load_credentials_from_file('examples/credentials.txt')
        
        # Create connection manager
        conn_manager = ConnectionManager(credentials)
        connection = conn_manager.connect()
        logger.info("Successfully authenticated to OVH OpenStack")
        
        # Step 2: Create compute manager
        logger.info("\n=== Step 2: Initialize Compute Manager ===")
        compute_manager = ComputeManager(connection)
        logger.info("Compute manager initialized")
        
        # Step 3: Define instance specifications
        logger.info("\n=== Step 3: Define Instance Specifications ===")
        
        # Note: You need to have a network and security group already created
        # You can use network_example.py and security_group_example.py first
        
        instance_specs = [
            InstanceSpec(
                name="web-server-1",
                flavor="s1-2",  # Small instance flavor
                image="Ubuntu 22.04",  # Ubuntu 22.04 image
                key_name="my-ssh-key",  # Replace with your SSH key name
                network_ids=["your-network-id"],  # Replace with your network ID
                security_groups=["web-security-group"],  # Replace with your security group
                user_data="""#!/bin/bash
echo "Hello from web-server-1" > /tmp/hello.txt
apt-get update
apt-get install -y nginx
systemctl start nginx
""",
                metadata={
                    "project": "example",
                    "environment": "dev",
                    "role": "web-server"
                }
            ),
            InstanceSpec(
                name="web-server-2",
                flavor="s1-2",
                image="Ubuntu 22.04",
                key_name="my-ssh-key",
                network_ids=["your-network-id"],
                security_groups=["web-security-group"],
                user_data="""#!/bin/bash
echo "Hello from web-server-2" > /tmp/hello.txt
apt-get update
apt-get install -y nginx
systemctl start nginx
""",
                metadata={
                    "project": "example",
                    "environment": "dev",
                    "role": "web-server"
                }
            )
        ]
        
        logger.info(f"Defined {len(instance_specs)} instance specifications")
        for spec in instance_specs:
            logger.info(f"  - {spec.name}: {spec.flavor}, {spec.image}")
        
        # Step 4: Create instances
        logger.info("\n=== Step 4: Create Compute Instances ===")
        logger.info("Creating instances (this may take a few minutes)...")
        
        instances = compute_manager.create_compute_instances(instance_specs)
        
        logger.info(f"\nSuccessfully created {len(instances)} instances:")
        for instance in instances:
            logger.info(f"  - Name: {instance.name}")
            logger.info(f"    ID: {instance.id}")
            logger.info(f"    Status: {instance.status}")
            if hasattr(instance, 'addresses') and instance.addresses:
                logger.info(f"    Addresses: {instance.addresses}")
        
        # Step 5: List all instances
        logger.info("\n=== Step 5: List All Instances ===")
        all_instances = compute_manager.list_instances()
        logger.info(f"Total instances in project: {len(all_instances)}")
        
        # Step 6: Get instance by name
        logger.info("\n=== Step 6: Get Instance by Name ===")
        instance = compute_manager.get_instance_by_name("web-server-1")
        if instance:
            logger.info(f"Found instance: {instance.name} (ID: {instance.id})")
        else:
            logger.info("Instance not found")
        
        # Step 7: Cleanup (optional - uncomment to delete instances)
        logger.info("\n=== Step 7: Cleanup (Optional) ===")
        logger.info("To delete instances, uncomment the cleanup code")
        
        # Uncomment the following lines to delete the created instances:
        # logger.info("Deleting created instances...")
        # for instance in instances:
        #     success = compute_manager.delete_instance(instance.id)
        #     if success:
        #         logger.info(f"Deleted instance: {instance.name}")
        #     else:
        #         logger.error(f"Failed to delete instance: {instance.name}")
        
        logger.info("\n=== Example Complete ===")
        logger.info("Instances created successfully!")
        logger.info("Remember to delete instances when done to avoid charges.")
        
    except ComputeError as e:
        logger.error(f"Compute error: {e}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Close connection
        if 'conn_manager' in locals():
            conn_manager.close()
            logger.info("Connection closed")


if __name__ == '__main__':
    main()
