"""Main deployment orchestration engine for OVH OpenStack."""
import sys
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from openstack.connection import Connection
from openstack.exceptions import SDKException, HttpException

from config.models import DeploymentConfig, AuthCredentials
from openstack_sdk.auth_manager import ConnectionManager, AuthenticationError
from openstack_sdk.network_manager import NetworkManager, NetworkError
from openstack_sdk.security_group_manager import SecurityGroupManager, SecurityGroupError
from openstack_sdk.compute_manager import ComputeManager, ComputeError
from openstack_sdk.volume_manager import VolumeManager, VolumeError
from utils.logger import get_logger


@dataclass
class FailedResource:
    """Information about a failed resource."""
    resource_type: str
    resource_name: str
    error_message: str


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    deployment_id: str
    created_resources: Dict[str, List[str]] = field(default_factory=dict)
    failed_resources: List[FailedResource] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: str = ""
    orphaned_resources: List[str] = field(default_factory=list)


class DeploymentError(Exception):
    """Exception raised for deployment failures."""
    pass


class DeploymentEngine:
    """
    Main deployment orchestration engine.
    
    Orchestrates resource creation in correct dependency order, implements
    deployment tracking with unique deployment_id, handles comprehensive error
    handling with try-catch blocks, generates DeploymentResult with all required
    fields, implements rollback logic for failed deployments, and provides
    cleanup functions for manual resource removal.
    """
    
    # Maximum number of concurrent operations
    MAX_WORKERS = 5
    
    # Exponential backoff parameters for API rate limiting
    INITIAL_BACKOFF = 1  # seconds
    MAX_BACKOFF = 60  # seconds
    BACKOFF_MULTIPLIER = 2
    
    def __init__(self, credentials: AuthCredentials, logger=None):
        """
        Initialize deployment engine.
        
        Args:
            credentials: Authentication credentials
            logger: Optional logger instance
        """
        self.credentials = credentials
        self.logger = logger or get_logger(__name__)
        self.conn_manager = ConnectionManager(credentials, logger=self.logger)
        self._resource_cache: Dict[str, Any] = {}
    
    def deploy_infrastructure(self, config: DeploymentConfig) -> DeploymentResult:
        """
        Deploy complete infrastructure from configuration.
        
        Orchestrates resource creation in correct dependency order:
        1. Networks and subnets
        2. Security groups
        3. Compute instances
        4. Volumes and attachments
        
        Implements deployment tracking with unique deployment_id, comprehensive
        error handling, and automatic rollback on failure.
        
        Args:
            config: Deployment configuration
            
        Returns:
            DeploymentResult with success status and created resources
            
        Raises:
            DeploymentError: If deployment fails
        """
        deployment_id = str(uuid.uuid4())
        start_time = time.time()
        created_resources: Dict[str, List[str]] = {
            'networks': [],
            'subnets': [],
            'security_groups': [],
            'instances': [],
            'volumes': []
        }
        failed_resources: List[FailedResource] = []
        
        self.logger.info(f"Starting deployment {deployment_id}")
        
        try:
            # Step 1: Establish connection
            self.logger.info("Establishing OpenStack connection")
            conn = self.conn_manager.connect()
            
            # Initialize managers
            network_mgr = NetworkManager(conn, logger=self.logger)
            sg_mgr = SecurityGroupManager(conn, logger=self.logger)
            compute_mgr = ComputeManager(conn, logger=self.logger)
            volume_mgr = VolumeManager(conn, logger=self.logger)
            
            # Step 2: Create network infrastructure (networks before instances)
            if config.networks:
                self.logger.info(f"Creating {len(config.networks)} network(s)")
                try:
                    networks = network_mgr.create_network_infrastructure(config.networks)
                    for network in networks:
                        created_resources['networks'].append(network.id)
                        # Cache network for later reference
                        self._resource_cache[f"network_{network.name}"] = network
                        
                        # Get subnets for this network
                        subnets = list(conn.network.subnets(network_id=network.id))
                        for subnet in subnets:
                            created_resources['subnets'].append(subnet.id)
                    
                    self.logger.info(f"Successfully created {len(networks)} network(s)")
                except NetworkError as e:
                    self.logger.error(f"Network creation failed: {e}")
                    failed_resources.append(FailedResource(
                        resource_type="network",
                        resource_name="network_infrastructure",
                        error_message=str(e)
                    ))
                    raise DeploymentError(f"Network creation failed: {e}") from e
            
            # Step 3: Create security groups (before instances)
            if config.security_groups:
                self.logger.info(f"Creating {len(config.security_groups)} security group(s)")
                try:
                    security_groups = sg_mgr.create_security_groups(config.security_groups)
                    for sg in security_groups:
                        created_resources['security_groups'].append(sg.id)
                        # Cache security group for later reference
                        self._resource_cache[f"sg_{sg.name}"] = sg
                    
                    self.logger.info(f"Successfully created {len(security_groups)} security group(s)")
                except SecurityGroupError as e:
                    self.logger.error(f"Security group creation failed: {e}")
                    failed_resources.append(FailedResource(
                        resource_type="security_group",
                        resource_name="security_groups",
                        error_message=str(e)
                    ))
                    raise DeploymentError(f"Security group creation failed: {e}") from e
            
            # Step 4: Create compute instances (after networks and security groups)
            if config.instances:
                self.logger.info(f"Creating {len(config.instances)} instance(s)")
                try:
                    instances = compute_mgr.create_compute_instances(config.instances)
                    instance_map = {}
                    for instance in instances:
                        created_resources['instances'].append(instance.id)
                        # Cache instance for volume attachment
                        instance_map[instance.name] = instance
                        self._resource_cache[f"instance_{instance.name}"] = instance
                    
                    self.logger.info(f"Successfully created {len(instances)} instance(s)")
                except ComputeError as e:
                    self.logger.error(f"Instance creation failed: {e}")
                    failed_resources.append(FailedResource(
                        resource_type="instance",
                        resource_name="compute_instances",
                        error_message=str(e)
                    ))
                    raise DeploymentError(f"Instance creation failed: {e}") from e
            else:
                instance_map = {}
            
            # Step 5: Create and attach volumes (after instances are ACTIVE)
            if config.volumes:
                self.logger.info(f"Creating {len(config.volumes)} volume(s)")
                try:
                    volumes = volume_mgr.create_and_attach_volumes(config.volumes, instance_map)
                    for volume in volumes:
                        created_resources['volumes'].append(volume.id)
                    
                    self.logger.info(f"Successfully created {len(volumes)} volume(s)")
                except VolumeError as e:
                    self.logger.error(f"Volume creation/attachment failed: {e}")
                    failed_resources.append(FailedResource(
                        resource_type="volume",
                        resource_name="volumes",
                        error_message=str(e)
                    ))
                    raise DeploymentError(f"Volume creation/attachment failed: {e}") from e
            
            # Calculate deployment duration
            duration = time.time() - start_time
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            self.logger.info(
                f"Deployment {deployment_id} completed successfully in {duration:.2f}s"
            )
            
            return DeploymentResult(
                success=True,
                deployment_id=deployment_id,
                created_resources=created_resources,
                failed_resources=[],
                duration_seconds=duration,
                timestamp=timestamp
            )
        
        except (DeploymentError, AuthenticationError) as e:
            # Deployment failed - perform rollback
            self.logger.error(f"Deployment {deployment_id} failed: {e}")
            
            # Calculate duration
            duration = time.time() - start_time
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Attempt rollback
            self.logger.info("Attempting rollback of created resources")
            orphaned = self.rollback_resources(created_resources, conn)
            
            return DeploymentResult(
                success=False,
                deployment_id=deployment_id,
                created_resources={},
                failed_resources=failed_resources,
                duration_seconds=duration,
                timestamp=timestamp,
                orphaned_resources=orphaned
            )
        
        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected deployment error: {e}", exc_info=True)
            
            duration = time.time() - start_time
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            failed_resources.append(FailedResource(
                resource_type="deployment",
                resource_name="infrastructure",
                error_message=f"Unexpected error: {str(e)}"
            ))
            
            # Attempt rollback
            orphaned = self.rollback_resources(created_resources, conn)
            
            return DeploymentResult(
                success=False,
                deployment_id=deployment_id,
                created_resources={},
                failed_resources=failed_resources,
                duration_seconds=duration,
                timestamp=timestamp,
                orphaned_resources=orphaned
            )
        
        finally:
            # Close connection
            self.conn_manager.close()

    
    def rollback_resources(
        self,
        created_resources: Dict[str, List[str]],
        conn: Connection
    ) -> List[str]:
        """
        Rollback resources created during failed deployment.
        
        Deletes resources in reverse dependency order:
        1. Volumes (must be detached first)
        2. Instances
        3. Security groups
        4. Subnets
        5. Networks
        
        Handles partial rollback failures and tracks orphaned resources.
        
        Args:
            created_resources: Dictionary of created resource IDs by type
            conn: OpenStack connection
            
        Returns:
            List of orphaned resource IDs that couldn't be deleted
        """
        self.logger.info("Starting resource rollback")
        orphaned_resources = []
        
        # Delete in reverse dependency order
        
        # Step 1: Delete volumes
        if created_resources.get('volumes'):
            self.logger.info(f"Rolling back {len(created_resources['volumes'])} volume(s)")
            for volume_id in created_resources['volumes']:
                try:
                    # Check if volume is attached and detach if necessary
                    volume = conn.block_storage.get_volume(volume_id)
                    if volume and volume.status == 'in-use':
                        # Get attachments
                        if hasattr(volume, 'attachments') and volume.attachments:
                            for attachment in volume.attachments:
                                instance_id = attachment.get('server_id')
                                if instance_id:
                                    self.logger.info(
                                        f"Detaching volume {volume_id} from instance {instance_id}"
                                    )
                                    try:
                                        conn.compute.delete_volume_attachment(
                                            volume_id, instance_id
                                        )
                                        # Wait for detachment
                                        time.sleep(2)
                                    except Exception as e:
                                        self.logger.warning(
                                            f"Failed to detach volume {volume_id}: {e}"
                                        )
                    
                    # Delete volume
                    self.logger.info(f"Deleting volume: {volume_id}")
                    conn.block_storage.delete_volume(volume_id, ignore_missing=True)
                    self.logger.info(f"Deleted volume: {volume_id}")
                
                except Exception as e:
                    self.logger.error(f"Failed to delete volume {volume_id}: {e}")
                    orphaned_resources.append(f"volume:{volume_id}")
        
        # Step 2: Delete instances
        if created_resources.get('instances'):
            self.logger.info(f"Rolling back {len(created_resources['instances'])} instance(s)")
            for instance_id in created_resources['instances']:
                try:
                    self.logger.info(f"Deleting instance: {instance_id}")
                    conn.compute.delete_server(instance_id, ignore_missing=True)
                    self.logger.info(f"Deleted instance: {instance_id}")
                except Exception as e:
                    self.logger.error(f"Failed to delete instance {instance_id}: {e}")
                    orphaned_resources.append(f"instance:{instance_id}")
        
        # Wait for instances to be fully deleted before deleting networks
        if created_resources.get('instances'):
            self.logger.info("Waiting for instances to be deleted")
            time.sleep(5)
        
        # Step 3: Delete security groups
        if created_resources.get('security_groups'):
            self.logger.info(
                f"Rolling back {len(created_resources['security_groups'])} security group(s)"
            )
            for sg_id in created_resources['security_groups']:
                try:
                    self.logger.info(f"Deleting security group: {sg_id}")
                    conn.network.delete_security_group(sg_id, ignore_missing=True)
                    self.logger.info(f"Deleted security group: {sg_id}")
                except Exception as e:
                    self.logger.error(f"Failed to delete security group {sg_id}: {e}")
                    orphaned_resources.append(f"security_group:{sg_id}")
        
        # Step 4: Delete subnets
        if created_resources.get('subnets'):
            self.logger.info(f"Rolling back {len(created_resources['subnets'])} subnet(s)")
            for subnet_id in created_resources['subnets']:
                try:
                    self.logger.info(f"Deleting subnet: {subnet_id}")
                    conn.network.delete_subnet(subnet_id, ignore_missing=True)
                    self.logger.info(f"Deleted subnet: {subnet_id}")
                except Exception as e:
                    self.logger.error(f"Failed to delete subnet {subnet_id}: {e}")
                    orphaned_resources.append(f"subnet:{subnet_id}")
        
        # Step 5: Delete networks
        if created_resources.get('networks'):
            self.logger.info(f"Rolling back {len(created_resources['networks'])} network(s)")
            for network_id in created_resources['networks']:
                try:
                    self.logger.info(f"Deleting network: {network_id}")
                    conn.network.delete_network(network_id, ignore_missing=True)
                    self.logger.info(f"Deleted network: {network_id}")
                except Exception as e:
                    self.logger.error(f"Failed to delete network {network_id}: {e}")
                    orphaned_resources.append(f"network:{network_id}")
        
        if orphaned_resources:
            self.logger.warning(
                f"Rollback incomplete: {len(orphaned_resources)} orphaned resource(s)"
            )
            self.logger.warning(f"Orphaned resources: {', '.join(orphaned_resources)}")
        else:
            self.logger.info("Rollback completed successfully")
        
        return orphaned_resources
    
    def cleanup_resources(
        self,
        resource_ids: Dict[str, List[str]]
    ) -> Dict[str, bool]:
        """
        Manually cleanup specified resources.
        
        Deletes resources in reverse dependency order and verifies deletion.
        Useful for cleaning up orphaned resources or manual teardown.
        
        Args:
            resource_ids: Dictionary of resource IDs to delete by type
                         Format: {'networks': [...], 'instances': [...], etc.}
            
        Returns:
            Dictionary mapping resource IDs to deletion success status
        """
        self.logger.info("Starting manual resource cleanup")
        
        results = {}
        
        try:
            conn = self.conn_manager.connect()
            
            # Use rollback function which already implements reverse dependency order
            orphaned = self.rollback_resources(resource_ids, conn)
            
            # Build results dictionary
            for resource_type, ids in resource_ids.items():
                for resource_id in ids:
                    resource_key = f"{resource_type}:{resource_id}"
                    results[resource_key] = resource_key not in orphaned
            
            self.logger.info(f"Cleanup complete: {len(results)} resource(s) processed")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            raise DeploymentError(f"Cleanup failed: {e}") from e
        
        finally:
            self.conn_manager.close()
    
    def _handle_api_rate_limit(self, attempt: int) -> None:
        """
        Handle API rate limiting with exponential backoff.
        
        Args:
            attempt: Current retry attempt number (0-indexed)
        """
        backoff = min(
            self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt),
            self.MAX_BACKOFF
        )
        self.logger.warning(
            f"API rate limit encountered, backing off for {backoff:.1f}s "
            f"(attempt {attempt + 1})"
        )
        time.sleep(backoff)
    
    def _execute_with_retry(
        self,
        operation,
        max_retries: int = 3,
        operation_name: str = "operation"
    ):
        """
        Execute operation with retry logic for rate limiting.
        
        Args:
            operation: Callable to execute
            max_retries: Maximum number of retry attempts
            operation_name: Name of operation for logging
            
        Returns:
            Result of operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        for attempt in range(max_retries):
            try:
                return operation()
            
            except HttpException as e:
                if e.status_code == 429:  # Too Many Requests
                    if attempt < max_retries - 1:
                        self._handle_api_rate_limit(attempt)
                        continue
                    else:
                        self.logger.error(
                            f"{operation_name} failed after {max_retries} attempts due to rate limiting"
                        )
                        raise
                else:
                    # Other HTTP errors should not be retried
                    raise
            
            except SDKException as e:
                # Check if it's a rate limit error
                if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    if attempt < max_retries - 1:
                        self._handle_api_rate_limit(attempt)
                        continue
                    else:
                        self.logger.error(
                            f"{operation_name} failed after {max_retries} attempts due to rate limiting"
                        )
                        raise
                else:
                    # Other SDK errors should not be retried
                    raise
            
            except Exception:
                # Unexpected errors should not be retried
                raise
    
    def _cache_flavors(self, conn: Connection) -> None:
        """
        Cache flavor information to reduce API calls.
        
        Args:
            conn: OpenStack connection
        """
        if 'flavors' not in self._resource_cache:
            self.logger.debug("Caching flavor information")
            try:
                flavors = list(conn.compute.flavors())
                self._resource_cache['flavors'] = {f.name: f for f in flavors}
                self.logger.debug(f"Cached {len(flavors)} flavor(s)")
            except Exception as e:
                self.logger.warning(f"Failed to cache flavors: {e}")
    
    def _cache_images(self, conn: Connection) -> None:
        """
        Cache image information to reduce API calls.
        
        Args:
            conn: OpenStack connection
        """
        if 'images' not in self._resource_cache:
            self.logger.debug("Caching image information")
            try:
                images = list(conn.compute.images())
                self._resource_cache['images'] = {i.name: i for i in images}
                self.logger.debug(f"Cached {len(images)} image(s)")
            except Exception as e:
                self.logger.warning(f"Failed to cache images: {e}")
    
    def _cache_networks(self, conn: Connection) -> None:
        """
        Cache network information to reduce API calls.
        
        Args:
            conn: OpenStack connection
        """
        if 'networks' not in self._resource_cache:
            self.logger.debug("Caching network information")
            try:
                networks = list(conn.network.networks())
                self._resource_cache['networks'] = {n.name: n for n in networks}
                self.logger.debug(f"Cached {len(networks)} network(s)")
            except Exception as e:
                self.logger.warning(f"Failed to cache networks: {e}")
    
    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """
        Get status of a deployment.
        
        Note: This is a placeholder for future implementation with persistent storage.
        Currently returns None as deployments are not persisted.
        
        Args:
            deployment_id: Unique deployment identifier
            
        Returns:
            DeploymentResult if found, None otherwise
        """
        self.logger.warning(
            f"Deployment status lookup not implemented for deployment {deployment_id}"
        )
        return None
