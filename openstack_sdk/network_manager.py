"""Network infrastructure creation and management for OVH OpenStack."""
import sys
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import ipaddress
import time
from typing import List, Dict, Optional, Set
from openstack.connection import Connection
from openstack.network.v2.network import Network
from openstack.network.v2.subnet import Subnet
from openstack.exceptions import SDKException

from config.models import NetworkSpec, SubnetSpec
from utils.logger import get_logger


class NetworkError(Exception):
    """Exception raised for network operation failures."""
    pass


class NetworkManager:
    """
    Manages network infrastructure creation and validation.
    
    Handles network and subnet creation, CIDR validation, overlap checking,
    network status verification, and name uniqueness enforcement.
    """
    
    # Maximum time to wait for network to become ACTIVE (seconds)
    NETWORK_ACTIVE_TIMEOUT = 30
    
    def __init__(self, connection: Connection, logger=None):
        """
        Initialize network manager.
        
        Args:
            connection: Authenticated OpenStack connection
            logger: Optional logger instance
        """
        self.conn = connection
        self.logger = logger or get_logger(__name__)
        self._created_network_names: Set[str] = set()
    
    def create_network_infrastructure(
        self, 
        network_specs: List[NetworkSpec]
    ) -> List[Network]:
        """
        Create complete network infrastructure from specifications.
        
        Creates networks and their associated subnets, validates CIDR notation,
        checks for overlaps, verifies network status, and enforces name uniqueness.
        
        Args:
            network_specs: List of network specifications
            
        Returns:
            List of created Network objects
            
        Raises:
            NetworkError: If network creation fails or validation errors occur
        """
        if not network_specs:
            self.logger.warning("No network specifications provided")
            return []
        
        self.logger.info(f"Creating network infrastructure: {len(network_specs)} networks")
        
        # Validate network name uniqueness across specs
        self._validate_network_names_unique(network_specs)
        
        # Validate CIDR ranges don't overlap within each network
        for network_spec in network_specs:
            self._validate_no_cidr_overlap(network_spec.subnets)
        
        created_networks = []
        
        try:
            for network_spec in network_specs:
                self.logger.info(f"Creating network: {network_spec.name}")
                
                # Check if network name already exists in deployment
                if network_spec.name in self._created_network_names:
                    raise NetworkError(
                        f"Network name '{network_spec.name}' already used in this deployment"
                    )
                
                # Create network
                network = self.create_network(network_spec)
                created_networks.append(network)
                
                # Track created network name
                self._created_network_names.add(network_spec.name)
                
                # Create subnets for this network
                for subnet_spec in network_spec.subnets:
                    self.logger.info(
                        f"Creating subnet '{subnet_spec.name}' for network '{network_spec.name}'"
                    )
                    subnet = self.create_subnet(subnet_spec, network.id)
                    self.logger.info(f"Created subnet: {subnet.id}")
                
                # Verify network is ACTIVE
                self._verify_network_active(network)
                
                self.logger.info(
                    f"Successfully created network '{network_spec.name}' with "
                    f"{len(network_spec.subnets)} subnet(s)"
                )
            
            self.logger.info(
                f"Network infrastructure creation complete: {len(created_networks)} networks"
            )
            return created_networks
        
        except Exception as e:
            self.logger.error(f"Network infrastructure creation failed: {e}")
            raise
    
    def create_network(self, network_spec: NetworkSpec) -> Network:
        """
        Create a network with specified configuration.
        
        Args:
            network_spec: Network specification
            
        Returns:
            Created Network object
            
        Raises:
            NetworkError: If network creation fails
        """
        try:
            # Create network
            network = self.conn.network.create_network(
                name=network_spec.name,
                admin_state_up=network_spec.admin_state_up,
                is_router_external=network_spec.external
            )
            
            self.logger.info(
                f"Created network '{network_spec.name}' (ID: {network.id}, "
                f"Status: {network.status})"
            )
            
            return network
        
        except SDKException as e:
            error_msg = f"Failed to create network '{network_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error creating network '{network_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg) from e
    
    def create_subnet(self, subnet_spec: SubnetSpec, network_id: str) -> Subnet:
        """
        Create a subnet associated with a network.
        
        Validates CIDR notation before creation and configures DNS nameservers
        and DHCP settings.
        
        Args:
            subnet_spec: Subnet specification
            network_id: ID of the parent network
            
        Returns:
            Created Subnet object
            
        Raises:
            NetworkError: If subnet creation fails or CIDR is invalid
        """
        # Validate CIDR notation
        if not self._validate_cidr(subnet_spec.cidr):
            raise NetworkError(
                f"Invalid CIDR notation for subnet '{subnet_spec.name}': {subnet_spec.cidr}"
            )
        
        # Validate IP version
        if subnet_spec.ip_version not in [4, 6]:
            raise NetworkError(
                f"Invalid IP version for subnet '{subnet_spec.name}': {subnet_spec.ip_version}. "
                "Must be 4 or 6"
            )
        
        # Validate gateway IP is within CIDR range if specified
        if subnet_spec.gateway_ip:
            if not self._validate_gateway_in_cidr(subnet_spec.gateway_ip, subnet_spec.cidr):
                raise NetworkError(
                    f"Gateway IP {subnet_spec.gateway_ip} is not within CIDR range "
                    f"{subnet_spec.cidr} for subnet '{subnet_spec.name}'"
                )
        
        try:
            # Prepare subnet parameters
            subnet_params = {
                'name': subnet_spec.name,
                'network_id': network_id,
                'cidr': subnet_spec.cidr,
                'ip_version': subnet_spec.ip_version,
                'enable_dhcp': subnet_spec.enable_dhcp
            }
            
            # Add optional parameters
            if subnet_spec.gateway_ip:
                subnet_params['gateway_ip'] = subnet_spec.gateway_ip
            
            if subnet_spec.dns_nameservers:
                subnet_params['dns_nameservers'] = subnet_spec.dns_nameservers
            
            # Create subnet
            subnet = self.conn.network.create_subnet(**subnet_params)
            
            self.logger.info(
                f"Created subnet '{subnet_spec.name}' (ID: {subnet.id}, "
                f"CIDR: {subnet_spec.cidr})"
            )
            
            return subnet
        
        except SDKException as e:
            error_msg = f"Failed to create subnet '{subnet_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error creating subnet '{subnet_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg) from e
    
    def _validate_cidr(self, cidr: str) -> bool:
        """
        Validate CIDR notation.
        
        Args:
            cidr: CIDR string to validate (e.g., "192.168.1.0/24")
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Ensure CIDR has a prefix (e.g., /24)
            if '/' not in str(cidr):
                return False
            ipaddress.ip_network(cidr, strict=False)
            return True
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Invalid CIDR '{cidr}': {e}")
            return False
    
    def _validate_gateway_in_cidr(self, gateway_ip: str, cidr: str) -> bool:
        """
        Validate that gateway IP is within CIDR range.
        
        Args:
            gateway_ip: Gateway IP address
            cidr: CIDR range
            
        Returns:
            True if gateway is within CIDR range, False otherwise
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            gateway = ipaddress.ip_address(gateway_ip)
            return gateway in network
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Error validating gateway {gateway_ip} in CIDR {cidr}: {e}")
            return False
    
    def _validate_no_cidr_overlap(self, subnet_specs: List[SubnetSpec]) -> None:
        """
        Validate that subnet CIDR ranges do not overlap within the same network.
        
        Args:
            subnet_specs: List of subnet specifications for a network
            
        Raises:
            NetworkError: If CIDR ranges overlap
        """
        if len(subnet_specs) <= 1:
            return
        
        # Parse all CIDR ranges
        networks = []
        for subnet_spec in subnet_specs:
            try:
                network = ipaddress.ip_network(subnet_spec.cidr, strict=False)
                networks.append((subnet_spec.name, network))
            except (ValueError, TypeError) as e:
                raise NetworkError(
                    f"Invalid CIDR for subnet '{subnet_spec.name}': {subnet_spec.cidr}"
                )
        
        # Check for overlaps
        for i, (name1, net1) in enumerate(networks):
            for name2, net2 in networks[i+1:]:
                if net1.overlaps(net2):
                    raise NetworkError(
                        f"CIDR ranges overlap between subnets '{name1}' ({net1}) "
                        f"and '{name2}' ({net2})"
                    )
    
    def _validate_network_names_unique(self, network_specs: List[NetworkSpec]) -> None:
        """
        Validate that all network names are unique.
        
        Args:
            network_specs: List of network specifications
            
        Raises:
            NetworkError: If duplicate network names are found
        """
        names = [spec.name for spec in network_specs]
        duplicates = [name for name in names if names.count(name) > 1]
        
        if duplicates:
            unique_duplicates = list(set(duplicates))
            raise NetworkError(
                f"Duplicate network names found: {', '.join(unique_duplicates)}"
            )
    
    def _verify_network_active(self, network: Network) -> None:
        """
        Verify that network reaches ACTIVE state.
        
        Args:
            network: Network object to verify
            
        Raises:
            NetworkError: If network doesn't reach ACTIVE state within timeout
        """
        start_time = time.time()
        current_network = None
        
        while time.time() - start_time < self.NETWORK_ACTIVE_TIMEOUT:
            # Refresh network status
            current_network = self.conn.network.get_network(network.id)
            
            if current_network.status == 'ACTIVE':
                self.logger.debug(f"Network {network.id} is ACTIVE")
                return
            
            if current_network.status == 'ERROR':
                raise NetworkError(
                    f"Network {network.id} entered ERROR state"
                )
            
            # Wait before checking again
            time.sleep(1)
        
        # Timeout reached
        current_status = current_network.status if current_network else "UNKNOWN"
        raise NetworkError(
            f"Network {network.id} did not reach ACTIVE state within "
            f"{self.NETWORK_ACTIVE_TIMEOUT} seconds (current status: {current_status})"
        )
    
    def get_network_by_name(self, name: str) -> Optional[Network]:
        """
        Get network by name.
        
        Args:
            name: Network name
            
        Returns:
            Network object if found, None otherwise
        """
        try:
            networks = list(self.conn.network.networks(name=name))
            if networks:
                return networks[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting network by name '{name}': {e}")
            return None
    
    def list_networks(self) -> List[Network]:
        """
        List all networks.
        
        Returns:
            List of Network objects
        """
        try:
            return list(self.conn.network.networks())
        except Exception as e:
            self.logger.error(f"Error listing networks: {e}")
            return []
    
    def delete_network(self, network_id: str) -> bool:
        """
        Delete a network.
        
        Args:
            network_id: ID of network to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting network: {network_id}")
            self.conn.network.delete_network(network_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting network {network_id}: {e}")
            return False
    
    def delete_subnet(self, subnet_id: str) -> bool:
        """
        Delete a subnet.
        
        Args:
            subnet_id: ID of subnet to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting subnet: {subnet_id}")
            self.conn.network.delete_subnet(subnet_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting subnet {subnet_id}: {e}")
            return False
