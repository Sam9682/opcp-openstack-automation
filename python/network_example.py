"""Example demonstrating network infrastructure creation."""

import sys
import os
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from openstack_sdk.auth_manager import AuthenticationManager, ConnectionManager
from openstack_sdk.network_manager import NetworkManager, NetworkError
from config.models import NetworkSpec, SubnetSpec
from utils.logger import get_logger, setup_logging


def example_network_with_application_credentials():
    """Example: Demonstrate network creation with application credentials."""
    print("\n=== Network Example with Application Credentials ===")
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    # Step 1: Load credentials and authenticate
    logger.info("\n1. Loading credentials from environment variables...")
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
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
        conn = conn_manager.connect()
        logger.info("   Connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return 1
    
    # Step 3: Define network specifications
    logger.info("\n3. Defining network specifications...")
    
    network_specs = [
        NetworkSpec(
            name="example-private-network",
            admin_state_up=True,
            external=False,
            subnets=[
                SubnetSpec(
                    name="example-subnet-1",
                    cidr="192.168.1.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    gateway_ip="192.168.1.1",
                    dns_nameservers=["8.8.8.8", "8.8.4.4"]
                ),
                SubnetSpec(
                    name="example-subnet-2",
                    cidr="192.168.2.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    gateway_ip="192.168.2.1",
                    dns_nameservers=["8.8.8.8"]
                )
            ]
        ),
        NetworkSpec(
            name="example-management-network",
            admin_state_up=True,
            external=False,
            subnets=[
                SubnetSpec(
                    name="example-mgmt-subnet",
                    cidr="10.0.0.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    dns_nameservers=["8.8.8.8", "8.8.4.4"]
                )
            ]
        )
    ]
    
    logger.info(f"   Defined {len(network_specs)} networks with multiple subnets")
    
    # Step 4: Create network infrastructure
    logger.info("\n4. Creating network infrastructure...")
    network_manager = NetworkManager(conn, logger=logger)
    
    try:
        networks = network_manager.create_network_infrastructure(network_specs)
        
        logger.info(f"\n   Successfully created {len(networks)} networks:")
        for network in networks:
            logger.info(f"   - {network.name} (ID: {network.id}, Status: {network.status})")
        
        # Step 5: List all networks
        logger.info("\n5. Listing all networks...")
        all_networks = network_manager.list_networks()
        logger.info(f"   Total networks in project: {len(all_networks)}")
        
        # Step 6: Demonstrate network lookup
        logger.info("\n6. Looking up network by name...")
        found_network = network_manager.get_network_by_name("example-private-network")
        if found_network:
            logger.info(f"   Found network: {found_network.name} (ID: {found_network.id})")
        
        # Step 7: Cleanup (optional - uncomment to delete created networks)
        logger.info("\n7. Cleanup (networks will remain - delete manually if needed)")
        logger.info("   To delete networks, uncomment the cleanup code in this example")
        
        # Uncomment to delete created networks:
        # logger.info("\n7. Cleaning up created networks...")
        # for network in networks:
        #     logger.info(f"   Deleting network: {network.name}")
        #     network_manager.delete_network(network.id)
        # logger.info("   Cleanup complete")
        
        print("✓ Network example with application credentials completed successfully!")
        return 0
        
    except NetworkError as e:
        logger.error(f"\nNetwork creation failed: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"\nUnexpected error: {e}")
        return 1
    
    finally:
        # Close connection
        conn_manager.close()
        logger.info("\nConnection closed")


def main():
    """Demonstrate network infrastructure creation."""
    logger = get_logger(__name__)
    
    logger.info("=== Network Infrastructure Creation Example ===")
    
    # Step 1: Load credentials and authenticate
    logger.info("\n1. Loading credentials from environment variables...")
    auth_manager = AuthenticationManager(logger=logger)
    
    try:
        credentials = auth_manager.load_credentials_from_env()
        logger.info(f"   Loaded credentials for user: {credentials.username}")
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        logger.info("\nPlease set the following environment variables:")
        logger.info("  - OS_AUTH_URL")
        logger.info("  - OS_USERNAME")
        logger.info("  - OS_PASSWORD")
        logger.info("  - OS_TENANT_NAME (or OS_PROJECT_NAME)")
        logger.info("  - OS_REGION_NAME")
        return 1
    
    # Step 2: Create connection
    logger.info("\n2. Creating OpenStack connection...")
    try:
        conn_manager = ConnectionManager(credentials, logger=logger)
        conn = conn_manager.connect()
        logger.info("   Connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return 1
    
    # Step 3: Define network specifications
    logger.info("\n3. Defining network specifications...")
    
    network_specs = [
        NetworkSpec(
            name="example-private-network",
            admin_state_up=True,
            external=False,
            subnets=[
                SubnetSpec(
                    name="example-subnet-1",
                    cidr="192.168.1.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    gateway_ip="192.168.1.1",
                    dns_nameservers=["8.8.8.8", "8.8.4.4"]
                ),
                SubnetSpec(
                    name="example-subnet-2",
                    cidr="192.168.2.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    gateway_ip="192.168.2.1",
                    dns_nameservers=["8.8.8.8"]
                )
            ]
        ),
        NetworkSpec(
            name="example-management-network",
            admin_state_up=True,
            external=False,
            subnets=[
                SubnetSpec(
                    name="example-mgmt-subnet",
                    cidr="10.0.0.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    dns_nameservers=["8.8.8.8", "8.8.4.4"]
                )
            ]
        )
    ]
    
    logger.info(f"   Defined {len(network_specs)} networks with multiple subnets")
    
    # Step 4: Create network infrastructure
    logger.info("\n4. Creating network infrastructure...")
    network_manager = NetworkManager(conn, logger=logger)
    
    try:
        networks = network_manager.create_network_infrastructure(network_specs)
        
        logger.info(f"\n   Successfully created {len(networks)} networks:")
        for network in networks:
            logger.info(f"   - {network.name} (ID: {network.id}, Status: {network.status})")
        
        # Step 5: List all networks
        logger.info("\n5. Listing all networks...")
        all_networks = network_manager.list_networks()
        logger.info(f"   Total networks in project: {len(all_networks)}")
        
        # Step 6: Demonstrate network lookup
        logger.info("\n6. Looking up network by name...")
        found_network = network_manager.get_network_by_name("example-private-network")
        if found_network:
            logger.info(f"   Found network: {found_network.name} (ID: {found_network.id})")
        
        # Step 7: Cleanup (optional - uncomment to delete created networks)
        logger.info("\n7. Cleanup (networks will remain - delete manually if needed)")
        logger.info("   To delete networks, uncomment the cleanup code in this example")
        
        # Uncomment to delete created networks:
        # logger.info("\n7. Cleaning up created networks...")
        # for network in networks:
        #     logger.info(f"   Deleting network: {network.name}")
        #     network_manager.delete_network(network.id)
        # logger.info("   Cleanup complete")
        
        logger.info("\n=== Example completed successfully ===")
        return 0
        
    except NetworkError as e:
        logger.error(f"\nNetwork creation failed: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"\nUnexpected error: {e}")
        return 1
    
    finally:
        # Close connection
        conn_manager.close()
        logger.info("\nConnection closed")


if __name__ == "__main__":
    # Run the main example first
    result1 = main()
    
    # Then run the application credentials example
    result2 = example_network_with_application_credentials()
    
    sys.exit(max(result1, result2))
