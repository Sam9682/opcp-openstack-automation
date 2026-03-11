"""Compute instance creation and management for OVH OpenStack."""

import time
from typing import List, Dict, Optional, Set
from openstack.connection import Connection
from openstack.compute.v2.server import Server
from openstack.exceptions import SDKException, ResourceTimeout

from config.models import InstanceSpec
from utils.logger import get_logger


class ComputeError(Exception):
    """Exception raised for compute operation failures."""
    pass


class ComputeManager:
    """
    Manages compute instance creation and validation.
    
    Handles instance creation with flavor and image validation, network attachment,
    security group application, SSH key configuration, user_data and metadata injection,
    instance status polling with timeout, and name uniqueness enforcement.
    """
    
    # Maximum time to wait for instance to become ACTIVE (seconds)
    INSTANCE_ACTIVE_TIMEOUT = 300
    
    # Polling interval for instance status checks (seconds)
    POLLING_INTERVAL = 5
    
    def __init__(self, connection: Connection, logger=None):
        """
        Initialize compute manager.
        
        Args:
            connection: Authenticated OpenStack connection
            logger: Optional logger instance
        """
        self.conn = connection
        self.logger = logger or get_logger(__name__)
        self._created_instance_names: Set[str] = set()
        self._flavor_cache: Dict[str, str] = {}  # flavor_name -> flavor_id
        self._image_cache: Dict[str, str] = {}  # image_name -> image_id
    
    def create_compute_instances(
        self,
        instance_specs: List[InstanceSpec]
    ) -> List[Server]:
        """
        Create compute instances from specifications.
        
        Creates instances with specified flavor, image, and name. Validates that
        flavor and image exist, attaches instances to specified networks, applies
        security groups, configures SSH keys, injects user_data and metadata,
        waits for instances to reach ACTIVE status with timeout, and enforces
        instance name uniqueness.
        
        Args:
            instance_specs: List of instance specifications
            
        Returns:
            List of created Server objects
            
        Raises:
            ComputeError: If instance creation fails or validation errors occur
        """
        if not instance_specs:
            self.logger.warning("No instance specifications provided")
            return []
        
        self.logger.info(f"Creating compute instances: {len(instance_specs)} instances")
        
        # Validate instance name uniqueness across specs
        self._validate_instance_names_unique(instance_specs)
        
        created_instances = []
        
        try:
            for instance_spec in instance_specs:
                self.logger.info(f"Creating instance: {instance_spec.name}")
                
                # Check if instance name already exists in deployment
                if instance_spec.name in self._created_instance_names:
                    raise ComputeError(
                        f"Instance name '{instance_spec.name}' already used in this deployment"
                    )
                
                # Create instance
                instance = self.create_instance(instance_spec)
                created_instances.append(instance)
                
                # Track created instance name
                self._created_instance_names.add(instance_spec.name)
                
                self.logger.info(
                    f"Successfully created instance '{instance_spec.name}' (ID: {instance.id})"
                )
            
            # Wait for all instances to reach ACTIVE status
            self.logger.info(f"Waiting for {len(created_instances)} instances to become ACTIVE")
            self._wait_for_instances_active(created_instances)
            
            self.logger.info(
                f"Instance creation complete: {len(created_instances)} instances ACTIVE"
            )
            return created_instances
        
        except Exception as e:
            self.logger.error(f"Instance creation failed: {e}")
            raise
    
    def create_instance(self, instance_spec: InstanceSpec) -> Server:
        """
        Create a single compute instance with specified configuration.
        
        Validates flavor and image exist, attaches to networks, applies security
        groups, configures SSH key, and injects user_data and metadata.
        
        Args:
            instance_spec: Instance specification
            
        Returns:
            Created Server object
            
        Raises:
            ComputeError: If instance creation fails or validation errors occur
        """
        # Validate and get flavor ID
        flavor_id = self._get_flavor_id(instance_spec.flavor)
        if not flavor_id:
            raise ComputeError(
                f"Flavor '{instance_spec.flavor}' not found in OVH catalog"
            )
        
        # Validate and get image ID
        image_id = self._get_image_id(instance_spec.image)
        if not image_id:
            raise ComputeError(
                f"Image '{instance_spec.image}' not found in OVH catalog"
            )
        
        # Validate network IDs
        if not instance_spec.network_ids:
            raise ComputeError(
                f"Instance '{instance_spec.name}' requires at least one network"
            )
        
        self._validate_networks_exist(instance_spec.network_ids)
        
        # Validate security groups exist
        if instance_spec.security_groups:
            self._validate_security_groups_exist(instance_spec.security_groups)
        
        try:
            # Prepare network configuration
            networks = [{'uuid': network_id} for network_id in instance_spec.network_ids]
            
            # Prepare instance parameters
            instance_params = {
                'name': instance_spec.name,
                'flavor_id': flavor_id,
                'image_id': image_id,
                'key_name': instance_spec.key_name,
                'networks': networks
            }
            
            # Add security groups if specified
            if instance_spec.security_groups:
                instance_params['security_groups'] = [
                    {'name': sg_name} for sg_name in instance_spec.security_groups
                ]
            
            # Add user_data if specified
            if instance_spec.user_data:
                instance_params['user_data'] = instance_spec.user_data
            
            # Add metadata if specified
            if instance_spec.metadata:
                instance_params['metadata'] = instance_spec.metadata
            
            # Create instance
            instance = self.conn.compute.create_server(**instance_params)
            
            self.logger.info(
                f"Created instance '{instance_spec.name}' (ID: {instance.id}, "
                f"Status: {instance.status}, Flavor: {instance_spec.flavor}, "
                f"Image: {instance_spec.image})"
            )
            
            return instance
        
        except SDKException as e:
            error_msg = f"Failed to create instance '{instance_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise ComputeError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error creating instance '{instance_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise ComputeError(error_msg) from e
    
    def _get_flavor_id(self, flavor_name: str) -> Optional[str]:
        """
        Get flavor ID by name, with caching.
        
        Args:
            flavor_name: Name of the flavor (e.g., "s1-2", "s1-4")
            
        Returns:
            Flavor ID if found, None otherwise
        """
        # Check cache first
        if flavor_name in self._flavor_cache:
            return self._flavor_cache[flavor_name]
        
        try:
            # Search for flavor by name
            flavor = self.conn.compute.find_flavor(flavor_name)
            if flavor:
                self._flavor_cache[flavor_name] = flavor.id
                self.logger.debug(f"Found flavor '{flavor_name}' (ID: {flavor.id})")
                return flavor.id
            
            self.logger.warning(f"Flavor '{flavor_name}' not found")
            return None
        
        except Exception as e:
            self.logger.error(f"Error finding flavor '{flavor_name}': {e}")
            return None
    
    def _get_image_id(self, image_name: str) -> Optional[str]:
        """
        Get image ID by name, with caching.
        
        Args:
            image_name: Name of the image (e.g., "Ubuntu 22.04", "Debian 11")
            
        Returns:
            Image ID if found, None otherwise
        """
        # Check cache first
        if image_name in self._image_cache:
            return self._image_cache[image_name]
        
        try:
            # Search for image by name
            image = self.conn.compute.find_image(image_name)
            if image:
                self._image_cache[image_name] = image.id
                self.logger.debug(f"Found image '{image_name}' (ID: {image.id})")
                return image.id
            
            self.logger.warning(f"Image '{image_name}' not found")
            return None
        
        except Exception as e:
            self.logger.error(f"Error finding image '{image_name}': {e}")
            return None
    
    def _validate_networks_exist(self, network_ids: List[str]) -> None:
        """
        Validate that all specified networks exist.
        
        Args:
            network_ids: List of network IDs to validate
            
        Raises:
            ComputeError: If any network doesn't exist
        """
        for network_id in network_ids:
            try:
                network = self.conn.network.get_network(network_id)
                if not network:
                    raise ComputeError(f"Network '{network_id}' not found")
            except Exception as e:
                raise ComputeError(f"Failed to validate network '{network_id}': {e}")
    
    def _validate_security_groups_exist(self, security_group_names: List[str]) -> None:
        """
        Validate that all specified security groups exist.
        
        Args:
            security_group_names: List of security group names to validate
            
        Raises:
            ComputeError: If any security group doesn't exist
        """
        for sg_name in security_group_names:
            try:
                # Search for security group by name
                sgs = list(self.conn.network.security_groups(name=sg_name))
                if not sgs:
                    raise ComputeError(f"Security group '{sg_name}' not found")
            except Exception as e:
                raise ComputeError(f"Failed to validate security group '{sg_name}': {e}")
    
    def _validate_instance_names_unique(self, instance_specs: List[InstanceSpec]) -> None:
        """
        Validate that all instance names are unique.
        
        Args:
            instance_specs: List of instance specifications
            
        Raises:
            ComputeError: If duplicate instance names are found
        """
        names = [spec.name for spec in instance_specs]
        duplicates = [name for name in names if names.count(name) > 1]
        
        if duplicates:
            unique_duplicates = list(set(duplicates))
            raise ComputeError(
                f"Duplicate instance names found: {', '.join(unique_duplicates)}"
            )
    
    def _wait_for_instances_active(self, instances: List[Server]) -> None:
        """
        Wait for all instances to reach ACTIVE status.
        
        Polls instance status with timeout. Raises error if any instance
        fails to reach ACTIVE status within timeout period.
        
        Args:
            instances: List of Server objects to wait for
            
        Raises:
            ComputeError: If any instance doesn't reach ACTIVE status within timeout
        """
        start_time = time.time()
        pending_instances = {instance.id: instance for instance in instances}
        
        while pending_instances and (time.time() - start_time) < self.INSTANCE_ACTIVE_TIMEOUT:
            for instance_id in list(pending_instances.keys()):
                try:
                    # Refresh instance status
                    current_instance = self.conn.compute.get_server(instance_id)
                    
                    if current_instance.status == 'ACTIVE':
                        self.logger.info(
                            f"Instance {current_instance.name} (ID: {instance_id}) is ACTIVE"
                        )
                        del pending_instances[instance_id]
                    
                    elif current_instance.status == 'ERROR':
                        # Get fault information if available
                        fault_msg = ""
                        if hasattr(current_instance, 'fault') and current_instance.fault:
                            fault_msg = f": {current_instance.fault.get('message', 'Unknown error')}"
                        
                        raise ComputeError(
                            f"Instance {current_instance.name} (ID: {instance_id}) "
                            f"entered ERROR state{fault_msg}"
                        )
                    
                    elif current_instance.status not in ['BUILD', 'ACTIVE']:
                        self.logger.warning(
                            f"Instance {current_instance.name} (ID: {instance_id}) "
                            f"in unexpected status: {current_instance.status}"
                        )
                
                except Exception as e:
                    self.logger.error(f"Error checking instance {instance_id} status: {e}")
                    raise ComputeError(f"Failed to check instance status: {e}")
            
            # If there are still pending instances, wait before checking again
            if pending_instances:
                time.sleep(self.POLLING_INTERVAL)
        
        # Check if timeout was reached
        if pending_instances:
            pending_names = [
                f"{inst.name} (ID: {inst_id})" 
                for inst_id, inst in pending_instances.items()
            ]
            raise ComputeError(
                f"Timeout waiting for instances to become ACTIVE after "
                f"{self.INSTANCE_ACTIVE_TIMEOUT} seconds. "
                f"Pending instances: {', '.join(pending_names)}"
            )
    
    def get_instance_by_name(self, name: str) -> Optional[Server]:
        """
        Get instance by name.
        
        Args:
            name: Instance name
            
        Returns:
            Server object if found, None otherwise
        """
        try:
            servers = list(self.conn.compute.servers(name=name))
            if servers:
                return servers[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting instance by name '{name}': {e}")
            return None
    
    def list_instances(self) -> List[Server]:
        """
        List all instances.
        
        Returns:
            List of Server objects
        """
        try:
            return list(self.conn.compute.servers())
        except Exception as e:
            self.logger.error(f"Error listing instances: {e}")
            return []
    
    def delete_instance(self, instance_id: str) -> bool:
        """
        Delete an instance.
        
        Args:
            instance_id: ID of instance to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting instance: {instance_id}")
            self.conn.compute.delete_server(instance_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting instance {instance_id}: {e}")
            return False
    
    def wait_for_instance_active(self, instance_id: str, timeout: int = None) -> Server:
        """
        Wait for a single instance to reach ACTIVE status.
        
        Args:
            instance_id: ID of instance to wait for
            timeout: Optional timeout in seconds (defaults to INSTANCE_ACTIVE_TIMEOUT)
            
        Returns:
            Server object in ACTIVE status
            
        Raises:
            ComputeError: If instance doesn't reach ACTIVE status within timeout
        """
        timeout = timeout or self.INSTANCE_ACTIVE_TIMEOUT
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                instance = self.conn.compute.get_server(instance_id)
                
                if instance.status == 'ACTIVE':
                    self.logger.info(f"Instance {instance_id} is ACTIVE")
                    return instance
                
                elif instance.status == 'ERROR':
                    fault_msg = ""
                    if hasattr(instance, 'fault') and instance.fault:
                        fault_msg = f": {instance.fault.get('message', 'Unknown error')}"
                    
                    raise ComputeError(
                        f"Instance {instance_id} entered ERROR state{fault_msg}"
                    )
                
                time.sleep(self.POLLING_INTERVAL)
            
            except ComputeError:
                raise
            except Exception as e:
                raise ComputeError(f"Error waiting for instance {instance_id}: {e}")
        
        raise ComputeError(
            f"Timeout waiting for instance {instance_id} to become ACTIVE "
            f"after {timeout} seconds"
        )
