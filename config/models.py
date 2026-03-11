"""Data models for OVH OpenStack deployment configuration."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SecurityGroupRule:
    """Security group rule specification."""
    direction: str  # "ingress" or "egress"
    protocol: str  # "tcp", "udp", "icmp", or "any"
    remote_ip_prefix: str  # CIDR notation
    ethertype: str = "IPv4"  # "IPv4" or "IPv6"
    port_range_min: Optional[int] = None
    port_range_max: Optional[int] = None


@dataclass
class SecurityGroupSpec:
    """Security group specification."""
    name: str
    description: str
    rules: List[SecurityGroupRule] = field(default_factory=list)


@dataclass
class SubnetSpec:
    """Subnet specification."""
    name: str
    cidr: str  # e.g., "192.168.1.0/24"
    ip_version: int = 4  # 4 or 6
    enable_dhcp: bool = True
    gateway_ip: Optional[str] = None
    dns_nameservers: List[str] = field(default_factory=list)


@dataclass
class NetworkSpec:
    """Network specification."""
    name: str
    admin_state_up: bool = True
    external: bool = False
    subnets: List[SubnetSpec] = field(default_factory=list)


@dataclass
class VolumeSpec:
    """Volume specification."""
    name: str
    size: int  # Size in GB
    volume_type: str = "classic"  # e.g., "classic", "high-speed"
    bootable: bool = False
    image_id: Optional[str] = None
    attach_to: Optional[str] = None  # Instance name to attach to


@dataclass
class InstanceSpec:
    """Instance specification."""
    name: str
    flavor: str  # e.g., "s1-2", "s1-4", "s1-8"
    image: str  # e.g., "Ubuntu 22.04", "Debian 11"
    key_name: str  # SSH key name
    network_ids: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    user_data: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeploymentConfig:
    """Complete deployment configuration."""
    auth_url: str
    username: str
    password: str
    tenant_name: str
    region: str
    project_name: str
    instances: List[InstanceSpec] = field(default_factory=list)
    networks: List[NetworkSpec] = field(default_factory=list)
    volumes: List[VolumeSpec] = field(default_factory=list)
    security_groups: List[SecurityGroupSpec] = field(default_factory=list)


@dataclass
class AuthCredentials:
    """Authentication credentials for OVH OpenStack."""
    auth_url: str
    username: str
    password: str
    tenant_name: str
    region: str
    project_name: str


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
