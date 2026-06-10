"""Example usage of compute instance manager."""

import sys
import os
import pathlib
import socket
import requests
from urllib3.exceptions import NameResolutionError, MaxRetryError

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from openstack_sdk.auth_manager import AuthenticationManager, ConnectionManager, AuthenticationError
from openstack_sdk.compute_manager import ComputeManager, ComputeError
from config.models import InstanceSpec
from utils.logger import get_logger


def main():
    """Demonstrate compute instance creation."""
    logger = get_logger(__name__)
    
    conn_manager = None
    
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
        
        # Attempt to connect with improved error handling
        try:
            connection = conn_manager.connect()
            logger.info("Successfully authenticated to OVH OpenStack")
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            logger.error("Please verify your credentials and network connectivity")
            logger.error("Common causes:")
            logger.error("  - Incorrect credentials in environment variables or file")
            logger.error("  - Incorrect endpoint URL in credentials")
            logger.error("  - Network connectivity issues")
            logger.error("  - DNS resolution problems")
            raise
        except NameResolutionError as e:
            logger.error(f"DNS resolution failed: {e}")
            logger.error("Please check if the OpenStack endpoint URL is correct and reachable")
            logger.error("Common causes:")
            logger.error("  - Incorrect endpoint URL in credentials")
            logger.error("  - Network connectivity issues")
            logger.error("  - DNS server problems")
            raise
        except MaxRetryError as e:
            logger.error(f"Connection failed: {e}")
            logger.error("Please verify your network connectivity and the OpenStack endpoint URL")
            logger.error("Common causes:")
            logger.error("  - Incorrect endpoint URL in credentials")
            logger.error("  - Network connectivity issues")
            logger.error("  - Firewall blocking connections")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            logger.error("Please verify your network connectivity and the OpenStack endpoint URL")
            logger.error("Common causes:")
            logger.error("  - Incorrect endpoint URL in credentials")
            logger.error("  - Network connectivity issues")
            logger.error("  - Firewall blocking connections")
            raise
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed: {e}")
            logger.error("Please check if the OpenStack endpoint URL is correct and reachable")
            logger.error("Common causes:")
            logger.error("  - Incorrect endpoint URL in credentials")
            logger.error("  - Network connectivity issues")
            logger.error("  - DNS server problems")
            raise
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            logger.error("Please verify your credentials and network connectivity")
            raise
        
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
                name="opcp-automation-web-server-1",
                flavor="scale-1",  # Small instance flavor
                image="7e995f9c-c6fc-4d26-97ab-6c224d69280c",  # Ubuntu 22.04 image
                key_name="lab-key",  # Replace with your SSH key name
                network_ids=["f96825f7-5c9f-4079-a393-b6f94628ee1e"],  # Replace with your network ID
                security_groups=["opcp-automation-web-server-sg"],  # Replace with your security group
                user_data="",
                metadata={
                    "project": "opcp-automation-example",
                    "environment": "dev",
                    "role": "opcp-automation-web-server"
                }
            ),
            InstanceSpec(
                name="opcp-automation-web-server-2",
                flavor="scale-1",
                image="7e995f9c-c6fc-4d26-97ab-6c224d69280c",
                key_name="lab-key",
                network_ids=["f96825f7-5c9f-4079-a393-b6f94628ee1e"],
                security_groups=["opcp-automation-web-server-sg"],
                user_data="",
                metadata={
                    "project": "opcp-automation-example",
                    "environment": "dev",
                    "role": "opcp-automation-web-server"
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
        if conn_manager is not None:
            conn_manager.close()
            logger.info("Connection closed")


if __name__ == '__main__':
    main()
