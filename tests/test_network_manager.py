"""Unit tests for network infrastructure management."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from openstack.network.v2.network import Network
from openstack.network.v2.subnet import Subnet
from openstack.exceptions import SDKException

from openstack_sdk.network_manager import NetworkManager, NetworkError
from config.models import NetworkSpec, SubnetSpec


@pytest.fixture
def mock_connection():
    """Create a mock OpenStack connection."""
    conn = Mock()
    conn.network = Mock()
    return conn


@pytest.fixture
def network_manager(mock_connection):
    """Create a NetworkManager instance with mock connection."""
    return NetworkManager(mock_connection)


@pytest.fixture
def sample_network_spec():
    """Create a sample network specification."""
    return NetworkSpec(
        name="test-network",
        admin_state_up=True,
        external=False,
        subnets=[
            SubnetSpec(
                name="test-subnet",
                cidr="192.168.1.0/24",
                ip_version=4,
                enable_dhcp=True,
                dns_nameservers=["8.8.8.8", "8.8.4.4"]
            )
        ]
    )


@pytest.fixture
def sample_subnet_spec():
    """Create a sample subnet specification."""
    return SubnetSpec(
        name="test-subnet",
        cidr="192.168.1.0/24",
        ip_version=4,
        enable_dhcp=True,
        gateway_ip="192.168.1.1",
        dns_nameservers=["8.8.8.8"]
    )


class TestNetworkCreation:
    """Tests for network creation functionality."""
    
    def test_create_network_success(self, network_manager, sample_network_spec):
        """Test successful network creation."""
        # Setup mock
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        mock_network.name = "test-network"
        mock_network.status = "ACTIVE"
        
        network_manager.conn.network.create_network.return_value = mock_network
        
        # Execute
        result = network_manager.create_network(sample_network_spec)
        
        # Verify
        assert result == mock_network
        network_manager.conn.network.create_network.assert_called_once_with(
            name="test-network",
            admin_state_up=True,
            is_router_external=False
        )
    
    def test_create_network_with_external_flag(self, network_manager):
        """Test network creation with external flag."""
        spec = NetworkSpec(name="external-net", external=True)
        mock_network = Mock(spec=Network)
        mock_network.id = "net-456"
        mock_network.status = "ACTIVE"
        
        network_manager.conn.network.create_network.return_value = mock_network
        
        result = network_manager.create_network(spec)
        
        assert result == mock_network
        network_manager.conn.network.create_network.assert_called_once_with(
            name="external-net",
            admin_state_up=True,
            is_router_external=True
        )
    
    def test_create_network_sdk_exception(self, network_manager, sample_network_spec):
        """Test network creation with SDK exception."""
        network_manager.conn.network.create_network.side_effect = SDKException("API error")
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager.create_network(sample_network_spec)
        
        assert "Failed to create network" in str(exc_info.value)
        assert "test-network" in str(exc_info.value)


class TestSubnetCreation:
    """Tests for subnet creation functionality."""
    
    def test_create_subnet_success(self, network_manager, sample_subnet_spec):
        """Test successful subnet creation."""
        mock_subnet = Mock(spec=Subnet)
        mock_subnet.id = "subnet-123"
        mock_subnet.name = "test-subnet"
        
        network_manager.conn.network.create_subnet.return_value = mock_subnet
        
        result = network_manager.create_subnet(sample_subnet_spec, "net-123")
        
        assert result == mock_subnet
        network_manager.conn.network.create_subnet.assert_called_once()
        call_kwargs = network_manager.conn.network.create_subnet.call_args[1]
        assert call_kwargs['name'] == "test-subnet"
        assert call_kwargs['network_id'] == "net-123"
        assert call_kwargs['cidr'] == "192.168.1.0/24"
        assert call_kwargs['ip_version'] == 4
        assert call_kwargs['enable_dhcp'] is True
        assert call_kwargs['gateway_ip'] == "192.168.1.1"
        assert call_kwargs['dns_nameservers'] == ["8.8.8.8"]
    
    def test_create_subnet_without_optional_params(self, network_manager):
        """Test subnet creation without optional parameters."""
        spec = SubnetSpec(
            name="minimal-subnet",
            cidr="10.0.0.0/24",
            ip_version=4
        )
        mock_subnet = Mock(spec=Subnet)
        mock_subnet.id = "subnet-456"
        
        network_manager.conn.network.create_subnet.return_value = mock_subnet
        
        result = network_manager.create_subnet(spec, "net-123")
        
        assert result == mock_subnet
        call_kwargs = network_manager.conn.network.create_subnet.call_args[1]
        assert 'gateway_ip' not in call_kwargs
        assert 'dns_nameservers' not in call_kwargs
    
    def test_create_subnet_invalid_cidr(self, network_manager):
        """Test subnet creation with invalid CIDR."""
        spec = SubnetSpec(
            name="bad-subnet",
            cidr="invalid-cidr",
            ip_version=4
        )
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager.create_subnet(spec, "net-123")
        
        assert "Invalid CIDR notation" in str(exc_info.value)
        assert "invalid-cidr" in str(exc_info.value)
    
    def test_create_subnet_invalid_ip_version(self, network_manager):
        """Test subnet creation with invalid IP version."""
        spec = SubnetSpec(
            name="bad-subnet",
            cidr="192.168.1.0/24",
            ip_version=5  # Invalid
        )
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager.create_subnet(spec, "net-123")
        
        assert "Invalid IP version" in str(exc_info.value)
    
    def test_create_subnet_gateway_outside_cidr(self, network_manager):
        """Test subnet creation with gateway IP outside CIDR range."""
        spec = SubnetSpec(
            name="bad-subnet",
            cidr="192.168.1.0/24",
            ip_version=4,
            gateway_ip="10.0.0.1"  # Outside CIDR range
        )
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager.create_subnet(spec, "net-123")
        
        assert "Gateway IP" in str(exc_info.value)
        assert "not within CIDR range" in str(exc_info.value)
    
    def test_create_subnet_ipv6(self, network_manager):
        """Test IPv6 subnet creation."""
        spec = SubnetSpec(
            name="ipv6-subnet",
            cidr="2001:db8::/64",
            ip_version=6,
            enable_dhcp=False
        )
        mock_subnet = Mock(spec=Subnet)
        mock_subnet.id = "subnet-ipv6"
        
        network_manager.conn.network.create_subnet.return_value = mock_subnet
        
        result = network_manager.create_subnet(spec, "net-123")
        
        assert result == mock_subnet
        call_kwargs = network_manager.conn.network.create_subnet.call_args[1]
        assert call_kwargs['ip_version'] == 6
        assert call_kwargs['cidr'] == "2001:db8::/64"


class TestCIDRValidation:
    """Tests for CIDR validation functionality."""
    
    def test_validate_cidr_valid_ipv4(self, network_manager):
        """Test validation of valid IPv4 CIDR."""
        assert network_manager._validate_cidr("192.168.1.0/24") is True
        assert network_manager._validate_cidr("10.0.0.0/8") is True
        assert network_manager._validate_cidr("172.16.0.0/12") is True
    
    def test_validate_cidr_valid_ipv6(self, network_manager):
        """Test validation of valid IPv6 CIDR."""
        assert network_manager._validate_cidr("2001:db8::/32") is True
        assert network_manager._validate_cidr("fe80::/10") is True
    
    def test_validate_cidr_invalid(self, network_manager):
        """Test validation of invalid CIDR."""
        assert network_manager._validate_cidr("invalid") is False
        assert network_manager._validate_cidr("192.168.1.0") is False
        assert network_manager._validate_cidr("192.168.1.0/33") is False
        assert network_manager._validate_cidr("") is False
    
    def test_validate_gateway_in_cidr_valid(self, network_manager):
        """Test gateway validation within CIDR range."""
        assert network_manager._validate_gateway_in_cidr(
            "192.168.1.1", "192.168.1.0/24"
        ) is True
        assert network_manager._validate_gateway_in_cidr(
            "192.168.1.254", "192.168.1.0/24"
        ) is True
    
    def test_validate_gateway_in_cidr_invalid(self, network_manager):
        """Test gateway validation outside CIDR range."""
        assert network_manager._validate_gateway_in_cidr(
            "10.0.0.1", "192.168.1.0/24"
        ) is False
        assert network_manager._validate_gateway_in_cidr(
            "192.168.2.1", "192.168.1.0/24"
        ) is False


class TestCIDROverlapChecking:
    """Tests for CIDR overlap checking."""
    
    def test_no_overlap_different_ranges(self, network_manager):
        """Test subnets with non-overlapping CIDR ranges."""
        subnets = [
            SubnetSpec(name="subnet1", cidr="192.168.1.0/24", ip_version=4),
            SubnetSpec(name="subnet2", cidr="192.168.2.0/24", ip_version=4),
            SubnetSpec(name="subnet3", cidr="10.0.0.0/24", ip_version=4)
        ]
        
        # Should not raise exception
        network_manager._validate_no_cidr_overlap(subnets)
    
    def test_overlap_detected(self, network_manager):
        """Test detection of overlapping CIDR ranges."""
        subnets = [
            SubnetSpec(name="subnet1", cidr="192.168.1.0/24", ip_version=4),
            SubnetSpec(name="subnet2", cidr="192.168.1.0/25", ip_version=4)  # Overlaps
        ]
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager._validate_no_cidr_overlap(subnets)
        
        assert "CIDR ranges overlap" in str(exc_info.value)
        assert "subnet1" in str(exc_info.value)
        assert "subnet2" in str(exc_info.value)
    
    def test_single_subnet_no_overlap(self, network_manager):
        """Test single subnet has no overlap."""
        subnets = [
            SubnetSpec(name="subnet1", cidr="192.168.1.0/24", ip_version=4)
        ]
        
        # Should not raise exception
        network_manager._validate_no_cidr_overlap(subnets)
    
    def test_empty_subnets_no_overlap(self, network_manager):
        """Test empty subnet list has no overlap."""
        # Should not raise exception
        network_manager._validate_no_cidr_overlap([])


class TestNetworkNameUniqueness:
    """Tests for network name uniqueness enforcement."""
    
    def test_unique_network_names(self, network_manager):
        """Test validation passes with unique network names."""
        specs = [
            NetworkSpec(name="network1"),
            NetworkSpec(name="network2"),
            NetworkSpec(name="network3")
        ]
        
        # Should not raise exception
        network_manager._validate_network_names_unique(specs)
    
    def test_duplicate_network_names(self, network_manager):
        """Test detection of duplicate network names."""
        specs = [
            NetworkSpec(name="network1"),
            NetworkSpec(name="network2"),
            NetworkSpec(name="network1")  # Duplicate
        ]
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager._validate_network_names_unique(specs)
        
        assert "Duplicate network names" in str(exc_info.value)
        assert "network1" in str(exc_info.value)
    
    def test_multiple_duplicates(self, network_manager):
        """Test detection of multiple duplicate network names."""
        specs = [
            NetworkSpec(name="net1"),
            NetworkSpec(name="net2"),
            NetworkSpec(name="net1"),
            NetworkSpec(name="net2")
        ]
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager._validate_network_names_unique(specs)
        
        assert "Duplicate network names" in str(exc_info.value)


class TestNetworkStatusVerification:
    """Tests for network status verification."""
    
    def test_verify_network_active_immediate(self, network_manager):
        """Test network that is immediately ACTIVE."""
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        mock_network.status = "ACTIVE"
        
        network_manager.conn.network.get_network.return_value = mock_network
        
        # Should not raise exception
        network_manager._verify_network_active(mock_network)
    
    def test_verify_network_active_after_delay(self, network_manager):
        """Test network that becomes ACTIVE after delay."""
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        
        # First call returns BUILD, second returns ACTIVE
        network_manager.conn.network.get_network.side_effect = [
            Mock(status="BUILD"),
            Mock(status="ACTIVE")
        ]
        
        # Should not raise exception
        network_manager._verify_network_active(mock_network)
    
    def test_verify_network_error_state(self, network_manager):
        """Test network that enters ERROR state."""
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        
        network_manager.conn.network.get_network.return_value = Mock(status="ERROR")
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager._verify_network_active(mock_network)
        
        assert "ERROR state" in str(exc_info.value)
    
    @patch('time.sleep')
    @patch('time.time')
    def test_verify_network_timeout(self, mock_time, mock_sleep, network_manager):
        """Test network activation timeout."""
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        
        # Simulate timeout
        mock_time.side_effect = [0, 31]  # Start time, then past timeout
        network_manager.conn.network.get_network.return_value = Mock(status="BUILD")
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager._verify_network_active(mock_network)
        
        assert "did not reach ACTIVE state" in str(exc_info.value)


class TestNetworkInfrastructureCreation:
    """Tests for complete network infrastructure creation."""
    
    def test_create_infrastructure_success(self, network_manager, sample_network_spec):
        """Test successful infrastructure creation."""
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        mock_network.name = "test-network"
        mock_network.status = "ACTIVE"
        
        mock_subnet = Mock(spec=Subnet)
        mock_subnet.id = "subnet-123"
        
        network_manager.conn.network.create_network.return_value = mock_network
        network_manager.conn.network.create_subnet.return_value = mock_subnet
        network_manager.conn.network.get_network.return_value = mock_network
        
        result = network_manager.create_network_infrastructure([sample_network_spec])
        
        assert len(result) == 1
        assert result[0] == mock_network
        network_manager.conn.network.create_network.assert_called_once()
        network_manager.conn.network.create_subnet.assert_called_once()
    
    def test_create_infrastructure_multiple_networks(self, network_manager):
        """Test creation of multiple networks."""
        specs = [
            NetworkSpec(
                name=f"network-{i}",
                subnets=[SubnetSpec(name=f"subnet-{i}", cidr=f"192.168.{i}.0/24", ip_version=4)]
            )
            for i in range(3)
        ]
        
        mock_networks = [
            Mock(spec=Network, id=f"net-{i}", name=f"network-{i}", status="ACTIVE")
            for i in range(3)
        ]
        
        network_manager.conn.network.create_network.side_effect = mock_networks
        network_manager.conn.network.create_subnet.return_value = Mock(spec=Subnet)
        network_manager.conn.network.get_network.side_effect = mock_networks
        
        result = network_manager.create_network_infrastructure(specs)
        
        assert len(result) == 3
        assert network_manager.conn.network.create_network.call_count == 3
        assert network_manager.conn.network.create_subnet.call_count == 3
    
    def test_create_infrastructure_empty_list(self, network_manager):
        """Test infrastructure creation with empty list."""
        result = network_manager.create_network_infrastructure([])
        
        assert result == []
        network_manager.conn.network.create_network.assert_not_called()
    
    def test_create_infrastructure_duplicate_names_in_deployment(self, network_manager):
        """Test detection of duplicate names within deployment."""
        spec1 = NetworkSpec(
            name="duplicate-net",
            subnets=[SubnetSpec(name="subnet1", cidr="192.168.1.0/24", ip_version=4)]
        )
        spec2 = NetworkSpec(
            name="duplicate-net",
            subnets=[SubnetSpec(name="subnet2", cidr="192.168.2.0/24", ip_version=4)]
        )
        
        with pytest.raises(NetworkError) as exc_info:
            network_manager.create_network_infrastructure([spec1, spec2])
        
        assert "Duplicate network names" in str(exc_info.value)


class TestNetworkUtilityMethods:
    """Tests for utility methods."""
    
    def test_get_network_by_name_found(self, network_manager):
        """Test getting network by name when it exists."""
        mock_network = Mock(spec=Network)
        mock_network.name = "test-network"
        
        network_manager.conn.network.networks.return_value = [mock_network]
        
        result = network_manager.get_network_by_name("test-network")
        
        assert result == mock_network
    
    def test_get_network_by_name_not_found(self, network_manager):
        """Test getting network by name when it doesn't exist."""
        network_manager.conn.network.networks.return_value = []
        
        result = network_manager.get_network_by_name("nonexistent")
        
        assert result is None
    
    def test_list_networks(self, network_manager):
        """Test listing all networks."""
        mock_networks = [Mock(spec=Network) for _ in range(3)]
        network_manager.conn.network.networks.return_value = mock_networks
        
        result = network_manager.list_networks()
        
        assert len(result) == 3
        assert result == mock_networks
    
    def test_delete_network_success(self, network_manager):
        """Test successful network deletion."""
        result = network_manager.delete_network("net-123")
        
        assert result is True
        network_manager.conn.network.delete_network.assert_called_once_with("net-123")
    
    def test_delete_network_failure(self, network_manager):
        """Test network deletion failure."""
        network_manager.conn.network.delete_network.side_effect = Exception("Delete failed")
        
        result = network_manager.delete_network("net-123")
        
        assert result is False
    
    def test_delete_subnet_success(self, network_manager):
        """Test successful subnet deletion."""
        result = network_manager.delete_subnet("subnet-123")
        
        assert result is True
        network_manager.conn.network.delete_subnet.assert_called_once_with("subnet-123")
    
    def test_delete_subnet_failure(self, network_manager):
        """Test subnet deletion failure."""
        network_manager.conn.network.delete_subnet.side_effect = Exception("Delete failed")
        
        result = network_manager.delete_subnet("subnet-123")
        
        assert result is False
