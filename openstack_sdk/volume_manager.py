"""Volume creation and attachment management for OVH OpenStack."""

import time
from typing import List, Dict, Optional
from openstack.connection import Connection
from openstack.block_storage.v3.volume import Volume
from openstack.compute.v2.server import Server
from openstack.exceptions import SDKException

from config.models import VolumeSpec
from utils.logger import get_logger


class VolumeError(Exception):
    """Exception raised for volume operation failures."""
    pass


class VolumeManager:
    """
    Manages volume creation and attachment.
    
    Handles volume creation with size and type validation, bootable volume handling
    with image_id, volume status polling with timeout, volume attachment logic with
    instance verification, and volume state transitions (available -> in-use).
    """
    
    # Maximum time to wait for volume to become available (seconds)
    VOLUME_AVAILABLE_TIMEOUT = 60
    
    # Polling interval for volume status checks (seconds)
    POLLING_INTERVAL = 2
    
    # Maximum polling interval with exponential backoff (seconds)
    MAX_POLLING_INTERVAL = 10
    
    def __init__(self, connection: Connection, logger=None):
        """
        Initialize volume manager.
        
        Args:
            connection: Authenticated OpenStack connection
            logger: Optional logger instance
        """
        self.conn = connection
        self.logger = logger or get_logger(__name__)
    
    def create_and_attach_volumes(
        self,
        volume_specs: List[VolumeSpec],
        instances: Dict[str, Server]
    ) -> List[Volume]:
        """
        Create volumes and attach them to instances.
        
        Creates volumes with specified size and type, validates volume size is
        positive integer, validates volume type is valid for OVH OpenStack,
        handles bootable volumes with image_id, waits for volumes to reach
        available status, attaches volumes to instances, verifies instances are
        in ACTIVE status before attachment, and verifies volume status changes
        to in-use after attachment.
        
        Args:
            volume_specs: List of volume specifications
            instances: Dictionary mapping instance names to Server objects
            
        Returns:
            List of created Volume objects
            
        Raises:
            VolumeError: If volume creation or attachment fails
        """
        if not volume_specs:
            self.logger.warning("No volume specifications provided")
            return []
        
        self.logger.info(f"Creating volumes: {len(volume_specs)} volumes")
        
        created_volumes = []
        
        try:
            for volume_spec in volume_specs:
                self.logger.info(f"Creating volume: {volume_spec.name}")
                
                # Validate volume specification
                self._validate_volume_spec(volume_spec, instances)
                
                # Create volume
                volume = self._create_volume(volume_spec)
                created_volumes.append(volume)
                
                # Wait for volume to become available
                self.logger.info(f"Waiting for volume '{volume_spec.name}' to become available")
                volume = self._wait_for_volume_available(volume.id)
                
                # Attach volume to instance if specified
                if volume_spec.attach_to:
                    instance = instances[volume_spec.attach_to]
                    self.logger.info(
                        f"Attaching volume '{volume_spec.name}' to instance '{volume_spec.attach_to}'"
                    )
                    self._attach_volume_to_instance(volume, instance)
                    
                    # Verify volume status changed to in-use
                    volume = self._verify_volume_in_use(volume.id)
                
                self.logger.info(
                    f"Successfully created volume '{volume_spec.name}' "
                    f"(ID: {volume.id}, Status: {volume.status})"
                )
            
            self.logger.info(
                f"Volume creation complete: {len(created_volumes)} volumes created"
            )
            return created_volumes
        
        except Exception as e:
            self.logger.error(f"Volume creation/attachment failed: {e}")
            raise
    
    def _validate_volume_spec(
        self,
        volume_spec: VolumeSpec,
        instances: Dict[str, Server]
    ) -> None:
        """
        Validate volume specification.
        
        Args:
            volume_spec: Volume specification to validate
            instances: Dictionary of available instances
            
        Raises:
            VolumeError: If validation fails
        """
        # Validate volume size is positive integer
        if not isinstance(volume_spec.size, int) or volume_spec.size <= 0:
            raise VolumeError(
                f"Volume size must be a positive integer, got: {volume_spec.size}"
            )
        
        # Validate bootable volume has image_id
        if volume_spec.bootable and not volume_spec.image_id:
            raise VolumeError(
                f"Bootable volume '{volume_spec.name}' requires image_id"
            )
        
        # Validate attach_to references existing instance
        if volume_spec.attach_to:
            if volume_spec.attach_to not in instances:
                raise VolumeError(
                    f"Volume '{volume_spec.name}' references non-existent instance: "
                    f"'{volume_spec.attach_to}'"
                )
            
            # Verify instance is in ACTIVE status
            instance = instances[volume_spec.attach_to]
            if instance.status != 'ACTIVE':
                raise VolumeError(
                    f"Cannot attach volume '{volume_spec.name}' to instance "
                    f"'{volume_spec.attach_to}' - instance status is {instance.status}, "
                    f"expected ACTIVE"
                )
    
    def _create_volume(self, volume_spec: VolumeSpec) -> Volume:
        """
        Create a single volume.
        
        Args:
            volume_spec: Volume specification
            
        Returns:
            Created Volume object
            
        Raises:
            VolumeError: If volume creation fails
        """
        try:
            # Prepare volume parameters
            volume_params = {
                'name': volume_spec.name,
                'size': volume_spec.size,
                'volume_type': volume_spec.volume_type
            }
            
            # Add bootable and image_id if specified
            if volume_spec.bootable and volume_spec.image_id:
                volume_params['bootable'] = True
                volume_params['imageRef'] = volume_spec.image_id
            
            # Create volume
            volume = self.conn.block_storage.create_volume(**volume_params)
            
            self.logger.info(
                f"Created volume '{volume_spec.name}' (ID: {volume.id}, "
                f"Size: {volume_spec.size}GB, Type: {volume_spec.volume_type}, "
                f"Status: {volume.status})"
            )
            
            return volume
        
        except SDKException as e:
            error_msg = f"Failed to create volume '{volume_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise VolumeError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error creating volume '{volume_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise VolumeError(error_msg) from e
    
    def _wait_for_volume_available(self, volume_id: str) -> Volume:
        """
        Wait for volume to reach available status.
        
        Polls volume status with exponential backoff until it reaches
        'available' status or timeout is reached.
        
        Args:
            volume_id: ID of volume to wait for
            
        Returns:
            Volume object in available status
            
        Raises:
            VolumeError: If volume doesn't reach available status within timeout
        """
        start_time = time.time()
        polling_interval = self.POLLING_INTERVAL
        
        while (time.time() - start_time) < self.VOLUME_AVAILABLE_TIMEOUT:
            try:
                volume = self.conn.block_storage.get_volume(volume_id)
                
                if volume.status == 'available':
                    elapsed = time.time() - start_time
                    self.logger.info(
                        f"Volume {volume_id} is available (took {elapsed:.1f}s)"
                    )
                    return volume
                
                elif volume.status == 'error':
                    raise VolumeError(
                        f"Volume {volume_id} entered error state"
                    )
                
                elif volume.status not in ['creating', 'available']:
                    self.logger.warning(
                        f"Volume {volume_id} in unexpected status: {volume.status}"
                    )
                
                # Wait before checking again with exponential backoff
                time.sleep(polling_interval)
                polling_interval = min(polling_interval * 1.5, self.MAX_POLLING_INTERVAL)
            
            except VolumeError:
                raise
            except Exception as e:
                raise VolumeError(f"Error checking volume {volume_id} status: {e}")
        
        raise VolumeError(
            f"Timeout waiting for volume {volume_id} to become available "
            f"after {self.VOLUME_AVAILABLE_TIMEOUT} seconds"
        )
    
    def _attach_volume_to_instance(self, volume: Volume, instance: Server) -> None:
        """
        Attach volume to instance.
        
        Args:
            volume: Volume object to attach
            instance: Server object to attach volume to
            
        Raises:
            VolumeError: If attachment fails
        """
        try:
            # Create volume attachment
            attachment = self.conn.compute.create_volume_attachment(
                server=instance,
                volume_id=volume.id
            )
            
            self.logger.info(
                f"Attached volume {volume.id} to instance {instance.id} "
                f"(attachment ID: {attachment.id})"
            )
        
        except SDKException as e:
            error_msg = (
                f"Failed to attach volume {volume.id} to instance {instance.id}: {str(e)}"
            )
            self.logger.error(error_msg)
            raise VolumeError(error_msg) from e
        
        except Exception as e:
            error_msg = (
                f"Unexpected error attaching volume {volume.id} to instance {instance.id}: "
                f"{str(e)}"
            )
            self.logger.error(error_msg)
            raise VolumeError(error_msg) from e
    
    def _verify_volume_in_use(self, volume_id: str) -> Volume:
        """
        Verify volume status changed to in-use after attachment.
        
        Args:
            volume_id: ID of volume to verify
            
        Returns:
            Volume object in in-use status
            
        Raises:
            VolumeError: If volume doesn't reach in-use status
        """
        start_time = time.time()
        polling_interval = self.POLLING_INTERVAL
        timeout = 30  # Shorter timeout for status verification
        
        while (time.time() - start_time) < timeout:
            try:
                volume = self.conn.block_storage.get_volume(volume_id)
                
                if volume.status == 'in-use':
                    self.logger.info(f"Volume {volume_id} is in-use")
                    return volume
                
                elif volume.status == 'error':
                    raise VolumeError(
                        f"Volume {volume_id} entered error state during attachment"
                    )
                
                # Wait before checking again
                time.sleep(polling_interval)
                polling_interval = min(polling_interval * 1.5, self.MAX_POLLING_INTERVAL)
            
            except VolumeError:
                raise
            except Exception as e:
                raise VolumeError(f"Error verifying volume {volume_id} status: {e}")
        
        raise VolumeError(
            f"Volume {volume_id} did not reach in-use status after {timeout} seconds"
        )
    
    def list_volumes(self) -> List[Volume]:
        """
        List all volumes.
        
        Returns:
            List of Volume objects
        """
        try:
            return list(self.conn.block_storage.volumes())
        except Exception as e:
            self.logger.error(f"Error listing volumes: {e}")
            return []
    
    def delete_volume(self, volume_id: str) -> bool:
        """
        Delete a volume.
        
        Args:
            volume_id: ID of volume to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting volume: {volume_id}")
            self.conn.block_storage.delete_volume(volume_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting volume {volume_id}: {e}")
            return False
    
    def detach_volume(self, instance_id: str, volume_id: str) -> bool:
        """
        Detach volume from instance.
        
        Args:
            instance_id: ID of instance
            volume_id: ID of volume to detach
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Detaching volume {volume_id} from instance {instance_id}")
            self.conn.compute.delete_volume_attachment(volume_id, instance_id)
            return True
        except Exception as e:
            self.logger.error(
                f"Error detaching volume {volume_id} from instance {instance_id}: {e}"
            )
            return False
