"""Example usage of VolumeManager for creating and attaching volumes."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openstack_sdk.auth_manager import AuthManager
from openstack_sdk.compute_manager import ComputeManager
from openstack_sdk.volume_manager import VolumeManager
from config.models import VolumeSpec, InstanceSpec
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Demonstrate volume creation and attachment."""
    
    # Load credentials from environment or file
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
        
        # Initialize managers
        compute_manager = ComputeManager(connection)
        volume_manager = VolumeManager(connection)
        
        # Example 1: Create standalone volumes (not attached)
        logger.info("\n=== Example 1: Creating standalone volumes ===")
        
        standalone_volumes = [
            VolumeSpec(
                name="data-volume-1",
                size=100,
                volume_type="classic"
            ),
            VolumeSpec(
                name="data-volume-2",
                size=200,
                volume_type="high-speed"
            )
        ]
        
        created_volumes = volume_manager.create_and_attach_volumes(
            standalone_volumes,
            {}  # No instances to attach to
        )
        
        logger.info(f"Created {len(created_volumes)} standalone volumes:")
        for volume in created_volumes:
            logger.info(f"  - {volume.name} (ID: {volume.id}, Status: {volume.status})")
        
        # Example 2: Create bootable volume
        logger.info("\n=== Example 2: Creating bootable volume ===")
        
        # Note: You need to get a valid image_id from your OpenStack environment
        # This is just an example - replace with actual image ID
        bootable_volume_spec = VolumeSpec(
            name="boot-volume",
            size=50,
            volume_type="high-speed",
            bootable=True,
            image_id="your-image-id-here"  # Replace with actual image ID
        )
        
        # Uncomment to create bootable volume:
        # bootable_volumes = volume_manager.create_and_attach_volumes(
        #     [bootable_volume_spec],
        #     {}
        # )
        # logger.info(f"Created bootable volume: {bootable_volumes[0].name}")
        
        # Example 3: Create volumes and attach to instances
        logger.info("\n=== Example 3: Creating volumes and attaching to instances ===")
        
        # First, we need to have instances created
        # This example assumes you have instances already created
        # In a real scenario, you would create instances first using ComputeManager
        
        # Get existing instances (or create them first)
        existing_instances = compute_manager.list_instances()
        
        if existing_instances:
            # Create a dictionary mapping instance names to Server objects
            instances_dict = {inst.name: inst for inst in existing_instances}
            
            # Create volumes to attach to first instance
            first_instance_name = existing_instances[0].name
            
            attached_volumes = [
                VolumeSpec(
                    name=f"attached-volume-{first_instance_name}",
                    size=150,
                    volume_type="classic",
                    attach_to=first_instance_name
                )
            ]
            
            created_attached = volume_manager.create_and_attach_volumes(
                attached_volumes,
                instances_dict
            )
            
            logger.info(f"Created and attached {len(created_attached)} volumes:")
            for volume in created_attached:
                logger.info(
                    f"  - {volume.name} (ID: {volume.id}, Status: {volume.status})"
                )
        else:
            logger.info("No existing instances found. Skipping attachment example.")
            logger.info("Create instances first using compute_example.py")
        
        # Example 4: List all volumes
        logger.info("\n=== Example 4: Listing all volumes ===")
        
        all_volumes = volume_manager.list_volumes()
        logger.info(f"Total volumes: {len(all_volumes)}")
        for volume in all_volumes:
            logger.info(
                f"  - {volume.name} (ID: {volume.id}, Size: {volume.size}GB, "
                f"Status: {volume.status})"
            )
        
        # Example 5: Cleanup - Delete created volumes
        logger.info("\n=== Example 5: Cleaning up volumes ===")
        
        # Delete the volumes we created
        for volume in created_volumes:
            logger.info(f"Deleting volume: {volume.name}")
            success = volume_manager.delete_volume(volume.id)
            if success:
                logger.info(f"  Successfully deleted {volume.name}")
            else:
                logger.error(f"  Failed to delete {volume.name}")
        
        logger.info("\nVolume management examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in volume example: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
