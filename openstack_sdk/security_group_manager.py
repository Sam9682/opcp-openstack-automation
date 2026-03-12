"""Security group creation and management for OVH OpenStack."""
import sys
import pathlib

# Add the parent directory to Python path to allow importing openstack_sdk
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import ipaddress
from typing import List, Set, Optional
from openstack.connection import Connection
from openstack.network.v2.security_group import SecurityGroup
from openstack.network.v2.security_group_rule import SecurityGroupRule as OSSecurityGroupRule
from openstack.exceptions import SDKException

from config.models import SecurityGroupSpec, SecurityGroupRule
from utils.logger import get_logger


class SecurityGroupError(Exception):
    """Exception raised for security group operation failures."""
    pass


class SecurityGroupManager:
    """
    Manages security group creation and validation.
    
    Handles security group and rule creation, validates rule parameters
    (direction, protocol, ports, CIDR), and enforces name uniqueness.
    """
    
    # Valid values for rule parameters
    VALID_DIRECTIONS = {'ingress', 'egress'}
    VALID_PROTOCOLS = {'tcp', 'udp', 'icmp', 'any'}
    VALID_ETHERTYPES = {'IPv4', 'IPv6'}
    
    def __init__(self, connection: Connection, logger=None):
        """
        Initialize security group manager.
        
        Args:
            connection: Authenticated OpenStack connection
            logger: Optional logger instance
        """
        self.conn = connection
        self.logger = logger or get_logger(__name__)
        self._created_sg_names: Set[str] = set()
    
    def create_security_groups(
        self,
        sg_specs: List[SecurityGroupSpec]
    ) -> List[SecurityGroup]:
        """
        Create security groups from specifications.
        
        Creates security groups with their rules, validates all rule parameters,
        and enforces name uniqueness.
        
        Args:
            sg_specs: List of security group specifications
            
        Returns:
            List of created SecurityGroup objects
            
        Raises:
            SecurityGroupError: If creation fails or validation errors occur
        """
        if not sg_specs:
            self.logger.warning("No security group specifications provided")
            return []
        
        self.logger.info(f"Creating security groups: {len(sg_specs)} groups")
        
        # Validate security group name uniqueness
        self._validate_sg_names_unique(sg_specs)
        
        created_groups = []
        
        try:
            for sg_spec in sg_specs:
                self.logger.info(f"Creating security group: {sg_spec.name}")
                
                # Check if security group name already exists in deployment
                if sg_spec.name in self._created_sg_names:
                    raise SecurityGroupError(
                        f"Security group name '{sg_spec.name}' already used in this deployment"
                    )
                
                # Create security group
                sg = self._create_security_group(sg_spec)
                created_groups.append(sg)
                
                # Track created security group name
                self._created_sg_names.add(sg_spec.name)
                
                # Create rules for this security group
                for rule in sg_spec.rules:
                    self.logger.debug(
                        f"Creating rule for security group '{sg_spec.name}': "
                        f"{rule.direction} {rule.protocol}"
                    )
                    self.create_security_group_rule(sg.id, rule)
                
                self.logger.info(
                    f"Successfully created security group '{sg_spec.name}' with "
                    f"{len(sg_spec.rules)} rule(s)"
                )
            
            self.logger.info(
                f"Security group creation complete: {len(created_groups)} groups"
            )
            return created_groups
        
        except Exception as e:
            self.logger.error(f"Security group creation failed: {e}")
            raise
    
    def _create_security_group(self, sg_spec: SecurityGroupSpec) -> SecurityGroup:
        """
        Create a security group.
        
        Args:
            sg_spec: Security group specification
            
        Returns:
            Created SecurityGroup object
            
        Raises:
            SecurityGroupError: If creation fails
        """
        try:
            sg = self.conn.network.create_security_group(
                name=sg_spec.name,
                description=sg_spec.description
            )
            
            self.logger.info(
                f"Created security group '{sg_spec.name}' (ID: {sg.id})"
            )
            
            return sg
        
        except SDKException as e:
            error_msg = f"Failed to create security group '{sg_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise SecurityGroupError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error creating security group '{sg_spec.name}': {str(e)}"
            self.logger.error(error_msg)
            raise SecurityGroupError(error_msg) from e
    
    def create_security_group_rule(
        self,
        security_group_id: str,
        rule: SecurityGroupRule
    ) -> OSSecurityGroupRule:
        """
        Create a security group rule with validation.
        
        Validates rule direction, protocol, port ranges, CIDR notation,
        and ethertype before creation.
        
        Args:
            security_group_id: ID of the security group
            rule: Security group rule specification
            
        Returns:
            Created SecurityGroupRule object
            
        Raises:
            SecurityGroupError: If validation fails or creation fails
        """
        # Validate rule parameters
        self._validate_rule(rule)
        
        try:
            # Prepare rule parameters
            rule_params = {
                'security_group_id': security_group_id,
                'direction': rule.direction,
                'ethertype': rule.ethertype,
                'remote_ip_prefix': rule.remote_ip_prefix
            }
            
            # Add protocol - OpenStack uses 'null' for 'any'
            if rule.protocol == 'any':
                rule_params['protocol'] = None
            else:
                rule_params['protocol'] = rule.protocol
            
            # Add port ranges if specified
            if rule.port_range_min is not None:
                rule_params['port_range_min'] = rule.port_range_min
            
            if rule.port_range_max is not None:
                rule_params['port_range_max'] = rule.port_range_max
            
            # Create rule
            created_rule = self.conn.network.create_security_group_rule(**rule_params)
            
            self.logger.debug(
                f"Created security group rule (ID: {created_rule.id}): "
                f"{rule.direction} {rule.protocol} "
                f"ports {rule.port_range_min}-{rule.port_range_max} "
                f"from {rule.remote_ip_prefix}"
            )
            
            return created_rule
        
        except SDKException as e:
            error_msg = (
                f"Failed to create security group rule "
                f"({rule.direction} {rule.protocol}): {str(e)}"
            )
            self.logger.error(error_msg)
            raise SecurityGroupError(error_msg) from e
        
        except Exception as e:
            error_msg = (
                f"Unexpected error creating security group rule "
                f"({rule.direction} {rule.protocol}): {str(e)}"
            )
            self.logger.error(error_msg)
            raise SecurityGroupError(error_msg) from e
    
    def _validate_rule(self, rule: SecurityGroupRule) -> None:
        """
        Validate security group rule parameters.
        
        Args:
            rule: Security group rule to validate
            
        Raises:
            SecurityGroupError: If validation fails
        """
        # Validate direction
        if rule.direction not in self.VALID_DIRECTIONS:
            raise SecurityGroupError(
                f"Invalid direction '{rule.direction}'. "
                f"Must be one of: {', '.join(self.VALID_DIRECTIONS)}"
            )
        
        # Validate protocol
        if rule.protocol not in self.VALID_PROTOCOLS:
            raise SecurityGroupError(
                f"Invalid protocol '{rule.protocol}'. "
                f"Must be one of: {', '.join(self.VALID_PROTOCOLS)}"
            )
        
        # Validate ethertype
        if rule.ethertype not in self.VALID_ETHERTYPES:
            raise SecurityGroupError(
                f"Invalid ethertype '{rule.ethertype}'. "
                f"Must be one of: {', '.join(self.VALID_ETHERTYPES)}"
            )
        
        # Validate port ranges
        if rule.port_range_min is not None and rule.port_range_max is not None:
            if rule.port_range_min > rule.port_range_max:
                raise SecurityGroupError(
                    f"Invalid port range: port_range_min ({rule.port_range_min}) "
                    f"must be less than or equal to port_range_max ({rule.port_range_max})"
                )
            
            # Validate port numbers are in valid range
            if not (0 <= rule.port_range_min <= 65535):
                raise SecurityGroupError(
                    f"Invalid port_range_min: {rule.port_range_min}. "
                    "Must be between 0 and 65535"
                )
            
            if not (0 <= rule.port_range_max <= 65535):
                raise SecurityGroupError(
                    f"Invalid port_range_max: {rule.port_range_max}. "
                    "Must be between 0 and 65535"
                )
        
        # Validate CIDR notation
        if not self._validate_cidr(rule.remote_ip_prefix):
            raise SecurityGroupError(
                f"Invalid CIDR notation: {rule.remote_ip_prefix}"
            )
    
    def _validate_cidr(self, cidr: str) -> bool:
        """
        Validate CIDR notation.
        
        Args:
            cidr: CIDR string to validate (e.g., "192.168.1.0/24" or "0.0.0.0/0")
            
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
    
    def _validate_sg_names_unique(self, sg_specs: List[SecurityGroupSpec]) -> None:
        """
        Validate that all security group names are unique.
        
        Args:
            sg_specs: List of security group specifications
            
        Raises:
            SecurityGroupError: If duplicate names are found
        """
        names = [spec.name for spec in sg_specs]
        duplicates = [name for name in names if names.count(name) > 1]
        
        if duplicates:
            unique_duplicates = list(set(duplicates))
            raise SecurityGroupError(
                f"Duplicate security group names found: {', '.join(unique_duplicates)}"
            )
    
    def get_security_group_by_name(self, name: str) -> Optional[SecurityGroup]:
        """
        Get security group by name.
        
        Args:
            name: Security group name
            
        Returns:
            SecurityGroup object if found, None otherwise
        """
        try:
            groups = list(self.conn.network.security_groups(name=name))
            if groups:
                return groups[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting security group by name '{name}': {e}")
            return None
    
    def list_security_groups(self) -> List[SecurityGroup]:
        """
        List all security groups.
        
        Returns:
            List of SecurityGroup objects
        """
        try:
            return list(self.conn.network.security_groups())
        except Exception as e:
            self.logger.error(f"Error listing security groups: {e}")
            return []
    
    def delete_security_group(self, security_group_id: str) -> bool:
        """
        Delete a security group.
        
        Args:
            security_group_id: ID of security group to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting security group: {security_group_id}")
            self.conn.network.delete_security_group(security_group_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting security group {security_group_id}: {e}")
            return False
