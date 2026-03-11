"""Configuration manager for loading and validating deployment configurations."""

import os
import json
import yaml
import re
from typing import Dict, Any, List
from pathlib import Path

from .models import (
    DeploymentConfig,
    InstanceSpec,
    NetworkSpec,
    SubnetSpec,
    VolumeSpec,
    SecurityGroupSpec,
    SecurityGroupRule,
    ValidationResult,
    AuthCredentials,
)


class ConfigurationManager:
    """Manages loading, parsing, and validating deployment configurations."""

    def __init__(self):
        """Initialize the configuration manager."""
        pass

    def load_config(self, file_path: str) -> DeploymentConfig:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            DeploymentConfig object
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Read file content
        with open(path, 'r') as f:
            content = f.read()
        
        # Parse based on file extension
        if path.suffix in ['.yaml', '.yml']:
            config_dict = yaml.safe_load(content)
        elif path.suffix == '.json':
            config_dict = json.loads(content)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Use .yaml, .yml, or .json")
        
        # Substitute environment variables
        config_dict = self._substitute_env_vars(config_dict)
        
        # Parse into data models
        return self._parse_config(config_dict)

    def _substitute_env_vars(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute environment variables in configuration values.
        
        Supports ${VAR_NAME} syntax.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Configuration dictionary with environment variables substituted
        """
        def substitute_value(value):
            if isinstance(value, str):
                # Replace ${VAR_NAME} with environment variable value
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for var_name in matches:
                    env_value = os.environ.get(var_name, '')
                    value = value.replace(f'${{{var_name}}}', env_value)
                return value
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return substitute_value(config_dict)

    def _parse_config(self, config_dict: Dict[str, Any]) -> DeploymentConfig:
        """
        Parse configuration dictionary into DeploymentConfig object.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            DeploymentConfig object
        """
        # Parse instances
        instances = []
        for inst_dict in config_dict.get('instances', []):
            instances.append(InstanceSpec(
                name=inst_dict['name'],
                flavor=inst_dict['flavor'],
                image=inst_dict['image'],
                key_name=inst_dict['key_name'],
                network_ids=inst_dict.get('network_ids', []),
                security_groups=inst_dict.get('security_groups', []),
                user_data=inst_dict.get('user_data'),
                metadata=inst_dict.get('metadata', {})
            ))
        
        # Parse networks
        networks = []
        for net_dict in config_dict.get('networks', []):
            subnets = []
            for subnet_dict in net_dict.get('subnets', []):
                subnets.append(SubnetSpec(
                    name=subnet_dict['name'],
                    cidr=subnet_dict['cidr'],
                    ip_version=subnet_dict.get('ip_version', 4),
                    enable_dhcp=subnet_dict.get('enable_dhcp', True),
                    gateway_ip=subnet_dict.get('gateway_ip'),
                    dns_nameservers=subnet_dict.get('dns_nameservers', [])
                ))
            
            networks.append(NetworkSpec(
                name=net_dict['name'],
                admin_state_up=net_dict.get('admin_state_up', True),
                external=net_dict.get('external', False),
                subnets=subnets
            ))
        
        # Parse volumes
        volumes = []
        for vol_dict in config_dict.get('volumes', []):
            volumes.append(VolumeSpec(
                name=vol_dict['name'],
                size=vol_dict['size'],
                volume_type=vol_dict.get('volume_type', 'classic'),
                bootable=vol_dict.get('bootable', False),
                image_id=vol_dict.get('image_id'),
                attach_to=vol_dict.get('attach_to')
            ))
        
        # Parse security groups
        security_groups = []
        for sg_dict in config_dict.get('security_groups', []):
            rules = []
            for rule_dict in sg_dict.get('rules', []):
                rules.append(SecurityGroupRule(
                    direction=rule_dict['direction'],
                    protocol=rule_dict['protocol'],
                    remote_ip_prefix=rule_dict['remote_ip_prefix'],
                    ethertype=rule_dict.get('ethertype', 'IPv4'),
                    port_range_min=rule_dict.get('port_range_min'),
                    port_range_max=rule_dict.get('port_range_max')
                ))
            
            security_groups.append(SecurityGroupSpec(
                name=sg_dict['name'],
                description=sg_dict['description'],
                rules=rules
            ))
        
        # Handle authentication credentials - check if we're using application credentials
        username = config_dict.get('username', '')
        password = config_dict.get('password', '')
        tenant_name = config_dict.get('tenant_name', '')
        
        # If application credentials are provided, use them instead
        if 'application_credential_id' in config_dict and 'application_credential_secret' in config_dict:
            username = ''
            password = ''
            tenant_name = config_dict.get('tenant_name', config_dict.get('project_name', ''))
        
        # Create DeploymentConfig
        return DeploymentConfig(
            auth_url=config_dict['auth_url'],
            username=username,
            password=password,
            tenant_name=tenant_name,
            region=config_dict.get('region', ''),
            project_name=config_dict.get('project_name', ''),
            instances=instances,
            networks=networks,
            volumes=volumes,
            security_groups=security_groups
        )

    def validate_config(self, config: DeploymentConfig) -> ValidationResult:
        """
        Validate deployment configuration.
        
        Args:
            config: DeploymentConfig object to validate
            
        Returns:
            ValidationResult with is_valid flag and error messages
        """
        errors = []
        
        # Validate authentication parameters
        if not config.auth_url:
            errors.append("auth_url is required")
        elif not self._is_valid_url(config.auth_url):
            errors.append(f"auth_url is not a valid HTTPS URL: {config.auth_url}")
        
        # Validate required fields - we always require region and auth_url
        if not config.region:
            errors.append("region is required")
            
        # For tenant_name, we allow it to be empty since it might be set via application credentials
        # The important thing is that auth_url is provided and region is provided
        # We don't enforce tenant_name requirement here since it could be empty for app credentials
        
        # Validate at least one instance
        if not config.instances:
            errors.append("At least one instance specification is required")
        
        # Validate instance specifications
        instance_names = set()
        for instance in config.instances:
            # Check for duplicate names
            if instance.name in instance_names:
                errors.append(f"Duplicate instance name: {instance.name}")
            instance_names.add(instance.name)
            
            # Validate required fields
            if not instance.flavor:
                errors.append(f"Instance flavor is required for: {instance.name}")
            
            if not instance.image:
                errors.append(f"Instance image is required for: {instance.name}")
            
            if not instance.key_name:
                errors.append(f"Instance key_name is required for: {instance.name}")
            
            if not instance.network_ids:
                errors.append(f"At least one network is required for instance: {instance.name}")
        
        # Validate network specifications
        network_names = set()
        for network in config.networks:
            # Check for duplicate names
            if network.name in network_names:
                errors.append(f"Duplicate network name: {network.name}")
            network_names.add(network.name)
            
            # Private networks need at least one subnet
            if not network.external and not network.subnets:
                errors.append(f"Private network requires at least one subnet: {network.name}")
            
            # Validate subnets
            subnet_names = set()
            for subnet in network.subnets:
                if subnet.name in subnet_names:
                    errors.append(f"Duplicate subnet name in network {network.name}: {subnet.name}")
                subnet_names.add(subnet.name)
                
                if not self._is_valid_cidr(subnet.cidr):
                    errors.append(f"Invalid CIDR notation: {subnet.cidr}")
                
                if subnet.ip_version not in [4, 6]:
                    errors.append(f"IP version must be 4 or 6, got: {subnet.ip_version}")
                
                if subnet.gateway_ip and not self._is_valid_ip(subnet.gateway_ip):
                    errors.append(f"Invalid gateway IP: {subnet.gateway_ip}")
        
        # Validate volume specifications
        volume_names = set()
        for volume in config.volumes:
            if volume.name in volume_names:
                errors.append(f"Duplicate volume name: {volume.name}")
            volume_names.add(volume.name)
            
            if volume.size <= 0:
                errors.append(f"Volume size must be positive for: {volume.name}")
            
            if volume.bootable and not volume.image_id:
                errors.append(f"Bootable volume requires image_id: {volume.name}")
            
            if volume.attach_to and volume.attach_to not in instance_names:
                errors.append(f"Volume attach_to references non-existent instance: {volume.attach_to}")
        
        # Validate security group specifications
        sg_names = set()
        for sg in config.security_groups:
            if sg.name in sg_names:
                errors.append(f"Duplicate security group name: {sg.name}")
            sg_names.add(sg.name)
            
            # Validate rules
            for rule in sg.rules:
                if rule.direction not in ['ingress', 'egress']:
                    errors.append(f"Security group rule direction must be 'ingress' or 'egress', got: {rule.direction}")
                
                if rule.protocol not in ['tcp', 'udp', 'icmp', 'any']:
                    errors.append(f"Security group rule protocol must be 'tcp', 'udp', 'icmp', or 'any', got: {rule.protocol}")
                
                if rule.port_range_min is not None and rule.port_range_max is not None:
                    if rule.port_range_min > rule.port_range_max:
                        errors.append(f"port_range_min must be <= port_range_max in security group {sg.name}")
                
                if not self._is_valid_cidr(rule.remote_ip_prefix):
                    errors.append(f"Invalid CIDR notation in security group rule: {rule.remote_ip_prefix}")
                
                if rule.ethertype not in ['IPv4', 'IPv6']:
                    errors.append(f"Security group rule ethertype must be 'IPv4' or 'IPv6', got: {rule.ethertype}")
        
        # Validate network references in instances
        for instance in config.instances:
            for network_id in instance.network_ids:
                # Note: We can't validate actual network IDs here, only network names
                # This validation will be done at deployment time
                pass
        
        # Validate security group references in instances
        for instance in config.instances:
            for sg_name in instance.security_groups:
                if sg_name not in sg_names:
                    errors.append(f"Instance {instance.name} references non-existent security group: {sg_name}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def get_auth_credentials(self, config: DeploymentConfig) -> AuthCredentials:
        """
        Extract authentication credentials from configuration.
        
        Args:
            config: DeploymentConfig object
            
        Returns:
            AuthCredentials object
        """
        return AuthCredentials(
            auth_url=config.auth_url,
            username=config.username,
            password=config.password,
            tenant_name=config.tenant_name,
            region=config.region,
            project_name=config.project_name
        )

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTPS URL."""
        return url.startswith('https://') and len(url) > 8

    def _is_valid_cidr(self, cidr: str) -> bool:
        """Check if CIDR notation is valid."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if not re.match(pattern, cidr):
            return False
        
        # Validate IP address and prefix
        try:
            ip_part, prefix_part = cidr.split('/')
            octets = [int(x) for x in ip_part.split('.')]
            prefix = int(prefix_part)
            
            # Check octets are in valid range
            if not all(0 <= octet <= 255 for octet in octets):
                return False
            
            # Check prefix is in valid range
            if not 0 <= prefix <= 32:
                return False
            
            return True
        except (ValueError, AttributeError):
            return False

    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        try:
            octets = [int(x) for x in ip.split('.')]
            return all(0 <= octet <= 255 for octet in octets)
        except (ValueError, AttributeError):
            return False
